from decimal import Decimal

import mm_crypto_utils
from mm_std import Ok, print_json
from pydantic import BaseModel, Field

import mm_sol.balance
from mm_sol import balance, token
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


def run(
    rpc_url: str,
    wallet_address: str,
    token_address: str | None,
    lamport: bool,
    proxies_url: str | None,
) -> None:
    result = BalanceResult()

    rpc_url = cli_utils.public_rpc_url(rpc_url)
    proxies = mm_crypto_utils.fetch_proxies_or_fatal(proxies_url) if proxies_url else None

    # sol balance
    sol_balance_res = balance.get_sol_balance_with_retries(rpc_url, wallet_address, retries=3, proxies=proxies)
    if isinstance(sol_balance_res, Ok):
        result.sol_balance = sol_balance_res.ok
    else:
        result.errors.append("sol_balance: " + sol_balance_res.err)

    # token balance
    if token_address:
        token_balance_res = mm_sol.balance.get_token_balance_with_retries(
            nodes=rpc_url,
            owner_address=wallet_address,
            token_mint_address=token_address,
            retries=3,
            proxies=proxies,
        )
        if isinstance(token_balance_res, Ok):
            result.token_balance = token_balance_res.ok
        else:
            result.errors.append("token_balance: " + token_balance_res.err)

        decimals_res = token.get_decimals_with_retries(rpc_url, token_address, retries=3, proxies=proxies)
        if isinstance(decimals_res, Ok):
            result.token_decimals = decimals_res.ok
        else:
            result.errors.append("token_decimals: " + decimals_res.err)

    if lamport:
        print_json(result)
    else:
        print_json(result.to_human_readable())
