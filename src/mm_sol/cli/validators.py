from collections.abc import Callable

from mm_crypto_utils import AddressToPrivate, ConfigValidators, Transfer

from mm_sol.account import get_public_key, is_address
from mm_sol.constants import SUFFIX_DECIMALS


class Validators(ConfigValidators):
    @staticmethod
    def sol_address() -> Callable[[str], str]:
        return ConfigValidators.address(is_address)

    @staticmethod
    def sol_addresses(unique: bool) -> Callable[[str], list[str]]:
        return ConfigValidators.addresses(unique, is_address=is_address)

    @staticmethod
    def sol_transfers() -> Callable[[str], list[Transfer]]:
        return ConfigValidators.transfers(is_address)

    @staticmethod
    def sol_private_keys() -> Callable[[str], AddressToPrivate]:
        return ConfigValidators.private_keys(get_public_key)

    @staticmethod
    def valid_sol_expression(var_name: str | None = None) -> Callable[[str], str]:
        return ConfigValidators.valid_calc_int_expression(var_name, SUFFIX_DECIMALS)

    @staticmethod
    def valid_token_expression(var_name: str | None = None) -> Callable[[str], str]:
        return ConfigValidators.valid_calc_int_expression(var_name, {"t": 6})

    @staticmethod
    def valid_sol_or_token_expression(var_name: str | None = None) -> Callable[[str], str]:
        return ConfigValidators.valid_calc_int_expression(var_name, SUFFIX_DECIMALS | {"t": 6})
