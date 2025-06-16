from mm_result import Result
from mm_web3 import Nodes, Proxies
from mm_web3.calcs import calc_expression_with_vars

from mm_sol import retry
from mm_sol.constants import UNIT_DECIMALS


def calc_sol_expression(expression: str, variables: dict[str, int] | None = None) -> int:
    return calc_expression_with_vars(expression, variables, unit_decimals=UNIT_DECIMALS)


def calc_token_expression(expression: str, token_decimals: int, variables: dict[str, int] | None = None) -> int:
    return calc_expression_with_vars(expression, variables, unit_decimals={"t": token_decimals})


async def calc_sol_value_for_address(
    *, nodes: Nodes, value_expression: str, address: str, proxies: Proxies, fee: int
) -> Result[int]:
    value_expression = value_expression.lower()
    variables: dict[str, int] | None = None
    if "balance" in value_expression:
        res = await retry.get_sol_balance(5, nodes, proxies, address=address)
        if res.is_err():
            return res
        variables = {"balance": res.unwrap()}

    value = calc_sol_expression(value_expression, variables)
    if "balance" in value_expression:
        value = value - fee
    return Result.ok(value)


async def calc_token_value_for_address(
    *, nodes: Nodes, value_expression: str, owner: str, token: str, token_decimals: int, proxies: Proxies
) -> Result[int]:
    variables: dict[str, int] | None = None
    value_expression = value_expression.lower()
    if "balance" in value_expression:
        res = await retry.get_token_balance(5, nodes, proxies, owner=owner, token=token)
        if res.is_err():
            return res
        variables = {"balance": res.unwrap()}
    value = calc_token_expression(value_expression, token_decimals, variables)
    return Result.ok(value)
