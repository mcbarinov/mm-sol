from mm_std import print_console

from mm_solana.account import generate_account, get_private_key_arr_str


def run(limit: int, array: bool) -> None:
    result = {}
    for _ in range(limit):
        acc = generate_account()
        private_key = acc.private_key_base58
        if array:
            private_key = get_private_key_arr_str(acc.private_key_base58)
        result[acc.public_key] = private_key
    print_console(result, print_json=True)
