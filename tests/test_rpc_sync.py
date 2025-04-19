from mm_sol import rpc_sync


def test_get_balance(mainnet_node, binance_wallet, random_proxy):
    res = rpc_sync.get_balance(mainnet_node, binance_wallet, proxy=random_proxy)
    assert res.unwrap() > 10_000_000


def test_get_block_height(mainnet_node, random_proxy):
    res = rpc_sync.get_block_height(mainnet_node, proxy=random_proxy)
    assert res.unwrap() > 10_000_000


def test_get_slot(testnet_node, random_proxy):
    res = rpc_sync.get_slot(testnet_node, proxy=random_proxy)
    assert res.unwrap() > 10_000


def test_get_epoch_info(testnet_node, random_proxy):
    res = rpc_sync.get_epoch_info(testnet_node, proxy=random_proxy)
    assert res.unwrap().epoch > 500


def test_get_health(mainnet_node, testnet_node, random_proxy):
    res = rpc_sync.get_health(mainnet_node, proxy=random_proxy)
    assert res.unwrap() is True

    res = rpc_sync.get_health(testnet_node, proxy=random_proxy)
    assert res.unwrap() is True


def test_get_cluster_nodes(testnet_node, random_proxy):
    res = rpc_sync.get_cluster_nodes(testnet_node, proxy=random_proxy)
    assert len(res.unwrap()) > 10


def test_get_vote_accounts(testnet_node, random_proxy):
    res = rpc_sync.get_vote_accounts(testnet_node, timeout=60, proxy=random_proxy)
    assert len(res.unwrap()) > 10


def test_get_leader_scheduler(testnet_node, random_proxy):
    res = rpc_sync.get_leader_scheduler(testnet_node, proxy=random_proxy)
    assert len(res.unwrap()) > 10


def test_get_transaction(mainnet_node, random_proxy):
    tx_hash = "2vifJ5g4inS4spZLQMUyVstvMrCM2mg1QC9xjD6bgsiMUwp8sTE5waCdshJ8SVaH95WGtexjH3q8ot1GoKe9yK3h"
    res = rpc_sync.get_transaction(mainnet_node, tx_hash, 0, proxy=random_proxy)
    assert res.unwrap()["blockTime"] == 1708667439
