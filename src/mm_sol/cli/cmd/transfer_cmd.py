import sys
import time
from pathlib import Path
from typing import Annotated, Self

import mm_crypto_utils
from loguru import logger
from mm_crypto_utils import AddressToPrivate, Transfer
from mm_std import BaseConfig, Err, fatal, utc_now
from pydantic import AfterValidator, BeforeValidator, Field, model_validator
from rich.console import Console
from rich.live import Live
from rich.table import Table
from solders.signature import Signature

from mm_sol.balance import get_sol_balance_with_retries, get_token_balance_with_retries
from mm_sol.cli import calcs, cli_utils
from mm_sol.cli.cli_utils import BaseConfigParams
from mm_sol.cli.validators import Validators
from mm_sol.converters import lamports_to_sol, to_token
from mm_sol.token import get_decimals_with_retries
from mm_sol.transfer import transfer_sol_with_retries, transfer_token_with_retries


class Config(BaseConfig):
    nodes: Annotated[list[str], BeforeValidator(Validators.nodes())]
    transfers: Annotated[list[Transfer], BeforeValidator(Validators.sol_transfers())]
    private_keys: Annotated[AddressToPrivate, BeforeValidator(Validators.sol_private_keys())]
    proxies: Annotated[list[str], Field(default_factory=list), BeforeValidator(Validators.proxies())]
    token: Annotated[str | None, AfterValidator(Validators.sol_address())] = None
    token_decimals: int = -1
    default_value: Annotated[str | None, AfterValidator(Validators.valid_sol_or_token_expression("balance"))] = None
    value_min_limit: Annotated[str | None, AfterValidator(Validators.valid_sol_or_token_expression())] = None
    delay: Annotated[str | None, AfterValidator(Validators.valid_calc_decimal_value())] = None  # in seconds
    round_ndigits: int = 5
    log_debug: Annotated[Path | None, BeforeValidator(Validators.log_file())] = None
    log_info: Annotated[Path | None, BeforeValidator(Validators.log_file())] = None

    @property
    def from_addresses(self) -> list[str]:
        return [r.from_address for r in self.transfers]

    @model_validator(mode="after")
    def final_validator(self) -> Self:
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

        if self.token:
            res = get_decimals_with_retries(self.nodes, self.token, retries=3, proxies=self.proxies)
            if isinstance(res, Err):
                fatal(f"can't get decimals for token={self.token}, error={res.err}")
            self.token_decimals = res.ok

        return self


class TransferCmdParams(BaseConfigParams):
    print_balances: bool
    print_transfers: bool
    debug: bool
    no_confirmation: bool
    emulate: bool
    print_config_verbose: bool


def run(cmd_params: TransferCmdParams) -> None:
    config = Config.read_toml_config_or_exit(cmd_params.config_path)

    if cmd_params.print_config_and_exit:
        cli_utils.print_config(config, exclude={"private_keys"}, count=None if cmd_params.debug else {"proxies"})
        sys.exit(0)

    if cmd_params.print_transfers:
        _print_transfers(config)
        sys.exit(0)

    if cmd_params.print_balances:
        _print_balances(config)
        sys.exit(0)

    _run_transfers(config, cmd_params)


def _run_transfers(config: Config, cmd_params: TransferCmdParams) -> None:
    mm_crypto_utils.init_logger(cmd_params.debug, config.log_debug, config.log_info)
    logger.info(f"transfer {cmd_params.config_path}: started at {utc_now()} UTC")
    logger.debug(f"config={config.model_dump(exclude={'private_keys'}) | {'version': cli_utils.get_version()}}")
    for i, route in enumerate(config.transfers):
        _transfer(route, config, cmd_params)
        if config.delay is not None and i < len(config.transfers) - 1:
            delay_value = mm_crypto_utils.calc_decimal_value(config.delay)
            logger.info(f"delay {delay_value} seconds")
            if not cmd_params.emulate:
                time.sleep(float(delay_value))
    logger.info(f"transfer {cmd_params.config_path}: finished at {utc_now()} UTC")


def _calc_value(transfer: Transfer, config: Config, transfer_sol_fee: int) -> int | None:
    if config.token:
        value_res = calcs.calc_token_value_for_address(
            nodes=config.nodes,
            value_expression=transfer.value,
            wallet_address=transfer.from_address,
            proxies=config.proxies,
            token_mint_address=config.token,
            token_decimals=config.token_decimals,
        )
    else:
        value_res = calcs.calc_sol_value_for_address(
            nodes=config.nodes,
            value_expression=transfer.value,
            address=transfer.from_address,
            proxies=config.proxies,
            fee=transfer_sol_fee,
        )
    logger.debug(f"{transfer.log_prefix}: value={value_res.ok_or_err()}")
    if isinstance(value_res, Err):
        logger.info(f"{transfer.log_prefix}: calc value error, {value_res.err}")

    return value_res.ok


def _check_value_min_limit(transfer: Transfer, value: int, config: Config) -> bool:
    """Returns False if the transfer should be skipped."""
    if config.value_min_limit:
        if config.token:
            value_min_limit = calcs.calc_token_expression(config.value_min_limit, config.token_decimals)
        else:
            value_min_limit = calcs.calc_sol_expression(config.value_min_limit)
        if value < value_min_limit:
            logger.info(f"{transfer.log_prefix}: value<value_min_limit, value={_value_with_suffix(value, config)}")
    return True


def _value_with_suffix(value: int, config: Config) -> str:
    if config.token:
        return f"{to_token(value, decimals=config.token_decimals, ndigits=config.round_ndigits)}t"
    return f"{lamports_to_sol(value, config.round_ndigits)}sol"


def _send_tx(transfer: Transfer, value: int, config: Config) -> Signature | None:
    logger.debug(f"{transfer.log_prefix}: value={_value_with_suffix(value, config)}")
    if config.token:
        res = transfer_token_with_retries(
            nodes=config.nodes,
            token_mint_address=config.token,
            from_address=transfer.from_address,
            private_key=config.private_keys[transfer.from_address],
            to_address=transfer.to_address,
            amount=value,
            decimals=config.token_decimals,
            proxies=config.proxies,
            retries=3,
        )
    else:
        res = transfer_sol_with_retries(
            nodes=config.nodes,
            from_address=transfer.from_address,
            private_key=config.private_keys[transfer.from_address],
            to_address=transfer.to_address,
            lamports=value,
            proxies=config.proxies,
            retries=3,
        )

    if isinstance(res, Err):
        logger.info(f"{transfer.log_prefix}: tx error {res.err}")
        return None
    return res.ok


def _transfer(transfer: Transfer, config: Config, cmd_params: TransferCmdParams) -> None:
    transfer_sol_fee = 5000

    value = _calc_value(transfer, config, transfer_sol_fee)
    if value is None:
        return

    if not _check_value_min_limit(transfer, value, config):
        return

    if cmd_params.emulate:
        logger.info(f"{transfer.log_prefix}: emulate, value={_value_with_suffix(value, config)}")
        return

    signature = _send_tx(transfer, value, config)
    if signature is None:
        return

    status = "UNKNOWN"
    if not cmd_params.no_confirmation:
        logger.debug(f"{transfer.log_prefix}: waiting for confirmation, sig={signature}")
        if cli_utils.wait_confirmation(config.nodes, config.proxies, signature, transfer.log_prefix):
            status = "OK"

    logger.info(f"{transfer.log_prefix}: sig={signature}, value={_value_with_suffix(value, config)}, status={status}")


def _print_transfers(config: Config) -> None:
    table = Table("n", "from_address", "to_address", "value", title="transfers")
    for count, transfer in enumerate(config.transfers, start=1):
        table.add_row(str(count), transfer.from_address, transfer.to_address, transfer.value)
    console = Console()
    console.print(table)


def _print_balances(config: Config) -> None:
    if config.token:
        headers = ["n", "from_address", "sol", "t", "to_address", "sol", "t"]
    else:
        headers = ["n", "from_address", "sol", "to_address", "sol"]
    table = Table(*headers, title="balances")
    with Live(table, refresh_per_second=0.5):
        for count, route in enumerate(config.transfers):
            from_sol_balance = _get_sol_balance_str(route.from_address, config)
            to_sol_balance = _get_sol_balance_str(route.to_address, config)
            from_t_balance = _get_token_balance_str(route.from_address, config) if config.token else ""
            to_t_balance = _get_token_balance_str(route.to_address, config) if config.token else ""

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


def _get_sol_balance_str(address: str, config: Config) -> str:
    return get_sol_balance_with_retries(config.nodes, address, proxies=config.proxies, retries=5).map_or_else(
        lambda err: err,
        lambda ok: str(lamports_to_sol(ok, config.round_ndigits)),
    )


def _get_token_balance_str(address: str, config: Config) -> str:
    if not config.token:
        raise ValueError("token is not set")
    return get_token_balance_with_retries(config.nodes, address, config.token, proxies=config.proxies, retries=5).map_or_else(
        lambda err: err,
        lambda ok: str(to_token(ok, config.token_decimals, ndigits=config.round_ndigits)),
    )
