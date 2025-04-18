import mm_crypto_utils
from mm_crypto_utils import Nodes, Proxies, VarInt
from mm_std import Result

from mm_sol import rpc, spl_token
from mm_sol.constants import SUFFIX_DECIMALS


def calc_sol_expression(expression: str, var: VarInt | None = None) -> int:
    return mm_crypto_utils.calc_int_expression(expression, var=var, suffix_decimals=SUFFIX_DECIMALS)


def calc_token_expression(expression: str, token_decimals: int, var: VarInt | None = None) -> int:
    return mm_crypto_utils.calc_int_expression(expression, var=var, suffix_decimals={"t": token_decimals})


async def calc_sol_value_for_address(
    *, nodes: Nodes, value_expression: str, address: str, proxies: Proxies, fee: int
) -> Result[int]:
    value_expression = value_expression.lower()
    var = None
    if "balance" in value_expression:
        res = await rpc.get_balance_with_retries(5, nodes, proxies, address=address)
        if res.is_error():
            return res
        var = VarInt("balance", res.unwrap())

    value = calc_sol_expression(value_expression, var)
    if "balance" in value_expression:
        value = value - fee
    return Result.success(value)


async def calc_token_value_for_address(
    *, nodes: Nodes, value_expression: str, owner: str, token: str, token_decimals: int, proxies: Proxies
) -> Result[int]:
    var = None
    value_expression = value_expression.lower()
    if "balance" in value_expression:
        res = await spl_token.get_balance_with_retries(5, nodes, proxies, owner=owner, token=token)
        if res.is_error():
            return res
        var = VarInt("balance", res.unwrap())
    value = calc_token_expression(value_expression, token_decimals, var)
    return Result.success(value)
