"""SOL and SPL token transfer command with multi-route support."""

import asyncio
import importlib.metadata
import sys
from pathlib import Path
from typing import Annotated

from loguru import logger
from mm_clikit import TomlConfig, fatal
from mm_std import utc
from mm_web3.account import PrivateKeyMap
from mm_web3.calcs import calc_decimal_expression
from mm_web3.log import init_loguru
from mm_web3.validators import Transfer
from pydantic import AfterValidator, BeforeValidator, Field, model_validator
from rich.console import Console
from rich.live import Live
from rich.table import Table
from solders.signature import Signature

import mm_sol.retry
from mm_sol import retry
from mm_sol.cli import calcs, cli_utils
from mm_sol.cli.cli_utils import BaseConfigParams
from mm_sol.cli.validators import Validators
from mm_sol.converters import lamports_to_sol, to_token


class Config(TomlConfig):
    """Transfer command configuration with routes, keys, and value expressions."""

    nodes: Annotated[list[str], BeforeValidator(Validators.nodes())]
    transfers: Annotated[list[Transfer], BeforeValidator(Validators.sol_transfers())]
    private_keys: Annotated[PrivateKeyMap, BeforeValidator(Validators.sol_private_keys())]
    proxies: Annotated[list[str], Field(default_factory=list), BeforeValidator(Validators.proxies())]
    token: Annotated[str | None, AfterValidator(Validators.sol_address())] = None
    token_decimals: int = -1
    default_value: Annotated[str | None, AfterValidator(Validators.valid_sol_or_token_expression("balance"))] = None
    value_min_limit: Annotated[str | None, AfterValidator(Validators.valid_sol_or_token_expression())] = None
    delay: Annotated[str | None, AfterValidator(Validators.decimal_expression())] = None  # in seconds
    round_ndigits: int = 5
    log_debug: Annotated[Path | None, BeforeValidator(Validators.log_file())] = None
    log_info: Annotated[Path | None, BeforeValidator(Validators.log_file())] = None

    @property
    def from_addresses(self) -> list[str]:
        """Return the list of sender addresses from all transfer routes."""
        return [r.from_address for r in self.transfers]

    @model_validator(mode="after")
    def final_validator(self) -> Config:
        """Validate private keys, transfer values, and token/sol expressions."""
        if not self.private_keys.contains_all_addresses(self.from_addresses):
            raise ValueError("private keys are not set for all addresses")

        for transfer in self.transfers:  # If value is not set for a transfer, then set it to the global value of the config.
            if not transfer.value and self.default_value:
                transfer.value = self.default_value
        for transfer in self.transfers:  # Check all transfers have a value.
            if not transfer.value:
                raise ValueError(f"{transfer.log_prefix}: value is not set")

        if self.token:
            if self.default_value:
                Validators.valid_token_expression("balance")(self.default_value)
            if self.value_min_limit:
                Validators.valid_token_expression()(self.value_min_limit)
        else:
            if self.default_value:
                Validators.valid_sol_expression("balance")(self.default_value)
            if self.value_min_limit:
                Validators.valid_sol_expression()(self.value_min_limit)

        return self


class TransferCmdParams(BaseConfigParams):
    """CLI parameters for the transfer command."""

    print_balances: bool
    print_transfers: bool
    debug: bool
    no_confirmation: bool
    emulate: bool
    print_config_verbose: bool


async def run(cmd_params: TransferCmdParams) -> None:
    """Execute the transfer command: print config/balances/transfers or run transfers."""
    config = Config.load_or_exit(cmd_params.config_path)

    if cmd_params.print_config_and_exit:
        config.print_and_exit(exclude={"private_keys"})

    # Fetch token decimals (async, can't be done in sync validator)
    if config.token:
        res = await mm_sol.retry.get_token_decimals(3, config.nodes, config.proxies, token=config.token)
        if res.is_err():
            fatal(f"can't get decimals for token={config.token}, error={res.unwrap_err()}")
        config.token_decimals = res.unwrap()

    if cmd_params.print_transfers:
        _print_transfers(config)
        sys.exit(0)

    if cmd_params.print_balances:
        await _print_balances(config)
        sys.exit(0)

    await _run_transfers(config, cmd_params)


async def _run_transfers(config: Config, cmd_params: TransferCmdParams) -> None:
    """Execute all configured transfer routes sequentially with optional delays."""
    init_loguru(cmd_params.debug, config.log_debug, config.log_info)
    logger.info(f"transfer {cmd_params.config_path}: started at {utc()} UTC")
    version = importlib.metadata.version("mm-sol")
    logger.debug(f"config={config.model_dump(exclude={'private_keys'}) | {'version': version}}")
    for i, route in enumerate(config.transfers):
        await _transfer(route, config, cmd_params)
        if config.delay is not None and i < len(config.transfers) - 1:
            delay_value = calc_decimal_expression(config.delay)
            logger.info(f"delay {delay_value} seconds")
            if not cmd_params.emulate:
                await asyncio.sleep(float(delay_value))
    logger.info(f"transfer {cmd_params.config_path}: finished at {utc()} UTC")


async def _calc_value(transfer: Transfer, config: Config, transfer_sol_fee: int) -> int | None:
    """Calculate the transfer value in smallest units, resolving balance-based expressions."""
    if config.token:
        value_res = await calcs.calc_token_value_for_address(
            nodes=config.nodes,
            value_expression=transfer.value,
            owner=transfer.from_address,
            proxies=config.proxies,
            token=config.token,
            token_decimals=config.token_decimals,
        )
    else:
        value_res = await calcs.calc_sol_value_for_address(
            nodes=config.nodes,
            value_expression=transfer.value,
            address=transfer.from_address,
            proxies=config.proxies,
            fee=transfer_sol_fee,
        )
    logger.debug(f"{transfer.log_prefix}: value={value_res.value_or_error()}")
    if value_res.is_err():
        logger.info(f"{transfer.log_prefix}: calc value error, {value_res.unwrap_err()}")

    return value_res.value


def _check_value_min_limit(transfer: Transfer, value: int, config: Config) -> bool:
    """Return False if the transfer value is below the configured minimum limit."""
    if config.value_min_limit:
        if config.token:
            value_min_limit = calcs.calc_token_expression(config.value_min_limit, config.token_decimals)
        else:
            value_min_limit = calcs.calc_sol_expression(config.value_min_limit)
        if value < value_min_limit:
            logger.info(f"{transfer.log_prefix}: value<value_min_limit, value={_value_with_suffix(value, config)}")
    return True


def _value_with_suffix(value: int, config: Config) -> str:
    """Format a value with its unit suffix (sol or t)."""
    if config.token:
        return f"{to_token(value, decimals=config.token_decimals, ndigits=config.round_ndigits)}t"
    return f"{lamports_to_sol(value, config.round_ndigits)}sol"


async def _send_tx(transfer: Transfer, value: int, config: Config) -> Signature | None:
    """Submit a SOL or token transfer transaction with retries."""
    logger.debug(f"{transfer.log_prefix}: value={_value_with_suffix(value, config)}")
    if config.token:
        res = await retry.transfer_token(
            3,
            config.nodes,
            config.proxies,
            token_mint_address=config.token,
            from_address=transfer.from_address,
            private_key=config.private_keys[transfer.from_address],
            to_address=transfer.to_address,
            amount=value,
            decimals=config.token_decimals,
        )
    else:
        res = await retry.transfer_sol(
            3,
            config.nodes,
            config.proxies,
            from_address=transfer.from_address,
            private_key=config.private_keys[transfer.from_address],
            to_address=transfer.to_address,
            lamports=value,
        )

    if res.is_err():
        logger.info(f"{transfer.log_prefix}: tx error {res.unwrap_err()}")
        return None
    return res.value


async def _transfer(transfer: Transfer, config: Config, cmd_params: TransferCmdParams) -> None:
    """Execute a single transfer route: calculate value, check limits, send, and confirm."""
    transfer_sol_fee = 5000

    value = await _calc_value(transfer, config, transfer_sol_fee)
    if value is None:
        return

    if not _check_value_min_limit(transfer, value, config):
        return

    if cmd_params.emulate:
        logger.info(f"{transfer.log_prefix}: emulate, value={_value_with_suffix(value, config)}")
        return

    signature = await _send_tx(transfer, value, config)
    if signature is None:
        return

    status = "UNKNOWN"
    if not cmd_params.no_confirmation:
        logger.debug(f"{transfer.log_prefix}: waiting for confirmation, sig={signature}")
        if cli_utils.wait_confirmation(config.nodes, config.proxies, signature, transfer.log_prefix):
            status = "OK"

    logger.info(f"{transfer.log_prefix}: sig={signature}, value={_value_with_suffix(value, config)}, status={status}")


def _print_transfers(config: Config) -> None:
    """Print a table of all configured transfer routes."""
    table = Table("n", "from_address", "to_address", "value", title="transfers")
    for count, transfer in enumerate(config.transfers, start=1):
        table.add_row(str(count), transfer.from_address, transfer.to_address, transfer.value)
    console = Console()
    console.print(table)


async def _print_balances(config: Config) -> None:
    """Print a live-updating table of SOL and token balances for all transfer routes."""
    if config.token:
        headers = ["n", "from_address", "sol", "t", "to_address", "sol", "t"]
    else:
        headers = ["n", "from_address", "sol", "to_address", "sol"]
    table = Table(*headers, title="balances")
    with Live(table, refresh_per_second=0.5):
        for count, route in enumerate(config.transfers):
            from_sol_balance = await _get_sol_balance_str(route.from_address, config)
            to_sol_balance = await _get_sol_balance_str(route.to_address, config)
            from_t_balance = await _get_token_balance_str(route.from_address, config) if config.token else ""
            to_t_balance = await _get_token_balance_str(route.to_address, config) if config.token else ""

            if config.token:
                table.add_row(
                    str(count),
                    route.from_address,
                    from_sol_balance,
                    from_t_balance,
                    route.to_address,
                    to_sol_balance,
                    to_t_balance,
                )
            else:
                table.add_row(
                    str(count),
                    route.from_address,
                    from_sol_balance,
                    route.to_address,
                    to_sol_balance,
                )


async def _get_sol_balance_str(address: str, config: Config) -> str:
    """Fetch SOL balance and return it as a formatted string."""
    res = await retry.get_sol_balance(5, config.nodes, config.proxies, address=address)
    return res.map(lambda ok: str(lamports_to_sol(ok, config.round_ndigits))).value_or_error()


async def _get_token_balance_str(address: str, config: Config) -> str:
    """Fetch token balance and return it as a formatted string."""
    if not config.token:
        raise ValueError("token is not set")
    res = await mm_sol.retry.get_token_balance(5, config.nodes, config.proxies, owner=address, token=config.token)
    return res.map(lambda ok: str(to_token(ok, config.token_decimals, ndigits=config.round_ndigits))).value_or_error()
