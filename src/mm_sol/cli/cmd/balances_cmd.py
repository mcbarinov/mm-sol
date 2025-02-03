import random
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any

from mm_crypto_utils import ConfigValidators
from mm_std import BaseConfig, print_json
from pydantic import BeforeValidator

import mm_sol.converters
from mm_sol import balance
from mm_sol.balance import get_token_balance_with_retries
from mm_sol.cli.validators import Validators


class Config(BaseConfig):
    accounts: Annotated[list[str], BeforeValidator(Validators.sol_addresses(unique=True))]
    tokens: Annotated[list[str], BeforeValidator(Validators.sol_addresses(unique=True))]
    nodes: Annotated[list[str], BeforeValidator(ConfigValidators.nodes())]
    proxies: Annotated[list[str], BeforeValidator(Validators.proxies())]

    @property
    def random_node(self) -> str:
        return random.choice(self.nodes)


def run(config_path: Path, print_config: bool) -> None:
    config = Config.read_toml_config_or_exit(config_path)
    if print_config:
        config.print_and_exit()

    result: dict[str, Any] = {"sol": _get_sol_balances(config.accounts, config)}
    result["sol_sum"] = sum([v for v in result["sol"].values() if v is not None])

    if config.tokens:
        for token in config.tokens:
            result[token] = _get_token_balances(token, config.accounts, config)
            result[token + "_sum"] = sum([v for v in result[token].values() if v is not None])

    print_json(result)


def _get_token_balances(token: str, accounts: list[str], config: Config) -> dict[str, int | None]:
    result = {}
    for account in accounts:
        result[account] = get_token_balance_with_retries(
            nodes=config.nodes,
            owner_address=account,
            token_mint_address=token,
            retries=3,
            proxies=config.proxies,
        ).ok_or_none()
    return result


def _get_sol_balances(accounts: list[str], config: Config) -> dict[str, Decimal | None]:
    result = {}
    for account in accounts:
        res = balance.get_sol_balance_with_retries(nodes=config.nodes, address=account, retries=3, proxies=config.proxies)
        result[account] = mm_sol.converters.lamports_to_sol(res.unwrap(), ndigits=2) if res.is_ok() else None
    return result
