import random
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any

from mm_crypto_utils import ConfigValidators
from mm_std import BaseConfig, Err, fatal, print_json
from pydantic import BeforeValidator, Field

import mm_sol.converters
from mm_sol import balance
from mm_sol.balance import get_token_balance_with_retries
from mm_sol.cli.validators import Validators
from mm_sol.token import get_decimals_with_retries


class Config(BaseConfig):
    accounts: Annotated[list[str], BeforeValidator(Validators.sol_addresses(unique=True))]
    tokens: Annotated[list[str], BeforeValidator(Validators.sol_addresses(unique=True))]
    nodes: Annotated[list[str], BeforeValidator(ConfigValidators.nodes())]
    proxies: Annotated[list[str], Field(default_factory=list), BeforeValidator(Validators.proxies())]

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
            token_decimals_res = get_decimals_with_retries(config.nodes, token, retries=3, proxies=config.proxies)
            if isinstance(token_decimals_res, Err):
                fatal(f"Failed to get decimals for token {token}: {token_decimals_res.unwrap_err()}")
            token_decimals = token_decimals_res.unwrap()
            result[token] = _get_token_balances(token, token_decimals, config.accounts, config)
            result[token + "_decimals"] = token_decimals
            result[token + "_sum"] = sum([v for v in result[token].values() if v is not None])

    print_json(result)


def _get_token_balances(token: str, token_decimals: int, accounts: list[str], config: Config) -> dict[str, Decimal | None]:
    result = {}
    for account in accounts:
        result[account] = (
            get_token_balance_with_retries(
                nodes=config.nodes,
                owner_address=account,
                token_mint_address=token,
                retries=3,
                proxies=config.proxies,
            )
            .map(lambda v: mm_sol.converters.to_token(v, token_decimals))
            .unwrap_or(None)
        )
    return result


def _get_sol_balances(accounts: list[str], config: Config) -> dict[str, Decimal | None]:
    result = {}
    for account in accounts:
        res = balance.get_sol_balance_with_retries(nodes=config.nodes, address=account, retries=3, proxies=config.proxies)
        result[account] = mm_sol.converters.lamports_to_sol(res.unwrap(), ndigits=2) if res.is_ok() else None
    return result
