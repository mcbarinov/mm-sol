from mm_solana.balance import sol_balance


def test_sol_balance(mainnet_node, usdt_owner_address):
    res = sol_balance(address=usdt_owner_address, nodes=mainnet_node)
    assert res.unwrap() > 10
