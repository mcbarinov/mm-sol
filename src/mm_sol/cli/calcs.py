import random
from decimal import Decimal

import mm_crypto_utils
from loguru import logger
from mm_crypto_utils import Nodes, Proxies
from mm_std import Ok, Result
from mm_std.str import split_on_plus_minus_tokens

from mm_sol.balance import get_sol_balance_with_retries, get_token_balance_with_retries
from mm_sol.converters import lamports_to_sol, sol_to_lamports, to_lamports


def calc_var_value(value: str, *, var_name: str = "var", var_value: int | None = None, decimals: int | None = None) -> int:
    if not isinstance(value, str):
        raise TypeError(f"value is not str: {value}")
    try:
        var_name = var_name.lower()
        result = 0
        for token in split_on_plus_minus_tokens(value.lower()):
            operator = token[0]
            item = token[1:]
            if item.isdigit():
                item_value = int(item)
            elif item.endswith("sol"):
                item = item.removesuffix("sol")
                item_value = sol_to_lamports(Decimal(item))
            elif item.endswith("t"):
                if decimals is None:
                    raise ValueError("t without decimals")  # noqa: TRY301
                item = item.removesuffix("t")
                item_value = int(Decimal(item) * 10**decimals)
            elif item.endswith(var_name):
                if var_value is None:
                    raise ValueError("base value is not set")  # noqa: TRY301
                item = item.removesuffix(var_name)
                k = Decimal(item) if item else Decimal(1)
                item_value = int(k * var_value)
            elif item.startswith("random(") and item.endswith(")"):
                item = item.lstrip("random(").rstrip(")")
                arr = item.split(",")
                if len(arr) != 2:
                    raise ValueError(f"wrong value, random part: {value}")  # noqa: TRY301
                from_value = to_lamports(arr[0], decimals=decimals)
                to_value = to_lamports(arr[1], decimals=decimals)
                if from_value > to_value:
                    raise ValueError(f"wrong value, random part: {value}")  # noqa: TRY301
                item_value = random.randint(from_value, to_value)
            else:
                raise ValueError(f"wrong value: {value}")  # noqa: TRY301

            if operator == "+":
                result += item_value
            if operator == "-":
                result -= item_value

        return result  # noqa: TRY300
    except Exception as err:
        raise ValueError(f"wrong value: {value}, error={err}") from err


def is_sol_value_less_min_limit(value_min_limit: str | None, value: int, log_prefix: str | None = None) -> bool:
    if value_min_limit is None:
        return False
    if value < calc_var_value(value_min_limit):
        prefix = mm_crypto_utils.get_log_prefix(log_prefix)
        logger.info("{}value is less min limit, value={}", prefix, lamports_to_sol(value))
        return True
    return False


def calc_sol_value(*, nodes: Nodes, value_str: str, address: str, proxies: Proxies, fee: int = 5000) -> Result[int]:
    balance_value = None
    if "balance" in value_str.lower():
        res = get_sol_balance_with_retries(nodes, address, proxies=proxies, retries=5)
        if res.is_err():
            return res
        balance_value = res.ok
    value = calc_var_value(value_str, var_name="balance", var_value=balance_value)
    if "balance" in value_str.lower():
        value = value - fee
    return Ok(value)


def calc_token_value(
    *, nodes: Nodes, value_str: str, wallet_address: str, token_mint_address: str, token_decimals: int, proxies: Proxies
) -> Result[int]:
    balance_value = None
    if "balance" in value_str.lower():
        res = get_token_balance_with_retries(
            nodes=nodes,
            owner_address=wallet_address,
            token_mint_address=token_mint_address,
            proxies=proxies,
            retries=5,
        )
        if res.is_err():
            return res
        balance_value = res.ok
    value = calc_var_value(value_str, var_name="balance", var_value=balance_value, decimals=token_decimals)
    return Ok(value)
