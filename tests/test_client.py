from mm_solana.utils import get_client


def test_proxy_client(mainnet_node, proxy):
    client = get_client(mainnet_node, proxy=proxy)
    assert client.get_block_height().value > 10_000_000
