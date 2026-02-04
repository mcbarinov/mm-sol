"""Solana-specific config validators for CLI commands."""

from collections.abc import Callable

from mm_web3 import ConfigValidators
from mm_web3.account import PrivateKeyMap
from mm_web3.validators import Transfer

from mm_sol.account import get_public_key, is_address
from mm_sol.constants import UNIT_DECIMALS


class Validators(ConfigValidators):
    """Pydantic validators for Solana addresses, private keys, and value expressions."""

    @staticmethod
    def sol_address() -> Callable[[str], str]:
        """Return a validator for a single Solana address."""
        return ConfigValidators.address(is_address)

    @staticmethod
    def sol_addresses(unique: bool) -> Callable[[str], list[str]]:
        """Return a validator for a list of Solana addresses."""
        return ConfigValidators.addresses(unique, is_address=is_address)

    @staticmethod
    def sol_transfers() -> Callable[[str], list[Transfer]]:
        """Return a validator for transfer routes with Solana addresses."""
        return ConfigValidators.transfers(is_address)

    @staticmethod
    def sol_private_keys() -> Callable[[str], PrivateKeyMap]:
        """Return a validator for private key mappings."""
        return ConfigValidators.private_keys(get_public_key)

    @staticmethod
    def valid_sol_expression(var_name: str | None = None) -> Callable[[str], str]:
        """Return a validator for SOL value expressions."""
        return ConfigValidators.expression_with_vars(var_name, UNIT_DECIMALS)

    @staticmethod
    def valid_token_expression(var_name: str | None = None) -> Callable[[str], str]:
        """Return a validator for token value expressions with 6 decimal places."""
        return ConfigValidators.expression_with_vars(var_name, {"t": 6})

    @staticmethod
    def valid_sol_or_token_expression(var_name: str | None = None) -> Callable[[str], str]:
        """Return a validator accepting both SOL and token value expressions."""
        return ConfigValidators.expression_with_vars(var_name, UNIT_DECIMALS | {"t": 6})
