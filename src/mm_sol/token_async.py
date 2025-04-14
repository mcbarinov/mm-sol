import httpx
from mm_std import DataResult
from solana.exceptions import SolanaRpcException
from solana.rpc.core import RPCException
from solders.solders import InvalidParamsMessage, Pubkey, get_associated_token_address

from mm_sol.utils import get_async_client


async def get_token_balance(
    node: str,
    owner_address: str,
    token_mint_address: str,
    token_account: str | None = None,
    timeout: float = 10,
    proxy: str | None = None,
) -> DataResult[int]:
    try:
        client = get_async_client(node, proxy=proxy, timeout=timeout)
        if not token_account:
            token_account = str(
                get_associated_token_address(Pubkey.from_string(owner_address), Pubkey.from_string(token_mint_address))
            )

        res = await client.get_token_account_balance(Pubkey.from_string(token_account))

        # Sometimes it not raise an error, but it returns this :(
        if isinstance(res, InvalidParamsMessage) and "could not find account" in res.message:
            return DataResult(ok=0, data=res.to_json())
        return DataResult(ok=int(res.value.amount), data=res.to_json())
    except RPCException as e:
        if "could not find account" in str(e):
            return DataResult(ok=0, data={"rpc_exception": str(e)})
        return DataResult(err="error", data={"rpc_exception": str(e)})
    except httpx.HTTPStatusError as e:
        return DataResult(err=f"http error: {e}")
    except SolanaRpcException as e:
        return DataResult(err=e.error_msg)
    except Exception as e:
        return DataResult(err="exception", data={"exception": str(e)})
