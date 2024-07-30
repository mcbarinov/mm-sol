import click
from mm_solana.account import generate_account, get_private_key_arr_str
from mm_std import print_console


@click.command(name="generate-accounts", help="Generate new accounts")
@click.option("--limit", "-l", type=int, default=5)
@click.option("--array", is_flag=True, help="Print private key in the array format.")
def cli(limit: int, array: bool) -> None:
    result = {}
    for _ in range(limit):
        acc = generate_account()
        private_key = acc.private_key_base58
        if array:
            private_key = get_private_key_arr_str(acc.private_key_base58)
        result[acc.public_key] = private_key
    print_console(result, print_json=True)
