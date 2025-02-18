import httpx
from mm_crypto_utils import Nodes, Proxies, random_node, random_proxy
from mm_std import Err, Ok, Result
from solana.exceptions import SolanaRpcException
from solana.rpc.core import RPCException
from solders.pubkey import Pubkey
from solders.rpc.errors import InvalidParamsMessage
from spl.token.instructions import get_associated_token_address

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
) -> Result[int]:
    try:
        client = get_client(node, proxy=proxy, timeout=timeout)
        if not token_account:
            token_account = str(
                get_associated_token_address(Pubkey.from_string(owner_address), Pubkey.from_string(token_mint_address))
            )

        res = client.get_token_account_balance(Pubkey.from_string(token_account))

        # Sometimes it not raise an error, but it returns this :(
        if isinstance(res, InvalidParamsMessage) and "could not find account" in res.message:
            return Ok(0)
        return Ok(int(res.value.amount), data=res.to_json())
    except RPCException as e:
        if len(e.args) > 1:
            s = e.args[0]
            if isinstance(s, InvalidParamsMessage) and "could not find account" in s.message:
                return Ok(0)
        return Err(e)
    except httpx.HTTPStatusError as e:
        return Err(f"http error: {e}")
    except SolanaRpcException as e:
        return Err(e.error_msg)
    except Exception as e:
        return Err(e)


def get_token_balance_with_retries(
    nodes: Nodes,
    owner_address: str,
    token_mint_address: str,
    retries: int,
    token_account: str | None = None,
    timeout: float = 10,
    proxies: Proxies = None,
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
        )
        if res.is_ok():
            return res

    return res
