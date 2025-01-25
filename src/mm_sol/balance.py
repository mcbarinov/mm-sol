from mm_std import Err, Result

from mm_sol import rpc
from mm_sol.types_ import Nodes, Proxies
from mm_sol.utils import get_node, get_proxy


def get_balance(node: str, address: str, timeout: int = 10, proxy: str | None = None) -> Result[int]:
    return rpc.get_balance(node, address, timeout, proxy)


def get_balance_with_retries(nodes: Nodes, address: str, retries: int, timeout: int = 10, proxies: Proxies = None) -> Result[int]:
    res: Result[int] = Err("not started yet")
    for _ in range(retries):
        res = get_balance(get_node(nodes), address, timeout=timeout, proxy=get_proxy(proxies))
        if res.is_ok():
            return res
    return res
