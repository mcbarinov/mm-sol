import sys
import time
from pathlib import Path
from typing import Annotated, Self

import mm_crypto_utils
from loguru import logger
from mm_crypto_utils import AddressToPrivate, TxRoute
from mm_std import BaseConfig, Err, fatal, utc_now
from pydantic import AfterValidator, BeforeValidator, Field, model_validator
from rich.live import Live
from rich.table import Table

from mm_sol import transfer
from mm_sol.balance import get_sol_balance_with_retries, get_token_balance_with_retries
from mm_sol.cli import calcs, cli_utils
from mm_sol.cli.validators import Validators
from mm_sol.converters import lamports_to_sol, to_token
from mm_sol.token import get_decimals_with_retries


# noinspection DuplicatedCode
class Config(BaseConfig):
    nodes: Annotated[list[str], BeforeValidator(Validators.nodes())]
    routes: Annotated[list[TxRoute], BeforeValidator(Validators.sol_routes())]
    private_keys: Annotated[AddressToPrivate, BeforeValidator(Validators.sol_private_keys())]
    proxies: Annotated[list[str], Field(default_factory=list), BeforeValidator(Validators.proxies())]
    token: Annotated[str, AfterValidator(Validators.sol_address())]
    value: Annotated[str, AfterValidator(Validators.valid_token_expression("balance"))]
    value_min_limit: Annotated[str | None, AfterValidator(Validators.valid_token_expression())] = None
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

    decimals_res = get_decimals_with_retries(config.nodes, config.token, retries=3, proxies=config.proxies)
    if isinstance(decimals_res, Err):
        fatal(f"can't get decimals for token={config.token}, error={decimals_res.err}")

    token_decimals = decimals_res.ok
    logger.debug(f"token decimals={token_decimals}")

    if print_balances:
        _print_balances(config, token_decimals)
        sys.exit(0)

    _run_transfers(config, token_decimals, no_confirmation=no_confirmation, emulate=emulate)


def _run_transfers(config: Config, token_decimals: int, *, no_confirmation: bool, emulate: bool) -> None:
    logger.info(f"started at {utc_now()} UTC")
    logger.debug(f"config={config.model_dump(exclude={'private_keys'}) | {'version': cli_utils.get_version()}}")
    for i, route in enumerate(config.routes):
        _transfer(
            route=route,
            token_decimals=token_decimals,
            config=config,
            no_confirmation=no_confirmation,
            emulate=emulate,
        )
        if not emulate and config.delay is not None and i < len(config.routes) - 1:
            delay_value = mm_crypto_utils.calc_decimal_value(config.delay)
            logger.debug(f"delay {delay_value} seconds")
            time.sleep(float(delay_value))
    logger.info(f"finished at {utc_now()} UTC")


def _transfer(*, route: TxRoute, config: Config, token_decimals: int, no_confirmation: bool, emulate: bool) -> None:
    log_prefix = f"{route.from_address}->{route.to_address}"
    fee = 5000

    # get value
    value_res = calcs.calc_token_value_for_address(
        nodes=config.nodes,
        value_expression=config.value,
        wallet_address=route.from_address,
        proxies=config.proxies,
        token_mint_address=config.token,
        token_decimals=token_decimals,
    )
    logger.debug(f"{log_prefix}: value={value_res.ok_or_err()}")
    if isinstance(value_res, Err):
        logger.info(f"{log_prefix}: calc value error, {value_res.err}")
        return
    value = value_res.ok
    value_t = f"{to_token(value, decimals=token_decimals, ndigits=config.round_ndigits)}t"

    # value_min_limit
    if config.value_min_limit:
        value_min_limit = calcs.calc_token_expression(config.value_min_limit, token_decimals)
        if value < value_min_limit:
            logger.info(f"{log_prefix}: value<value_min_limit, value={value_t}")
            return

    if emulate:
        logger.info(f"{log_prefix}: emulate, value={value_t}, fee={fee}lamports")
        return

    logger.debug(f"{log_prefix}: value={to_token(value, decimals=token_decimals)}t, fee={fee}lamports")
    res = transfer.transfer_token_with_retries(
        nodes=config.nodes,
        token_mint_address=config.token,
        from_address=route.from_address,
        private_key=config.private_keys[route.from_address],
        to_address=route.to_address,
        amount=value,
        decimals=token_decimals,
        proxies=config.proxies,
        retries=3,
    )

    if isinstance(res, Err):
        logger.info(f"{log_prefix}: send_error: {res.err}")
        return
    signature = res.ok

    if no_confirmation:
        msg = f"{log_prefix}: sig={signature}, value={value_t}"
        logger.info(msg)
    else:
        logger.debug(f"{log_prefix}: sig={signature}, waiting for confirmation")
        status = "UNKNOWN"
        if cli_utils.wait_confirmation(config.nodes, config.proxies, signature, log_prefix):
            status = "OK"
        msg = f"{log_prefix}: sig={signature}, value={value_t}, status={status}"
        logger.info(msg)


def _print_balances(config: Config, token_decimals: int) -> None:
    table = Table("n", "from_address", "sol", "t", "to_address", "sol", "t", title="balances")
    with Live(table, refresh_per_second=0.5):
        for count, route in enumerate(config.routes):
            from_sol_balance = _get_sol_balance_str(route.from_address, config)
            to_sol_balance = _get_sol_balance_str(route.to_address, config)
            from_t_balance = _get_token_balance_str(route.from_address, config, token_decimals)
            to_t_balance = _get_token_balance_str(route.to_address, config, token_decimals)
            row: list[str] = [
                str(count),
                route.from_address,
                from_sol_balance,
                from_t_balance,
                route.to_address,
                to_sol_balance,
                to_t_balance,
            ]
            table.add_row(*row)


def _get_sol_balance_str(address: str, config: Config) -> str:
    return get_sol_balance_with_retries(config.nodes, address, proxies=config.proxies, retries=5).map_or_else(
        lambda err: err,
        lambda ok: str(lamports_to_sol(ok, config.round_ndigits)),
    )


def _get_token_balance_str(address: str, config: Config, token_decimals: int) -> str:
    return get_token_balance_with_retries(config.nodes, address, config.token, proxies=config.proxies, retries=5).map_or_else(
        lambda err: err,
        lambda ok: str(to_token(ok, token_decimals, ndigits=config.round_ndigits)),
    )
