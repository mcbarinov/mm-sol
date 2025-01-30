import mm_sol.balance
from mm_sol import token
from mm_sol.account import generate_account


def test_get_balance(mainnet_node, usdt_token_address, usdt_owner_address, proxies):
    res = mm_sol.balance.get_token_balance_with_retries(
        mainnet_node, usdt_owner_address, usdt_token_address, proxies=proxies, retries=3
    )
    assert res.unwrap() > 0


def test_get_balance_no_tokens_account_1(mainnet_node, usdt_token_address, random_proxy):
    res = mm_sol.balance.get_token_balance(
        mainnet_node,
        generate_account().public_key,
        usdt_token_address,
        proxy=random_proxy,
        no_token_accounts_return_zero=False,
    )
    assert res.err == "no_token_accounts"


def test_get_balance_no_tokens_account_2(mainnet_node, usdt_token_address, random_proxy):
    res = mm_sol.balance.get_token_balance(
        mainnet_node,
        generate_account().public_key,
        usdt_token_address,
        proxy=random_proxy,
    )
    assert res.ok == 0


def test_get_decimals(mainnet_node, usdt_token_address, random_proxy):
    res = token.get_decimals(mainnet_node, usdt_token_address, proxy=random_proxy)
    assert res.unwrap() == 6
