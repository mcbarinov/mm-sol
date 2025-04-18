import pytest

from mm_sol import rpc

pytestmark = pytest.mark.asyncio


async def test_get_balance(mainnet_node, binance_wallet, random_proxy):
    res = await rpc.get_balance(mainnet_node, binance_wallet, proxy=random_proxy)
    assert res.unwrap() > 10_000_000
