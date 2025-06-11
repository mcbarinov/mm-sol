import pydash
from mm_result import Result
from pydantic import BaseModel
from solders.message import Message
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address

from mm_sol import rpc_sync, utils
from mm_sol.account import check_private_key, get_keypair


async def transfer_token(
    *,
    node: str,
    token_mint_address: str | Pubkey,
    from_address: str | Pubkey,
    private_key: str,
    to_address: str | Pubkey,
    amount: int,  # smallest unit
    decimals: int,
    proxy: str | None = None,
    timeout: float = 10,
    create_token_account_if_not_exists: bool = True,
) -> Result[Signature]:
    # TODO: try/except this function!!!
    acc = get_keypair(private_key)
    if not check_private_key(from_address, private_key):
        return Result.err("invalid_private_key")

    from_address = utils.pubkey(from_address)
    token_mint_address = utils.pubkey(token_mint_address)
    to_address = utils.pubkey(to_address)

    client = utils.get_async_client(node, proxy=proxy, timeout=timeout)
    token_client = AsyncToken(conn=client, pubkey=token_mint_address, program_id=TOKEN_PROGRAM_ID, payer=acc)

    recipient_token_account = get_associated_token_address(to_address, token_mint_address, token_program_id=TOKEN_PROGRAM_ID)
    from_token_account = get_associated_token_address(from_address, token_mint_address, token_program_id=TOKEN_PROGRAM_ID)
    logs: list[object] = []

    account_info_res = await client.get_account_info(recipient_token_account)
    if account_info_res.value is None:
        if create_token_account_if_not_exists:
            create_account_res = token_client.create_associated_token_account(to_address, skip_confirmation=False)
            logs.append(create_account_res)
        else:
            return Result.err("no_token_account")

    res = await token_client.transfer_checked(
        source=from_token_account,
        dest=recipient_token_account,
        owner=from_address,
        amount=amount,
        decimals=decimals,
        multi_signers=None,
    )
    logs.append(res)

    return Result.ok(res.value, {"logs": logs})


async def transfer_sol(
    *,
    node: str,
    from_address: str,
    private_key: str,
    to_address: str,
    lamports: int,
    proxy: str | None = None,
    timeout: float = 10,
) -> Result[Signature]:
    acc = get_keypair(private_key)
    if not check_private_key(from_address, private_key):
        return Result.err("invalid_private_key")

    client = utils.get_async_client(node, proxy=proxy, timeout=timeout)
    data = None
    try:
        ixs = [transfer(TransferParams(from_pubkey=acc.pubkey(), to_pubkey=Pubkey.from_string(to_address), lamports=lamports))]
        msg = Message(ixs, acc.pubkey())
        blockhash = await client.get_latest_blockhash()
        tx = Transaction([acc], msg, blockhash.value.blockhash)
        res = await client.send_transaction(tx)
        data = res.to_json()
        return Result.ok(res.value, {"response": data})
    except Exception as e:
        return Result.err(e, {"response": data})


class SolTransferInfo(BaseModel):
    source: str
    destination: str
    lamports: int


def find_sol_transfers(node: str, tx_signature: str) -> Result[list[SolTransferInfo]]:
    res = rpc_sync.get_transaction(node, tx_signature, encoding="jsonParsed")
    if res.is_err():
        return res  # type: ignore[return-value]
    result = []
    try:
        for ix in pydash.get(res.ok, "transaction.message.instructions"):
            program_id = ix.get("programId")
            ix_type = pydash.get(ix, "parsed.type")
            if program_id == "11111111111111111111111111111111" and ix_type == "transfer":
                source = pydash.get(ix, "parsed.info.source")
                destination = pydash.get(ix, "parsed.info.destination")
                lamports = pydash.get(ix, "parsed.info.lamports")
                if source and destination and lamports:
                    result.append(SolTransferInfo(source=source, destination=destination, lamports=lamports))
        return res.with_value(result)
    except Exception as e:
        return Result.err(e, res.extra)
