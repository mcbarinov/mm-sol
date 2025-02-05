import contextlib
import random
from dataclasses import dataclass

import base58
import pydash
from mm_std import Err, Ok, Result
from mnemonic import Mnemonic
from pydantic import BaseModel
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.rpc.responses import GetAccountInfoResp

PHANTOM_DERIVATION_PATH = "m/44'/501'/{i}'/0'"
WORD_STRENGTH = {12: 128, 15: 160, 18: 192, 21: 224, 24: 256}


class NewAccount(BaseModel):
    public_key: str
    private_key_base58: str
    private_key_arr: list[int]


@dataclass
class DerivedAccount:
    index: int
    path: str
    address: str
    private_key: str


def generate_mnemonic(num_words: int = 24) -> str:
    if num_words not in WORD_STRENGTH:
        raise ValueError(f"num_words must be one of {list(WORD_STRENGTH.keys())}")
    mnemonic = Mnemonic("english")
    return mnemonic.generate(strength=WORD_STRENGTH[num_words])


def derive_accounts(mnemonic: str, passphrase: str, derivation_path: str, limit: int) -> list[DerivedAccount]:
    if "{i}" not in derivation_path:
        raise ValueError("derivation_path must contain {i}, for example: m/44'/501'/{i}'/0'")

    result: list[DerivedAccount] = []
    seed = Mnemonic.to_seed(mnemonic, passphrase)
    for i in range(limit):
        path = derivation_path.replace("{i}", str(i))
        keypair = Keypair.from_seed_and_derivation_path(seed, path)
        result.append(
            DerivedAccount(
                index=i,
                path=path,
                address=str(keypair.pubkey()),
                private_key=base58.b58encode(bytes(keypair.to_bytes_array())).decode("utf-8"),
            )
        )

    return result


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


def check_private_key(public_key: str | Pubkey, private_key: str | list[int]) -> bool:
    if isinstance(public_key, str):
        public_key = Pubkey.from_string(public_key)
    return get_keypair(private_key).pubkey() == public_key


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


def is_address(pubkey: str) -> bool:
    with contextlib.suppress(Exception):
        Pubkey.from_string(pubkey)
        return True
    return False
