import mm_crypto_utils
from mm_crypto_utils import Nodes, Proxies
from mm_std import Err, Ok, Result
from solders.pubkey import Pubkey

from mm_sol.utils import get_client


def get_decimals(node: str, token_mint_address: str, timeout: float = 10, proxy: str | None = None) -> Result[int]:
    data = None
    try:
        client = get_client(node, proxy=proxy, timeout=timeout)
        res = client.get_token_supply(Pubkey.from_string(token_mint_address))
        data = res
        return Ok(res.value.decimals)
    except Exception as e:
        return Err(e, data=data)


def get_decimals_with_retries(
    nodes: Nodes, token_mint_address: str, retries: int, timeout: float = 10, proxies: Proxies = None
) -> Result[int]:
    res: Result[int] = Err("not started yet")
    for _ in range(retries):
        res = get_decimals(
            node=mm_crypto_utils.random_node(nodes),
            token_mint_address=token_mint_address,
            timeout=timeout,
            proxy=mm_crypto_utils.random_proxy(proxies),
        )
        if res.is_ok():
            return res
    return res
