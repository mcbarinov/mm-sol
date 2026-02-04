"""Tests for Solana RPC client creation."""

from mm_sol.utils import get_client


def test_proxy_client(mainnet_node, random_proxy):
    """Verify client with proxy can fetch block height."""
    client = get_client(mainnet_node, proxy=random_proxy)
    assert client.get_block_height().value > 10_000_000
