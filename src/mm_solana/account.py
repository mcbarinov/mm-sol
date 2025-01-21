import random
from typing import TYPE_CHECKING

import base58
import pydash
from mm_std import Err, Ok, Result
from pydantic import BaseModel
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey

if TYPE_CHECKING:
    from solders.rpc.responses import GetAccountInfoResp


class NewAccount(BaseModel):
    public_key: str
    private_key_base58: str
    private_key_arr: list[int]


def generate_account() -> NewAccount:
    keypair = Keypair()
    public_key = str(keypair.pubkey())
    private_key_base58 = base58.b58encode(bytes(keypair.to_bytes_array())).decode("utf-8")
    private_key_arr = list(keypair.to_bytes_array())
    return NewAccount(public_key=public_key, private_key_base58=private_key_base58, private_key_arr=private_key_arr)


def get_keypair(private_key: str | list[int]) -> Keypair:
    if isinstance(private_key, str):
        if "[" in private_key:
            private_key_ = [int(x) for x in private_key.replace("[", "").replace("]", "").split(",")]
        else:
            private_key_ = base58.b58decode(private_key)  # type: ignore[assignment]
    else:
        private_key_ = private_key
    return Keypair.from_bytes(private_key_)


def check_private_key(public_key_base58: str, private_key: str | list[int]) -> bool:
    return str(get_keypair(private_key).pubkey()) == public_key_base58


def get_public_key(private_key: str) -> str:
    if "[" in private_key:
        private_key_ = [int(x) for x in private_key.replace("[", "").replace("]", "").split(",")]
    else:
        private_key_ = base58.b58decode(private_key)  # type: ignore[assignment]
    return str(Keypair.from_bytes(private_key_).pubkey())


def get_private_key_base58(private_key: str) -> str:
    keypair = get_keypair(private_key)
    return base58.b58encode(bytes(keypair.to_bytes_array())).decode("utf-8")


def get_private_key_arr(private_key: str) -> list[int]:
    keypair = get_keypair(private_key)
    return list(x for x in keypair.to_bytes_array())  # noqa: C400


def get_private_key_arr_str(private_key: str) -> str:
    return f"[{','.join(str(x) for x in get_private_key_arr(private_key))}]"


def is_empty_account(*, address: str, node: str | None = None, nodes: list[str] | None = None, attempts: int = 3) -> Result[bool]:
    if not node and not nodes:
        raise ValueError("node or nodes must be set")
    error = None
    data = None
    for _ in range(attempts):
        try:
            client = Client(node or random.choice(nodes))  # type: ignore[arg-type]
            res: GetAccountInfoResp = client.get_account_info(Pubkey.from_string(address))
            data = res
            slot = pydash.get(res, "result.context.slot")
            value = pydash.get(res, "result.value")
            if slot and value is None:
                return Ok(True, data=data)
            if slot and value:
                return Ok(False, data=data)
        except Exception as e:
            error = str(e)
    return Err(error or "unknown response", data=data)


def is_valid_pubkey(pubkey: str) -> bool:
    try:
        Pubkey.from_string(pubkey)
        return True  # noqa: TRY300
    except Exception:
        return False
