from typing import Any

import pydash
from mm_http import http_request_sync
from mm_result import Result
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_MAINNET_RPC = "https://api.mainnet-beta.solana.com"
DEFAULT_TESTNET_RPC = "https://api.testnet.solana.com"


class EpochInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    epoch: int
    absolute_slot: int = Field(..., alias="absoluteSlot")
    block_height: int = Field(..., alias="blockHeight")
    slot_index: int = Field(..., alias="slotIndex")
    slots_in_epoch: int = Field(..., alias="slotsInEpoch")
    transaction_count: int = Field(..., alias="transactionCount")

    @property
    def progress(self) -> float:
        return round(self.slot_index / self.slots_in_epoch * 100, 2)


class ClusterNode(BaseModel):
    pubkey: str
    version: str | None
    gossip: str | None
    rpc: str | None


class VoteAccount(BaseModel):
    class EpochCredits(BaseModel):
        epoch: int
        credits: int
        previous_credits: int

    validator: str
    vote: str
    commission: int
    stake: int
    credits: list[EpochCredits]
    epoch_vote_account: bool
    root_slot: int
    last_vote: int
    delinquent: bool


class BlockProduction(BaseModel):
    class Leader(BaseModel):
        address: str
        produced: int
        skipped: int

    slot: int
    first_slot: int
    last_slot: int
    leaders: list[Leader]

    @property
    def total_produced(self) -> int:
        return sum(leader.produced for leader in self.leaders)

    @property
    def total_skipped(self) -> int:
        return sum(leader.skipped for leader in self.leaders)


class StakeActivation(BaseModel):
    state: str
    active: int
    inactive: int


def rpc_call(
    *,
    node: str,
    method: str,
    params: list[Any],
    id_: int = 1,
    timeout: float = 5,
    proxy: str | None = None,
) -> Result[Any]:
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": id_}
    if node.startswith("http"):
        return _http_call(node, data, timeout, proxy)
    raise NotImplementedError("ws is not implemented")


def _http_call(node: str, data: dict[str, object], timeout: float, proxy: str | None) -> Result[Any]:
    res = http_request_sync(node, method="POST", proxy=proxy, timeout=timeout, json=data)
    try:
        if res.is_err():
            return res.to_result_err()

        json_body = res.parse_json_body()
        err = pydash.get(json_body, "error.message")
        if err:
            return res.to_result_err(f"service_error: {err}")
        if "result" in json_body:
            return res.to_result_ok(json_body["result"])

        return res.to_result_err("unknown_response")
    except Exception as e:
        return res.to_result_err(e)


def get_balance(node: str, address: str, timeout: float = 5, proxy: str | None = None) -> Result[int]:
    """Returns balance in lamports"""
    return rpc_call(node=node, method="getBalance", params=[address], timeout=timeout, proxy=proxy).map(lambda r: r["value"])


def get_block_height(node: str, timeout: float = 5, proxy: str | None = None) -> Result[int]:
    """Returns balance in lamports"""
    return rpc_call(node=node, method="getBlockHeight", params=[], timeout=timeout, proxy=proxy)


def get_slot(node: str, timeout: float = 5, proxy: str | None = None) -> Result[int]:
    return rpc_call(node=node, method="getSlot", params=[], timeout=timeout, proxy=proxy)


def get_epoch_info(node: str, epoch: int | None = None, timeout: float = 5, proxy: str | None = None) -> Result[EpochInfo]:
    params = [epoch] if epoch else []
    return rpc_call(node=node, method="getEpochInfo", params=params, timeout=timeout, proxy=proxy).map(lambda r: EpochInfo(**r))


def get_health(node: str, timeout: float = 5, proxy: str | None = None) -> Result[bool]:
    return rpc_call(node=node, method="getHealth", params=[], timeout=timeout, proxy=proxy).map(lambda r: r == "ok")


def get_cluster_nodes(node: str, timeout: float = 5, proxy: str | None = None) -> Result[list[ClusterNode]]:
    return rpc_call(node=node, method="getClusterNodes", timeout=timeout, proxy=proxy, params=[]).map(
        lambda r: [ClusterNode(**n) for n in r],
    )


def get_vote_accounts(node: str, timeout: float = 5, proxy: str | None = None) -> Result[list[VoteAccount]]:
    res = rpc_call(node=node, method="getVoteAccounts", timeout=timeout, proxy=proxy, params=[])
    if res.is_err():
        return res
    try:
        data = res.unwrap()
        result: list[VoteAccount] = []
        for a in data["current"]:
            result.append(  # noqa: PERF401
                VoteAccount(
                    validator=a["nodePubkey"],
                    vote=a["votePubkey"],
                    commission=a["commission"],
                    stake=a["activatedStake"],
                    credits=[
                        VoteAccount.EpochCredits(epoch=c[0], credits=c[1], previous_credits=c[2]) for c in a["epochCredits"]
                    ],
                    delinquent=False,
                    epoch_vote_account=a["epochVoteAccount"],
                    root_slot=a["rootSlot"],
                    last_vote=a["lastVote"],
                ),
            )
        for a in data["delinquent"]:
            result.append(  # noqa: PERF401
                VoteAccount(
                    validator=a["nodePubkey"],
                    vote=a["votePubkey"],
                    commission=a["commission"],
                    stake=a["activatedStake"],
                    credits=[
                        VoteAccount.EpochCredits(epoch=c[0], credits=c[1], previous_credits=c[2]) for c in a["epochCredits"]
                    ],
                    delinquent=True,
                    epoch_vote_account=a["epochVoteAccount"],
                    root_slot=a["rootSlot"],
                    last_vote=a["lastVote"],
                ),
            )
        return res.with_value(result)
    except Exception as e:
        return res.with_error(e)


def get_leader_scheduler(
    node: str,
    slot: int | None = None,
    timeout: float = 5,
    proxy: str | None = None,
) -> Result[dict[str, list[int]]]:
    return rpc_call(
        node=node,
        method="getLeaderSchedule",
        timeout=timeout,
        proxy=proxy,
        params=[slot],
    )


def get_stake_activation(node: str, address: str, timeout: float = 60, proxy: str | None = None) -> Result[StakeActivation]:
    return rpc_call(node=node, method="getStakeActivation", timeout=timeout, proxy=proxy, params=[address]).map(
        lambda ok: StakeActivation(**ok),
    )


def get_transaction(
    node: str,
    signature: str,
    max_supported_transaction_version: int | None = None,
    encoding: str = "json",
    timeout: float = 5,
    proxy: str | None = None,
) -> Result[dict[str, object] | None]:
    if max_supported_transaction_version is not None:
        params = [signature, {"maxSupportedTransactionVersion": max_supported_transaction_version, "encoding": encoding}]
    else:
        params = [signature, encoding]
    return rpc_call(node=node, method="getTransaction", timeout=timeout, proxy=proxy, params=params)
