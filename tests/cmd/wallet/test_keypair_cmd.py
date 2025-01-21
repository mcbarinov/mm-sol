import json

from typer.testing import CliRunner

from mm_solana.cli.cli import app

runner = CliRunner()


def test_new_cmd():
    public = "FkXw3cUycwsMYHAGacfhBJpa31WTvq5bUZNGhCW4GFVD"
    private_base58 = "3JTDggs2wpXWbQoL44XGHWzkAvC2LsfTVcx7gPX1dw7izxQ77oMvnMxCnCHQCGrM1RviAVpPhLexsjJKxqVq9Zqd"
    private_arr = "[115,21,127,168,159,11,95,157,134,159,18,133,4,114,119,129,96,140,193,211,35,139,32,177,172,204,5,2,193,94,194,122,219,42,145,4,32,80,123,141,81,235,64,60,55,47,81,102,41,253,60,85,116,238,173,120,98,38,211,48,253,89,18,196]"  # noqa: E501
    res = runner.invoke(app, f"wallet keypair {private_base58}")
    assert res.exit_code == 0

    keypair = json.loads(res.stdout)
    assert keypair["public"] == public
    assert keypair["private_base58"] == private_base58
    assert keypair["private_arr"] == private_arr
