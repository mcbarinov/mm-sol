from mm_result import Result
from solana.exceptions import SolanaRpcException
from solana.rpc.core import RPCException
from solders.solders import InvalidParamsMessage, Pubkey, get_associated_token_address

from mm_sol.utils import get_async_client


async def get_balance(
    node: str,
    owner: str,
    token: str,
    token_account: str | None = None,
    timeout: float = 5,
    proxy: str | None = None,
) -> Result[int]:
    response = None
    try:
        client = get_async_client(node, proxy=proxy, timeout=timeout)
        if not token_account:
            token_account = str(get_associated_token_address(Pubkey.from_string(owner), Pubkey.from_string(token)))

        res = await client.get_token_account_balance(Pubkey.from_string(token_account))
        response = res.to_json()

        # Sometimes it not raise an error, but it returns this :(
        if isinstance(res, InvalidParamsMessage) and "could not find account" in res.message:
            return Result.ok(0, {"response": response})
        return Result.ok(int(res.value.amount), {"response": response})
    except RPCException as e:
        if "could not find account" in str(e):
            return Result.ok(0, {"response": response, "rpc_exception": str(e)})
        return Result.err(e, {"response": response})
    except SolanaRpcException as e:
        return Result.err((e.error_msg, e), {"response": response})
    except Exception as e:
        return Result.err(e, {"response": response})


async def get_decimals(node: str, token: str, timeout: float = 5, proxy: str | None = None) -> Result[int]:
    response = None
    try:
        client = get_async_client(node, proxy=proxy, timeout=timeout)
        res = await client.get_token_supply(Pubkey.from_string(token))
        response = res.to_json()
        return Result.ok(res.value.decimals, {"response": response})
    except Exception as e:
        return Result.err(e, {"response": response})
