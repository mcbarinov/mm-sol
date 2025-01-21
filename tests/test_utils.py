from decimal import Decimal

from mm_solana import utils
from mm_solana.rpc import DEFAULT_MAINNET_RPC


def test_lamports_to_sol():
    res = utils.lamports_to_sol(272356343007, ndigits=4)
    assert res == Decimal("272.3563")


def test_get_node():
    assert utils.get_node() == DEFAULT_MAINNET_RPC
    assert utils.get_node("n1") == "n1"
    res = utils.get_node(["n1", "n2"])
    assert res in ("n1", "n2")


def test_get_proxy():
    assert utils.get_proxy([]) is None
