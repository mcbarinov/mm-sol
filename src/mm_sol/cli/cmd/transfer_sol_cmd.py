import sys
import time
from pathlib import Path
from typing import Annotated, Self

import mm_crypto_utils
from loguru import logger
from mm_crypto_utils import AddressToPrivate, TxRoute
from mm_std import BaseConfig, Err, utc_now
from pydantic import AfterValidator, BeforeValidator, Field, model_validator
from rich.live import Live
from rich.table import Table

from mm_sol import transfer
from mm_sol.balance import get_sol_balance_with_retries
from mm_sol.cli import calcs, cli_utils
from mm_sol.cli.calcs import calc_sol_expression
from mm_sol.cli.validators import Validators
from mm_sol.converters import lamports_to_sol


# noinspection DuplicatedCode
class Config(BaseConfig):
    nodes: Annotated[list[str], BeforeValidator(Validators.nodes())]
    routes: Annotated[list[TxRoute], BeforeValidator(Validators.sol_routes())]
    private_keys: Annotated[AddressToPrivate, BeforeValidator(Validators.sol_private_keys())]
    proxies: Annotated[list[str], Field(default_factory=list), BeforeValidator(Validators.proxies())]
    value: Annotated[str, AfterValidator(Validators.valid_sol_expression("balance"))]
    value_min_limit: Annotated[str | None, AfterValidator(Validators.valid_sol_expression())] = None
    delay: Annotated[str | None, AfterValidator(Validators.valid_calc_decimal_value())] = None  # in seconds
    round_ndigits: int = 5
    log_debug: Annotated[Path | None, BeforeValidator(Validators.log_file())] = None
    log_info: Annotated[Path | None, BeforeValidator(Validators.log_file())] = None

    @property
    def from_addresses(self) -> list[str]:
        return [r.from_address for r in self.routes]

    @model_validator(mode="after")
    def final_validator(self) -> Self:
        if not self.private_keys.contains_all_addresses(self.from_addresses):
            raise ValueError("private keys are not set for all addresses")

        return self


def run(
    config_path: Path,
    *,
    print_balances: bool,
    print_config: bool,
    debug: bool,
    no_confirmation: bool,
    emulate: bool,
) -> None:
    config = Config.read_toml_config_or_exit(config_path)

    if print_config:
        config.print_and_exit({"private_keys"})

    mm_crypto_utils.init_logger(debug, config.log_debug, config.log_info)

    if print_balances:
        _print_balances(config)
        sys.exit(0)

    _run_transfers(config, no_confirmation=no_confirmation, emulate=emulate)


def _run_transfers(config: Config, *, no_confirmation: bool, emulate: bool) -> None:
    logger.info(f"started at {utc_now()} UTC")
    logger.debug(f"config={config.model_dump(exclude={'private_keys'}) | {'version': cli_utils.get_version()}}")
    for i, route in enumerate(config.routes):
        _transfer(
            from_address=route.from_address,
            to_address=route.to_address,
            config=config,
            no_confirmation=no_confirmation,
            emulate=emulate,
        )
        if not emulate and config.delay is not None and i < len(config.routes) - 1:
            delay_value = mm_crypto_utils.calc_decimal_value(config.delay)
            logger.debug(f"delay {delay_value} seconds")
            time.sleep(float(delay_value))
    logger.info(f"finished at {utc_now()} UTC")


def _transfer(*, from_address: str, to_address: str, config: Config, no_confirmation: bool, emulate: bool) -> None:
    log_prefix = f"{from_address}->{to_address}"
    fee = 5000
    # get value
    value_res = calcs.calc_sol_value_for_address(
        nodes=config.nodes, value_expression=config.value, address=from_address, proxies=config.proxies, fee=fee
    )
    logger.debug(f"{log_prefix}value={value_res.ok_or_err()}")
    if isinstance(value_res, Err):
        logger.info(f"{log_prefix}calc value error, {value_res.err}")
        return
    value = value_res.ok

    # value_min_limit
    if config.value_min_limit:
        value_min_limit = calc_sol_expression(config.value_min_limit)
        if value < value_min_limit:
            logger.info(f"{log_prefix}: value<value_min_limit, value={lamports_to_sol(value, config.round_ndigits)}sol")
            return

    # emulate?
    if emulate:
        msg = f"{log_prefix}: emulate, value={lamports_to_sol(value, config.round_ndigits)}SOL,"
        msg += f" fee={fee}"
        logger.info(msg)
        return

    debug_tx_params = {"fee": fee, "value": value, "to": to_address}
    logger.debug(f"{log_prefix}: tx_params={debug_tx_params}")

    res = transfer.transfer_sol_with_retries(
        nodes=config.nodes,
        from_address=from_address,
        private_key=config.private_keys[from_address],
        to_address=to_address,
        lamports=value,
        proxies=config.proxies,
        retries=3,
    )

    if isinstance(res, Err):
        logger.info(f"{log_prefix}: send_error: {res.err}")
        return
    signature = res.ok

    if no_confirmation:
        msg = f"{log_prefix}: sig={signature}, value={lamports_to_sol(value, config.round_ndigits)}"
        logger.info(msg)
    else:
        logger.debug(f"{log_prefix}: sig={signature}, waiting for confirmation")
        status = "UNKNOWN"
        if cli_utils.wait_confirmation(config.nodes, config.proxies, signature, log_prefix):
            status = "OK"
        msg = f"{log_prefix}: sig={signature}, value={lamports_to_sol(value, config.round_ndigits)}, status={status}"
        logger.info(msg)


def _print_balances(config: Config) -> None:
    table = Table("n", "from_address", "sol", "to_address", "sol", title="balances")
    with Live(table, refresh_per_second=0.5):
        for count, route in enumerate(config.routes):
            from_balance = _get_sol_balance_str(route.from_address, config)
            to_balance = _get_sol_balance_str(route.to_address, config)
            row: list[str] = [str(count), route.from_address, from_balance, route.to_address, to_balance]
            table.add_row(*row)


def _get_sol_balance_str(address: str, config: Config) -> str:
    return get_sol_balance_with_retries(config.nodes, address, proxies=config.proxies, retries=5).map_or_else(
        lambda err: err,
        lambda ok: str(lamports_to_sol(ok, config.round_ndigits)),
    )
