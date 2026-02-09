"""Mnemonic generation and account derivation command."""

from dataclasses import asdict
from typing import Any

from mm_clikit import print_json

from mm_sol.account import derive_accounts, generate_mnemonic


def run(mnemonic: str, passphrase: str, words: int, derivation_path: str, limit: int) -> None:  # nosec
    """Generate or use a mnemonic to derive accounts and print results."""
    result: dict[str, Any] = {}
    if not mnemonic:
        mnemonic = generate_mnemonic(words)
    result["mnemonic"] = mnemonic
    if passphrase:
        result["passphrase"] = passphrase
    accounts = derive_accounts(mnemonic=mnemonic, passphrase=passphrase, derivation_path=derivation_path, limit=limit)

    result["accounts"] = [asdict(acc) for acc in accounts]
    print_json(result)
