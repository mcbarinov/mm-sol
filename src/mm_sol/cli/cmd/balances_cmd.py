"""Multi-account balances query command."""

import random
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any

from mm_print import print_json
from mm_web3 import ConfigValidators, Web3CliConfig
from pydantic import BeforeValidator, Field

import mm_sol.retry
from mm_sol import converters, retry
from mm_sol.cli.cli_utils import fatal
from mm_sol.cli.validators import Validators


class Config(Web3CliConfig):
    """Configuration for the balances command."""

    accounts: Annotated[list[str], BeforeValidator(Validators.sol_addresses(unique=True))]
    tokens: Annotated[list[str], BeforeValidator(Validators.sol_addresses(unique=True))]
    nodes: Annotated[list[str], BeforeValidator(ConfigValidators.nodes())]
    proxies: Annotated[list[str], Field(default_factory=list), BeforeValidator(Validators.proxies())]

    @property
    def random_node(self) -> str:
        """Return a randomly selected RPC node URL."""
        return random.choice(self.nodes)


async def run(config_path: Path, print_config: bool) -> None:
    """Fetch and print SOL and token balances for all configured accounts."""
    config = Config.read_toml_config_or_exit(config_path)
    if print_config:
        config.print_and_exit()

    result: dict[str, Any] = {"sol": await _get_sol_balances(config.accounts, config)}
    result["sol_sum"] = sum([v for v in result["sol"].values() if v is not None])

    if config.tokens:
        for token_address in config.tokens:
            res = await mm_sol.retry.get_token_decimals(3, config.nodes, config.proxies, token=token_address)
            if res.is_err():
                fatal(f"Failed to get decimals for token {token_address}: {res.unwrap_err()}")

            token_decimals = res.unwrap()
            result[token_address] = await _get_token_balances(token_address, token_decimals, config.accounts, config)
            result[token_address + "_decimals"] = token_decimals
            result[token_address + "_sum"] = sum([v for v in result[token_address].values() if v is not None])

    print_json(result)


async def _get_token_balances(
    token_address: str, token_decimals: int, accounts: list[str], config: Config
) -> dict[str, Decimal | None]:
    """Fetch token balances for all accounts, returning a dict of address to balance."""
    result: dict[str, Decimal | None] = {}
    for account in accounts:
        result[account] = (
            (await mm_sol.retry.get_token_balance(3, config.nodes, config.proxies, owner=account, token=token_address))
            .map(lambda v: converters.to_token(v, token_decimals))
            .value
        )

    return result


async def _get_sol_balances(accounts: list[str], config: Config) -> dict[str, Decimal | None]:
    """Fetch SOL balances for all accounts, returning a dict of address to balance."""
    result = {}
    for account in accounts:
        result[account] = (
            (await retry.get_sol_balance(3, config.nodes, config.proxies, address=account)).map(converters.lamports_to_sol).value
        )

    return result
