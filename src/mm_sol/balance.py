import httpx
from mm_crypto_utils import Nodes, Proxies, random_node, random_proxy
from mm_std import Err, Ok, Result
from solana.exceptions import SolanaRpcException
from solana.rpc.types import TokenAccountOpts
from solders.pubkey import Pubkey

from mm_sol import rpc
from mm_sol.utils import get_client


def get_sol_balance(node: str, address: str, timeout: int = 10, proxy: str | None = None) -> Result[int]:
    return rpc.get_balance(node, address, timeout, proxy)


def get_sol_balance_with_retries(
    nodes: Nodes, address: str, retries: int, timeout: int = 10, proxies: Proxies = None
) -> Result[int]:
    res: Result[int] = Err("not started yet")
    for _ in range(retries):
        res = get_sol_balance(random_node(nodes), address, timeout=timeout, proxy=random_proxy(proxies))
        if res.is_ok():
            return res
    return res


def get_token_balance(
    node: str,
    owner_address: str,
    token_mint_address: str,
    token_account: str | None = None,
    timeout: float = 10,
    proxy: str | None = None,
    no_token_accounts_return_zero: bool = True,
) -> Result[int]:
    data: list[object] = []
    try:
        client = get_client(node, proxy=proxy, timeout=timeout)
        if token_account:
            res_balance = client.get_token_account_balance(Pubkey.from_string(token_account))
            data.append(res_balance)
            return Ok(int(res_balance.value.amount))

        res_accounts = client.get_token_accounts_by_owner(
            Pubkey.from_string(owner_address),
            TokenAccountOpts(mint=Pubkey.from_string(token_mint_address)),
        )
        data.append(res_accounts)

        if no_token_accounts_return_zero and not res_accounts.value:
            return Ok(0)
        if not res_accounts.value:
            return Err("no_token_accounts")

        token_accounts = [a.pubkey for a in res_accounts.value]
        balances = []
        for token_account_ in token_accounts:
            res = client.get_token_account_balance(token_account_)
            data.append(res)
            if res.value:  # type:ignore[truthy-bool]
                balances.append(int(res.value.amount))

        return Ok(sum(balances))
    except httpx.HTTPStatusError as e:
        return Err(f"http error: {e}", data=data)
    except SolanaRpcException as e:
        return Err(e.error_msg, data=data)
    except Exception as e:
        return Err(e, data=data)


def get_token_balance_with_retries(
    nodes: Nodes,
    owner_address: str,
    token_mint_address: str,
    retries: int,
    token_account: str | None = None,
    timeout: float = 10,
    proxies: Proxies = None,
    no_token_accounts_return_zero: bool = True,
) -> Result[int]:
    res: Result[int] = Err("not started yet")
    for _ in range(retries):
        res = get_token_balance(
            random_node(nodes),
            owner_address,
            token_mint_address,
            token_account,
            timeout=timeout,
            proxy=random_proxy(proxies),
            no_token_accounts_return_zero=no_token_accounts_return_zero,
        )
        if res.is_ok():
            return res
    return res
