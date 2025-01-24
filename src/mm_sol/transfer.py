from decimal import Decimal

import pydash
from mm_std import Err, Ok, Result
from pydantic import BaseModel
from solders.message import Message
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction

from mm_sol import rpc, utils
from mm_sol.account import check_private_key, get_keypair
from mm_sol.types import Nodes, Proxies


def transfer_sol(
    *,
    node: str,
    from_address: str,
    private_key: str,
    to_address: str,
    value: Decimal,
    proxy: str | None = None,
    timeout: float = 10,
) -> Result[str]:
    acc = get_keypair(private_key)
    if not check_private_key(from_address, private_key):
        return Err("invalid_private_key")

    client = utils.get_client(node, proxy=proxy, timeout=timeout)
    data = None
    lamports = int(value * 10**9)
    try:
        ixns = [transfer(TransferParams(from_pubkey=acc.pubkey(), to_pubkey=Pubkey.from_string(to_address), lamports=lamports))]
        msg = Message(ixns, acc.pubkey())
        tx = Transaction([acc], msg, client.get_latest_blockhash().value.blockhash)
        res = client.send_transaction(tx)
        data = res.to_json()
        return Ok(str(res.value), data=data)
    except Exception as e:
        return Err(e, data=data)


def transfer_sol_with_retries(
    *,
    nodes: Nodes,
    from_address: str,
    private_key: str,
    to_address: str,
    value: Decimal,
    proxies: Proxies = None,
    timeout: float = 10,
    retries: int = 3,
) -> Result[str]:
    res: Result[str] = Err("not started yet")
    for _ in range(retries):
        res = transfer_sol(
            node=utils.get_node(nodes),
            from_address=from_address,
            private_key=private_key,
            to_address=to_address,
            value=value,
            proxy=utils.get_proxy(proxies),
            timeout=timeout,
        )
        if res.is_ok():
            return res
    return res


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
