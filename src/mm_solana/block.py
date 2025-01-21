from mm_std import Err, Ok, Result
from pydantic import BaseModel

from mm_solana.rpc import rpc_call


class BlockTxCount(BaseModel):
    slot: int
    block_time: int | None
    vote_tx_ok: int
    vote_tx_error: int
    non_vote_tx_ok: int
    non_vote_tx_error: int


def calc_block_tx_count(node: str, slot: int, timeout: int = 10, proxy: str | None = None) -> Result[BlockTxCount]:
    res = rpc_call(node=node, method="getBlock", params=[slot], timeout=timeout, proxy=proxy)
    if res.is_err():
        return res
    vote_tx_ok = 0
    vote_tx_error = 0
    non_vote_tx_ok = 0
    non_vote_tx_error = 0
    vote_tx_keys = [
        "SysvarS1otHashes111111111111111111111111111",
        "SysvarC1ock11111111111111111111111111111111",
        "Vote111111111111111111111111111111111111111",
    ]
    try:
        res_ok = res.unwrap()
        txs = res_ok["transactions"]
        block_time = res_ok["blockTime"]
        for tx in txs:
            is_error = tx["meta"]["err"] is not None
            account_keys = tx["transaction"]["message"]["accountKeys"]
            if len(account_keys) == 5 and vote_tx_keys == account_keys[2:]:
                if is_error:
                    vote_tx_error += 1
                else:
                    vote_tx_ok += 1
            elif is_error:
                non_vote_tx_error += 1
            else:
                non_vote_tx_ok += 1

        return Ok(
            BlockTxCount(
                slot=slot,
                vote_tx_ok=vote_tx_ok,
                vote_tx_error=vote_tx_error,
                non_vote_tx_ok=non_vote_tx_ok,
                non_vote_tx_error=non_vote_tx_error,
                block_time=block_time,
            ),
            res.data,
        )
    except Exception as e:
        return Err(e, data=res.data)
