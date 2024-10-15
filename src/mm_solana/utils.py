import random
from decimal import Decimal

from mm_solana.rpc import DEFAULT_MAINNET_RPC
from mm_solana.types import Nodes, Proxies


def lamports_to_sol(lamports: int, ndigits: int = 4) -> Decimal:
    return Decimal(str(round(lamports / 10**9, ndigits=ndigits)))


def get_node(nodes: Nodes | None = None) -> str:
    if nodes is None:
        return DEFAULT_MAINNET_RPC
    if isinstance(nodes, str):
        return nodes
    return random.choice(nodes)
    # match nodes:
    #     case None:
    #         return DEFAULT_MAINNET_RPC
    #     case list():
    #         return random.choice(nodes)
    #     case _:
    #         return nodes


def get_proxy(proxies: Proxies) -> str | None:
    if not proxies:
        return None
    if isinstance(proxies, str):
        return proxies
    return random.choice(proxies)

    # match proxies:
    #     case [] | None:
    #         return None
    #     case list():
    #         return random.choice(proxies)
    #     case _:
    #         return proxies
