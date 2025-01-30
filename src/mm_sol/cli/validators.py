from mm_crypto_utils import ConfigValidators

from mm_sol.cli import calcs


def is_valid_var_lamports(value: str | None, base_name: str = "var", decimals: int | None = None) -> bool:
    if value is None:
        return True  # check for None on BaseModel.field type level
    try:
        calcs.calc_var_value(value, var_value=123, var_name=base_name, decimals=decimals)
        return True  # noqa: TRY300
    except ValueError:
        return False


class Validators(ConfigValidators):
    pass
