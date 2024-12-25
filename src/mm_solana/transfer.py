from decimal import Decimal

import pydash
from mm_std import Err, Ok, Result
from pydantic import BaseModel
from solana.rpc.api import Client
from solders.message import Message
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction

from mm_solana import rpc, utils
from mm_solana.account import check_private_key, get_keypair


def transfer_sol(
    *,
    from_address: str,
    private_key_base58: str,
    recipient_address: str,
    amount_sol: Decimal,
    nodes: str | list[str] | None = None,
    attempts: int = 3,
) -> Result[str]:
    acc = get_keypair(private_key_base58)
    if not check_private_key(from_address, private_key_base58):
        raise ValueError("from_address or private_key_base58 is invalid")

    lamports = int(amount_sol * 10**9)
    error = None
    data = None
    for _ in range(attempts):
        try:
            client = Client(utils.get_node(nodes))
            # tx = Transaction(from_keypairs=[acc])
            # ti = transfer(
            #     TransferParams(from_pubkey=acc.pubkey(), to_pubkey=Pubkey.from_string(recipient_address), lamports=lamports),
            # )
            # tx.add(ti)
            # res = client.send_legacy_transaction(tx, acc)
            ixns = [
                transfer(
                    TransferParams(from_pubkey=acc.pubkey(), to_pubkey=Pubkey.from_string(recipient_address), lamports=lamports)
                )
            ]
            msg = Message(ixns, acc.pubkey())
            tx = Transaction([acc], msg, client.get_latest_blockhash().value.blockhash)
            res = client.send_transaction(tx)
            data = res.to_json()
            return Ok(str(res.value), data=data)
        except Exception as e:
            error = e

    return Err(error or "unknown", data=data)


class TransferInfo(BaseModel):
    source: str
    destination: str
    lamports: int


def find_transfers(node: str, tx_signature: str) -> Result[list[TransferInfo]]:
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
                    result.append(TransferInfo(source=source, destination=destination, lamports=lamports))
        return Ok(result, data=res.data)
    except Exception as e:
        return Err(e, res.data)
