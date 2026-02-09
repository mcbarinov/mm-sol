"""Keypair details display command."""

from pathlib import Path

from mm_clikit import print_json

from mm_sol.account import (
    get_private_key_arr_str,
    get_private_key_base58,
    get_public_key,
)


def run(private_key: str) -> None:
    """Print public key, base58 private key, and array private key from a private key input."""
    if (file := Path(private_key)).is_file():
        private_key = file.read_text()

    public = get_public_key(private_key)
    private_base58 = get_private_key_base58(private_key)
    private_arr = get_private_key_arr_str(private_key)
    print_json({"public": public, "private_base58": private_base58, "private_arr": private_arr})
