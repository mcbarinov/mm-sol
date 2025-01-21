import json

from typer.testing import CliRunner

from mm_solana.account import get_public_key
from mm_solana.cli.cli import app

runner = CliRunner()


def test_new_cmd():
    res = runner.invoke(app, "wallet new -l 11")
    assert res.exit_code == 0

    accounts = json.loads(res.stdout)
    assert len(accounts) == 11
    for address, private in accounts.items():
        assert address == get_public_key(private)


def test_new_generates_different_keys():
    res1 = runner.invoke(app, "wallet new -l 2")
    assert res1.exit_code == 0

    res2 = runner.invoke(app, "wallet new -l 2")
    assert res2.exit_code == 0

    assert res1.stdout != res2.stdout
