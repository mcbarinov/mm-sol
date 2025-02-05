import json

from mm_sol.account import PHANTOM_DERIVATION_PATH
from mm_sol.cli.cli import app


def test_mnemonic_cmd(cli_runner):
    mnemonic = "cotton limit tube replace sister flight double muffin health neutral hill maid"
    passphrase = "my-secret"
    path = PHANTOM_DERIVATION_PATH

    res = cli_runner.invoke(app, f"wallet mnemonic -m '{mnemonic}' -p '{passphrase}' --path '{path}' -l 11")
    assert res.exit_code == 0

    data = json.loads(res.stdout)
    assert len(data["accounts"]) == 11

    # pprint(data["accounts"][2])

    assert data["accounts"][2]["address"] == "Gdfo64rJK6eZBNaN1pRMM6u2aBdpTmuSSzwNNvN8wrbC"
    assert (
        data["accounts"][2]["private_key"]
        == "39YAWGyPPQBuzoCFNndZGqwHciLYPajfq3f9L37TxSrryvDB4cHKfJRWWQPx3shWAjojhayhvq8wfnf4fRrpqz2N"
    )


def test_mnemonic_cmd_generates_different_result(cli_runner):
    res1 = cli_runner.invoke(app, "wallet mnemonic -l 2")
    data1 = json.loads(res1.stdout)
    assert res1.exit_code == 0

    res2 = cli_runner.invoke(app, "wallet mnemonic -l 2")
    data2 = json.loads(res2.stdout)
    assert res2.exit_code == 0

    assert res1.stdout != res2.stdout
    assert data1["accounts"][1]["address"] != data2["accounts"][1]["address"]
    assert data1["accounts"][1]["private_key"] != data2["accounts"][1]["private_key"]
