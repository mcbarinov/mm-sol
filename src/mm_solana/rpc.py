from typing import Any

from mm_std import Err, Ok, Result, hr
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
    timeout: int = 10,
    proxy: str | None = None,
) -> Result[Any]:
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": id_}
    if node.startswith("http"):
        return _http_call(node, data, timeout, proxy)
    raise NotImplementedError("ws is not implemented")


def _http_call(node: str, data: dict[str, object], timeout: int, proxy: str | None) -> Result[Any]:
    res = hr(node, method="POST", proxy=proxy, timeout=timeout, params=data, json_params=True)
    try:
        if res.is_error():
            return res.to_err_result()

        err = res.json.get("error", {}).get("message", "")
        if err:
            return res.to_err_result(f"service_error: {err}")
        if "result" in res.json:
            return res.to_ok_result(res.json["result"])

        return res.to_err_result("unknown_response")
    except Exception as e:
        return res.to_err_result(f"exception: {e!s}")


def get_balance(node: str, address: str, timeout: int = 10, proxy: str | None = None) -> Result[int]:
    """Returns balance in lamports"""
    return rpc_call(node=node, method="getBalance", params=[address], timeout=timeout, proxy=proxy).and_then(lambda r: r["value"])


def get_block_height(node: str, timeout: int = 10, proxy: str | None = None) -> Result[int]:
    """Returns balance in lamports"""
    return rpc_call(node=node, method="getBlockHeight", params=[], timeout=timeout, proxy=proxy)


def get_slot(node: str, timeout: int = 10, proxy: str | None = None) -> Result[int]:
    return rpc_call(node=node, method="getSlot", params=[], timeout=timeout, proxy=proxy)


def get_epoch_info(node: str, epoch: int | None = None, timeout: int = 10, proxy: str | None = None) -> Result[EpochInfo]:
    params = [epoch] if epoch else []
    return rpc_call(node=node, method="getEpochInfo", params=params, timeout=timeout, proxy=proxy).and_then(
        lambda r: EpochInfo(**r),
    )


def get_health(node: str, timeout: int = 10, proxy: str | None = None) -> Result[bool]:
    return rpc_call(node=node, method="getHealth", params=[], timeout=timeout, proxy=proxy).and_then(lambda r: r == "ok")


def get_cluster_nodes(node: str, timeout: int = 30, proxy: str | None = None) -> Result[list[ClusterNode]]:
    return rpc_call(node=node, method="getClusterNodes", timeout=timeout, proxy=proxy, params=[]).and_then(
        lambda r: [ClusterNode(**n) for n in r],
    )


def get_vote_accounts(node: str, timeout: int = 30, proxy: str | None = None) -> Result[list[VoteAccount]]:
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
        return Ok(result, res.data)
    except Exception as e:
        return Err(e, res.data)


def get_leader_scheduler(
    node: str,
    slot: int | None = None,
    timeout: int = 10,
    proxy: str | None = None,
) -> Result[dict[str, list[int]]]:
    return rpc_call(
        node=node,
        method="getLeaderSchedule",
        timeout=timeout,
        proxy=proxy,
        params=[slot],
    )


def get_block_production(node: str, timeout: int = 60, proxy: str | None = None) -> Result[BlockProduction]:
    res = rpc_call(node=node, method="getBlockProduction", timeout=timeout, proxy=proxy, params=[])
    if res.is_err():
        return res
    try:
        res_ok = res.unwrap()
        slot = res_ok["context"]["slot"]
        first_slot = res_ok["value"]["range"]["firstSlot"]
        last_slot = res_ok["value"]["range"]["lastSlot"]
        leaders = []
        for address, (leader, produced) in res.ok["value"]["byIdentity"].items():  # type: ignore[index]
            leaders.append(BlockProduction.Leader(address=address, produced=produced, skipped=leader - produced))
        return Ok(BlockProduction(slot=slot, first_slot=first_slot, last_slot=last_slot, leaders=leaders), res.data)
    except Exception as e:
        return Err(e, data=res.data)


def get_stake_activation(node: str, address: str, timeout: int = 60, proxy: str | None = None) -> Result[StakeActivation]:
    return rpc_call(node=node, method="getStakeActivation", timeout=timeout, proxy=proxy, params=[address]).and_then(
        lambda ok: StakeActivation(**ok),
    )


def get_transaction(
    node: str,
    signature: str,
    max_supported_transaction_version: int | None = None,
    encoding: str = "json",
    timeout: int = 60,
    proxy: str | None = None,
) -> Result[dict[str, object] | None]:
    if max_supported_transaction_version is not None:
        params = [signature, {"maxSupportedTransactionVersion": max_supported_transaction_version, "encoding": encoding}]
    else:
        params = [signature, encoding]
    return rpc_call(node=node, method="getTransaction", timeout=timeout, proxy=proxy, params=params)
