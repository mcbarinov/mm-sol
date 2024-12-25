import random
from decimal import Decimal

from solana.rpc.api import Client
from solana.rpc.commitment import Commitment

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


def get_proxy(proxies: Proxies) -> str | None:
    if not proxies:
        return None
    if isinstance(proxies, str):
        return proxies
    return random.choice(proxies)


def get_client(
    endpoint: str,
    commitment: Commitment | None = None,
    extra_headers: dict[str, str] | None = None,
    proxy: str | None = None,
    timeout: float = 10,
) -> Client:
    return Client(endpoint, commitment=commitment, extra_headers=extra_headers, timeout=timeout, proxy=proxy)
