from decimal import Decimal

import mm_print
from mm_web3 import fetch_proxies
from pydantic import BaseModel, Field

import mm_sol.retry
from mm_sol import retry
from mm_sol.cli import cli_utils


class HumanReadableBalanceResult(BaseModel):
    sol_balance: Decimal | None
    token_balance: Decimal | None
    token_decimals: int | None
    errors: list[str]


class BalanceResult(BaseModel):
    sol_balance: int | None = None
    token_balance: int | None = None
    token_decimals: int | None = None
    errors: list[str] = Field(default_factory=list)

    def to_human_readable(self) -> HumanReadableBalanceResult:
        sol_balance = Decimal(self.sol_balance) / 10**9 if self.sol_balance is not None else None
        token_balance = None
        if self.token_balance is not None and self.token_decimals is not None:
            token_balance = Decimal(self.token_balance) / 10**self.token_decimals
        return HumanReadableBalanceResult(
            sol_balance=sol_balance, token_balance=token_balance, token_decimals=self.token_decimals, errors=self.errors
        )


async def run(
    rpc_url: str,
    wallet_address: str,
    token_address: str | None,
    lamport: bool,
    proxies_url: str | None,
) -> None:
    result = BalanceResult()

    rpc_url = cli_utils.public_rpc_url(rpc_url)

    proxies = (await fetch_proxies(proxies_url)).unwrap() if proxies_url else None

    # sol balance
    sol_balance_res = await retry.get_sol_balance(3, rpc_url, proxies, address=wallet_address)
    if sol_balance_res.is_ok():
        result.sol_balance = sol_balance_res.unwrap()
    else:
        result.errors.append("sol_balance: " + sol_balance_res.unwrap_err())

    # token balance
    if token_address:
        token_balance_res = await mm_sol.retry.get_token_balance(3, rpc_url, proxies, owner=wallet_address, token=token_address)

        if token_balance_res.is_ok():
            result.token_balance = token_balance_res.unwrap()
        else:
            result.errors.append("token_balance: " + token_balance_res.unwrap_err())

        decimals_res = await mm_sol.retry.get_token_decimals(3, rpc_url, proxies, token=token_address)
        if decimals_res.is_ok():
            result.token_decimals = decimals_res.unwrap()
        else:
            result.errors.append("token_decimals: " + decimals_res.unwrap_err())

    if lamport:
        mm_print.json(result)
    else:
        mm_print.json(result.to_human_readable())
