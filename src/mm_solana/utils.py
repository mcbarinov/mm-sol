import random
from decimal import Decimal

from mm_solana.rpc import DEFAULT_MAINNET_RPC


def lamports_to_sol(lamports: int, ndigits: int = 4) -> Decimal:
    return Decimal(str(round(lamports / 10**9, ndigits=ndigits)))


def get_node(nodes: str | list[str] | None = None) -> str:
    match nodes:
        case None:
            return DEFAULT_MAINNET_RPC
        case list():
            return random.choice(nodes)
        case _:
            return nodes


def get_proxy(proxies: str | list[str] | None) -> str | None:
    match proxies:
        case list():
            return random.choice(proxies)
        case None:
            return None
        case _:
            return proxies
