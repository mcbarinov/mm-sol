import mm_crypto_utils
from mm_crypto_utils import Nodes, Proxies, VarInt
from mm_std import Err, Ok, Result

from mm_sol.balance import get_sol_balance_with_retries, get_token_balance_with_retries
from mm_sol.constants import SUFFIX_DECIMALS


def calc_sol_expression(expression: str, var: VarInt | None = None) -> int:
    return mm_crypto_utils.calc_int_expression(expression, var=var, suffix_decimals=SUFFIX_DECIMALS)


def calc_token_expression(expression: str, token_decimals: int, var: VarInt | None = None) -> int:
    return mm_crypto_utils.calc_int_expression(expression, var=var, suffix_decimals={"t": token_decimals})


def calc_sol_value_for_address(*, nodes: Nodes, value_expression: str, address: str, proxies: Proxies, fee: int) -> Result[int]:
    value_expression = value_expression.lower()
    var = None
    if "balance" in value_expression:
        res = get_sol_balance_with_retries(nodes, address, proxies=proxies, retries=5)
        if isinstance(res, Err):
            return res
        var = VarInt("balance", res.ok)

    value = calc_sol_expression(value_expression, var)
    if "balance" in value_expression:
        value = value - fee
    return Ok(value)


def calc_token_value_for_address(
    *, nodes: Nodes, value_expression: str, wallet_address: str, token_mint_address: str, token_decimals: int, proxies: Proxies
) -> Result[int]:
    var = None
    value_expression = value_expression.lower()
    if "balance" in value_expression:
        res = get_token_balance_with_retries(
            nodes=nodes,
            owner_address=wallet_address,
            token_mint_address=token_mint_address,
            proxies=proxies,
            retries=5,
        )
        if isinstance(res, Err):
            return res
        var = VarInt("balance", res.ok)
    value = calc_token_expression(value_expression, token_decimals, var)
    return Ok(value)
