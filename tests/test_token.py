import mm_sol.balance
from mm_sol import token
from mm_sol.account import generate_account


def test_get_balance(mainnet_node, usdt_token_address, usdt_owner_address, proxies):
    res = mm_sol.balance.get_token_balance_with_retries(
        mainnet_node, usdt_owner_address, usdt_token_address, proxies=proxies, retries=3
    )
    assert res.unwrap() > 0


def test_get_balance_no_tokens_account(mainnet_node, usdt_token_address, proxies):
    res = mm_sol.balance.get_token_balance_with_retries(
        mainnet_node, generate_account().public_key, usdt_token_address, proxies=proxies, retries=5
    )
    assert res.ok == 0


def test_get_decimals(mainnet_node, usdt_token_address, proxies):
    res = token.get_decimals_with_retries(mainnet_node, usdt_token_address, proxies=proxies, retries=5)
    assert res.unwrap() == 6
