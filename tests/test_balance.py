import pytest

from mm_sol.balance import get_sol_balance, get_sol_balance_async, get_token_balance, get_token_balance_async

pytestmark = pytest.mark.anyio


def test_get_sol_balance(mainnet_node, usdt_owner_address, random_proxy):
    res = get_sol_balance(mainnet_node, usdt_owner_address, proxy=random_proxy)
    assert res.unwrap() > 10


async def test_get_sol_balance_async(mainnet_node, usdt_owner_address, random_proxy):
    res = await get_sol_balance_async(mainnet_node, usdt_owner_address, proxy=random_proxy)
    assert res.unwrap() > 10


def test_get_token_balance(mainnet_node, binance_wallet, usdt_token_address, random_proxy):
    res = get_token_balance(mainnet_node, binance_wallet, usdt_token_address, proxy=random_proxy)
    assert res.unwrap() > 10


async def test_get_token_balance_async(mainnet_node, binance_wallet, usdt_token_address, random_proxy):
    res = await get_token_balance_async(mainnet_node, binance_wallet, usdt_token_address, proxy=random_proxy)
    assert res.unwrap() > 10
