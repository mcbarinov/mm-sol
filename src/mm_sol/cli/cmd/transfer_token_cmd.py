import os
import sys
import time
from pathlib import Path
from typing import Annotated, Self

import mm_crypto_utils
import typer
from loguru import logger
from mm_crypto_utils import AddressToPrivate, TxRoute
from mm_std import BaseConfig, Err, fatal, utc_now
from pydantic import AfterValidator, BeforeValidator, Field, model_validator

from mm_sol.account import get_public_key, is_address
from mm_sol.cli import calcs, cli_utils
from mm_sol.cli.validators import Validators
from mm_sol.token import get_decimals_with_retries


class Config(BaseConfig):
    nodes: Annotated[list[str], BeforeValidator(Validators.nodes())]
    routes: Annotated[list[TxRoute], BeforeValidator(Validators.routes(is_address))]
    routes_from_file: Path | None = None
    routes_to_file: Path | None = None
    private_keys: Annotated[
        AddressToPrivate, Field(default_factory=AddressToPrivate), BeforeValidator(Validators.private_keys(get_public_key))
    ]
    private_keys_file: Path | None = None
    proxies_url: str | None = None
    proxies: list[str] = Field(default_factory=list)
    token: Annotated[str, AfterValidator(Validators.address(is_address))]
    value: str
    value_min_limit: str | None = None
    delay: str | None = None  # in seconds
    round_ndigits: int = 5
    log_debug: Annotated[Path | None, BeforeValidator(Validators.log_file())] = None
    log_info: Annotated[Path | None, BeforeValidator(Validators.log_file())] = None

    @property
    def from_addresses(self) -> list[str]:
        return [r.from_address for r in self.routes]

    @model_validator(mode="after")
    def final_validator(self) -> Self:
        # routes_files
        if self.routes_from_file and self.routes_to_file:
            self.routes += TxRoute.from_files(self.routes_from_file, self.routes_to_file, is_address)
        if not self.routes:
            raise ValueError("routes is empty")

        # load private keys from file
        if self.private_keys_file:
            self.private_keys.update(AddressToPrivate.from_file(self.private_keys_file, get_public_key))

        # check all private keys exist
        if not self.private_keys.contains_all_addresses(self.from_addresses):
            raise ValueError("private keys are not set for all addresses")

        # fetch proxies from proxies_url
        proxies_url = self.proxies_url or os.getenv("MM_PROXIES_URL", "")
        if proxies_url:
            self.proxies += mm_crypto_utils.fetch_proxies_or_fatal(proxies_url)

        return self


def run(
    config_path: str,
    *,
    print_balances: bool,
    print_config: bool,
    debug: bool,
    no_confirmation: bool,
    emulate: bool,
) -> None:
    config = Config.read_config_or_exit(config_path)

    if print_config:
        config.print_and_exit({"private_keys", "proxies"})

    mm_crypto_utils.init_logger(debug, config.log_debug, config.log_info)

    decimals_res = get_decimals_with_retries(config.nodes, config.token, retries=3, proxies=config.proxies)
    if isinstance(decimals_res, Err):
        fatal(f"can't get decimals for token={config.token}, error={decimals_res.err}")

    token_decimals = decimals_res.ok
    logger.debug(f"token decimals={token_decimals}")

    if print_balances:
        # cli_utils.print_balances(config.nodes, config.from_addresses, round_ndigits=config.round_ndigits, proxies=config.proxies) # noqa: E501
        typer.echo("Not implemented yet")
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
    value_res = calcs.calc_token_value(
        nodes=config.nodes,
        value_str=config.value,
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

    logger.debug(f"{log_prefix}: value={value}, fee={fee}, no_confirmation={no_confirmation}, emulate={emulate}")
