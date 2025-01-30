from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
from solders.pubkey import Pubkey


def get_client(
    endpoint: str,
    commitment: Commitment | None = None,
    extra_headers: dict[str, str] | None = None,
    proxy: str | None = None,
    timeout: float = 10,
) -> Client:
    return Client(endpoint, commitment=commitment, extra_headers=extra_headers, timeout=timeout, proxy=proxy)


def pubkey(value: str | Pubkey) -> Pubkey:
    if isinstance(value, Pubkey):
        return value
    return Pubkey.from_string(value)
