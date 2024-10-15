from mm_solana.balance import get_balance


def test_get_balance(mainnet_node, usdt_owner_address, random_proxy):
    res = get_balance(mainnet_node, usdt_owner_address, proxy=random_proxy)
    assert res.unwrap() > 10
