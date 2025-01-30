import os
import random
from decimal import Decimal
from typing import Annotated, Any, Self

import mm_crypto_utils
from mm_crypto_utils import ConfigValidators
from mm_std import BaseConfig, print_json
from pydantic import BeforeValidator, Field, model_validator

import mm_sol.converters
from mm_sol import balance
from mm_sol.account import is_address
from mm_sol.balance import get_token_balance_with_retries


class Config(BaseConfig):
    accounts: Annotated[list[str], BeforeValidator(ConfigValidators.addresses(unique=True, is_address=is_address))]
    nodes: Annotated[list[str], BeforeValidator(ConfigValidators.nodes())]
    tokens: Annotated[list[str], BeforeValidator(ConfigValidators.addresses(unique=True, is_address=is_address))]
    proxies_url: str | None = None
    proxies: list[str] = Field(default_factory=list)

    @property
    def random_node(self) -> str:
        return random.choice(self.nodes)

    @model_validator(mode="after")
    def final_validator(self) -> Self:
        # fetch proxies from proxies_url
        proxies_url = self.proxies_url or os.getenv("MM_SOL_PROXIES_URL", "")
        if proxies_url:
            self.proxies += mm_crypto_utils.fetch_proxies_or_fatal(proxies_url)

        return self


def run(config_path: str, print_config: bool) -> None:
    config = Config.read_config_or_exit(config_path)
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
