from mm_solana import token
from mm_solana.account import generate_account


def test_get_balance(mainnet_node, usdt_token_address, usdt_owner_address):
    # existing token account
    res = token.get_balance(mainnet_node, usdt_owner_address, usdt_token_address)
    assert res.ok > 0

    res = token.get_balance(mainnet_node, generate_account().public_key, usdt_token_address)
    assert res.err == "no_token_accounts"
