from mm_std import Err, Result

from mm_solana import rpc, token, utils


def sol_balance(
    *,
    address: str,
    nodes: str | list[str] | None = None,
    proxies: str | list[str] | None = None,
    attempts: int = 1,
    timeout: int = 10,
) -> Result[int]:
    res: Result[int] = Err("not started yet")
    for _ in range(attempts):
        res = rpc.get_balance(utils.get_node(nodes), address, timeout, utils.get_proxy(proxies))
        if res.is_ok():
            return res
    return res


def token_balance(
    *,
    token_mint_address: str,
    wallet_address: str,
    nodes: str | list[str] | None = None,
    attempts: int = 1,
) -> Result[int]:
    res: Result[int] = Err("not started yet")
    for _ in range(attempts):
        res = token.get_balance(node=utils.get_node(nodes), owner_address=wallet_address, token_mint_address=token_mint_address)
        if res.is_ok():
            return res
    return res
