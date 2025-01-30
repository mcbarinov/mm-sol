import os
import sys
import time
from pathlib import Path
from typing import Annotated, Self

import mm_crypto_utils
from loguru import logger
from mm_crypto_utils import AddressToPrivate, TxRoute
from mm_std import BaseConfig, Err, utc_now
from pydantic import BeforeValidator, Field, model_validator
from solders.signature import Signature

from mm_sol import transfer
from mm_sol.account import get_public_key, is_address
from mm_sol.cli import calcs, cli_utils, validators
from mm_sol.cli.validators import Validators
from mm_sol.converters import lamports_to_sol
from mm_sol.utils import get_client


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

        # value
        if not validators.is_valid_var_lamports(self.value, "balance"):
            raise ValueError(f"wrong value: {self.value}")

        # value_min_limit
        if not validators.is_valid_var_lamports(self.value_min_limit):
            raise ValueError(f"wrong value_min_limit: {self.value_min_limit}")

        # delay
        if not validators.is_valid_var_lamports(self.delay):
            raise ValueError(f"wrong delay: {self.delay}")

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

    if print_balances:
        cli_utils.print_balances(config.nodes, config.from_addresses, round_ndigits=config.round_ndigits, proxies=config.proxies)
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
    value_res = calcs.calc_sol_value(
        nodes=config.nodes, value_str=config.value, address=from_address, proxies=config.proxies, fee=fee
    )
    logger.debug(f"{log_prefix}value={value_res.ok_or_err()}")
    if isinstance(value_res, Err):
        logger.info(f"{log_prefix}calc value error, {value_res.err}")
        return
    value = value_res.ok

    # value_min_limit
    if calcs.is_sol_value_less_min_limit(config.value_min_limit, value, log_prefix=log_prefix):
        return

    tx_params = {
        "fee": fee,
        "value": value,
        "to": to_address,
    }

    # emulate?
    if emulate:
        msg = f"{log_prefix}: emulate, value={lamports_to_sol(value, config.round_ndigits)}SOL,"
        msg += f" fee={fee}"
        logger.info(msg)
        return

    logger.debug(f"{log_prefix}: tx_params={tx_params}")

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
        if _wait_confirmation(config, signature, log_prefix):
            status = "OK"
        msg = f"{log_prefix}: sig={signature}, value={lamports_to_sol(value, config.round_ndigits)}, status={status}"
        logger.info(msg)


def _wait_confirmation(config: Config, signature: Signature, log_prefix: str) -> bool:
    count = 0
    while True:
        try:
            node = mm_crypto_utils.random_node(config.nodes)
            proxy = mm_crypto_utils.random_proxy(config.proxies)
            client = get_client(node, proxy=proxy)
            res = client.get_transaction(signature)
            if res.value and res.value.slot:  # check for tx error
                return True
        except Exception as e:
            logger.error(f"{log_prefix}: can't get confirmation, error={e}")
        time.sleep(1)
        count += 1
        if count > 30:
            logger.error(f"{log_prefix}: can't get confirmation, timeout")
            return False
