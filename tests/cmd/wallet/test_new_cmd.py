import json

from mm_sol.account import get_public_key
from mm_sol.cli.cli import app


def test_new_cmd(cli_runner):
    res = cli_runner.invoke(app, "wallet new -l 11")
    assert res.exit_code == 0

    accounts = json.loads(res.stdout)
    assert len(accounts) == 11
    for address, private in accounts.items():
        assert address == get_public_key(private)


def test_new_generates_different_keys(cli_runner):
    res1 = cli_runner.invoke(app, "wallet new -l 2")
    assert res1.exit_code == 0

    res2 = cli_runner.invoke(app, "wallet new -l 2")
    assert res2.exit_code == 0

    assert res1.stdout != res2.stdout
