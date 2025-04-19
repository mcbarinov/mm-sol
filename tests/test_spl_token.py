import pytest

from mm_sol import spl_token
from mm_sol.account import generate_account

pytestmark = pytest.mark.asyncio


async def test_get_balance(mainnet_node, usdt_token_address, usdt_owner_address, random_proxy):
    res = await spl_token.get_balance(mainnet_node, usdt_owner_address, usdt_token_address, proxy=random_proxy)
    assert res.unwrap() > 0


async def test_get_balance_no_token_account(mainnet_node, usdt_token_address, random_proxy):
    res = await spl_token.get_balance(mainnet_node, generate_account().public_key, usdt_token_address, proxy=random_proxy)

    assert res.unwrap() == 0


async def test_get_decimals(mainnet_node, usdt_token_address, random_proxy):
    res = await spl_token.get_decimals(mainnet_node, usdt_token_address, proxy=random_proxy)
    assert res.unwrap() == 6
