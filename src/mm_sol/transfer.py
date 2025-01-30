from decimal import Decimal

import mm_crypto_utils
import pydash
from mm_crypto_utils import Nodes, Proxies
from mm_std import Err, Ok, Result
from pydantic import BaseModel
from solders.message import Message
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from spl.token.client import Token
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address

import mm_sol.converters
from mm_sol import rpc, utils
from mm_sol.account import check_private_key, get_keypair


def transfer_token(
    *,
    node: str,
    token_mint_address: str | Pubkey,
    from_address: str | Pubkey,
    private_key: str,
    to_address: str | Pubkey,
    amount: Decimal,
    decimals: int,
    proxy: str | None = None,
    timeout: float = 10,
    create_token_account_if_not_exists: bool = True,
) -> Result[Signature]:
    acc = get_keypair(private_key)
    if not check_private_key(from_address, private_key):
        return Err("invalid_private_key")

    from_address = utils.pubkey(from_address)
    token_mint_address = utils.pubkey(token_mint_address)
    to_address = utils.pubkey(to_address)

    client = utils.get_client(node, proxy=proxy, timeout=timeout)
    token_client = Token(conn=client, pubkey=token_mint_address, program_id=TOKEN_PROGRAM_ID, payer=acc)

    recipient_token_account = get_associated_token_address(to_address, token_mint_address, token_program_id=TOKEN_PROGRAM_ID)
    from_token_account = get_associated_token_address(from_address, token_mint_address, token_program_id=TOKEN_PROGRAM_ID)

    data: list[object] = []

    account_info_res = client.get_account_info(recipient_token_account)
    if account_info_res.value is None:
        if create_token_account_if_not_exists:
            create_account_res = token_client.create_account(to_address, skip_confirmation=False)
            data.append(create_account_res)
        else:
            return Err("no_token_account")

    res = token_client.transfer_checked(
        source=from_token_account,
        dest=recipient_token_account,
        owner=from_address,
        amount=mm_sol.converters.sol_to_lamports(amount),
        decimals=decimals,
    )
    data.append(res)

    return Ok(res.value, data=data)


def transfer_token_with_retries(
    *,
    nodes: Nodes,
    token_mint_address: str | Pubkey,
    from_address: str | Pubkey,
    private_key: str,
    to_address: str | Pubkey,
    amount: Decimal,
    decimals: int,
    proxies: Proxies = None,
    timeout: float = 10,
    retries: int = 3,
) -> Result[Signature]:
    res: Result[Signature] = Err("not started yet")
    for _ in range(retries):
        res = transfer_token(
            node=mm_crypto_utils.random_node(nodes),
            token_mint_address=token_mint_address,
            from_address=from_address,
            private_key=private_key,
            to_address=to_address,
            amount=amount,
            decimals=decimals,
            proxy=mm_crypto_utils.random_proxy(proxies),
            timeout=timeout,
        )
        if res.is_ok():
            return res
    return res


def transfer_sol(
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
        return Err("invalid_private_key")

    client = utils.get_client(node, proxy=proxy, timeout=timeout)
    data = None
    try:
        ixs = [transfer(TransferParams(from_pubkey=acc.pubkey(), to_pubkey=Pubkey.from_string(to_address), lamports=lamports))]
        msg = Message(ixs, acc.pubkey())
        tx = Transaction([acc], msg, client.get_latest_blockhash().value.blockhash)
        res = client.send_transaction(tx)
        data = res.to_json()
        return Ok(res.value, data=data)
    except Exception as e:
        return Err(e, data=data)


def transfer_sol_with_retries(
    *,
    nodes: Nodes,
    from_address: str,
    private_key: str,
    to_address: str,
    lamports: int,
    proxies: Proxies = None,
    timeout: float = 10,
    retries: int = 3,
) -> Result[Signature]:
    res: Result[Signature] = Err("not started yet")
    for _ in range(retries):
        res = transfer_sol(
            node=mm_crypto_utils.random_node(nodes),
            from_address=from_address,
            private_key=private_key,
            to_address=to_address,
            lamports=lamports,
            proxy=mm_crypto_utils.random_proxy(proxies),
            timeout=timeout,
        )
        if res.is_ok():
            return res
    return res


class SolTransferInfo(BaseModel):
    source: str
    destination: str
    lamports: int


def find_sol_transfers(node: str, tx_signature: str) -> Result[list[SolTransferInfo]]:
    res = rpc.get_transaction(node, tx_signature, encoding="jsonParsed")
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
        return Ok(result, data=res.data)
    except Exception as e:
        return Err(e, res.data)
