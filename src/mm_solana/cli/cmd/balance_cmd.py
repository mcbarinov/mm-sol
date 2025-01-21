import random
from decimal import Decimal
from typing import Any

from mm_std import BaseConfig, print_console, str_to_list
from pydantic import StrictStr, field_validator

from mm_solana import balance, utils
from mm_solana.cli import cli_utils
from mm_solana.token import get_balance_with_retries


class Config(BaseConfig):
    accounts: list[StrictStr]
    nodes: list[StrictStr]
    tokens: list[StrictStr] | None = None

    @classmethod
    @field_validator("accounts", "nodes", "tokens", mode="before")
    def to_list_validator(cls, v: list[str] | str | None) -> list[str]:
        return str_to_list(v)

    @property
    def random_node(self) -> str:
        return random.choice(self.nodes)


def run(config_path: str, print_config: bool) -> None:
    config = Config.read_config_or_exit(config_path)
    cli_utils.print_config_and_exit(print_config, config)

    # config = parse_config(ctx, config_path, Config)
    # print_config_and_exit(ctx, config)
    result: dict[str, Any] = {"sol": _get_sol_balances(config.accounts, config.nodes)}
    result["sol_sum"] = sum([v for v in result["sol"].values() if v is not None])

    if config.tokens:
        for token in config.tokens:
            result[token] = _get_token_balances(token, config.accounts, config.nodes)
            result[token + "_sum"] = sum([v for v in result[token].values() if v is not None])

    print_console(result, print_json=True)


def _get_token_balances(token: str, accounts: list[str], nodes: list[str]) -> dict[str, int | None]:
    result = {}
    for account in accounts:
        # result[account] = _get_token_balance(token, account, nodes)
        result[account] = get_balance_with_retries(
            nodes=nodes,
            owner_address=account,
            token_mint_address=token,
            retries=3,
        ).ok_or_none()
    return result


def _get_sol_balances(accounts: list[str], nodes: list[str]) -> dict[str, Decimal | None]:
    result = {}
    for account in accounts:
        res = balance.get_balance_with_retries(nodes=nodes, address=account, retries=3)
        result[account] = utils.lamports_to_sol(res.unwrap(), ndigits=2) if res.is_ok() else None
    return result
