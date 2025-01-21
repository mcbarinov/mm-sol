import json
import random
from decimal import Decimal
from pathlib import Path
from typing import Literal

import pydash
from mm_std import CommandResult, Err, Ok, Result, run_command, run_ssh_command
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ValidatorInfo(BaseModel):
    identity_address: str
    info_address: str
    name: str | None
    keybase: str | None
    website: str | None
    details: str | None


class StakeAccount(BaseModel):
    type: str = Field(..., alias="stakeType")
    balance: float | None = Field(..., alias="accountBalance")
    withdrawer: str
    staker: str
    vote: str | None = Field(None, alias="delegatedVoteAccountAddress")

    @field_validator("balance")
    @classmethod
    def from_lamports_to_sol(cls, v: int | None) -> float | None:
        if v:
            return v / 1_000_000_000


class Stake(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    stake_address: str = Field(..., alias="stakePubkey")
    withdrawer_address: str = Field(..., alias="withdrawer")
    vote_address: str | None = Field(None, alias="delegatedVoteAccountAddress")
    balance: float | None = Field(..., alias="accountBalance")
    delegated: float | None = Field(None, alias="delegatedStake")
    active: float | None = Field(None, alias="activeStake")
    lock_time: int | None = Field(None, alias="unixTimestamp")

    @field_validator("balance", "delegated", "active")
    @classmethod
    def from_lamports_to_sol(cls, v: int | None) -> float | None:
        if v:
            return v / 1_000_000_000


def get_balance(
    *,
    address: str,
    solana_dir: str = "",
    url: str = "localhost",
    ssh_host: str | None = None,
    ssh_key_path: str | None = None,
    timeout: int = 60,
) -> Result[Decimal]:
    solana_dir = _solana_dir(solana_dir)
    cmd = f"{solana_dir}solana balance {address} -u {url}"
    res = _exec_cmd(cmd, ssh_host, ssh_key_path, timeout)
    data = {"cmd": cmd, "stdout": res.stdout, "stderr": res.stderr}
    try:
        return Ok(Decimal(res.stdout.replace("SOL", "").strip()), data=data)
    except Exception as e:
        return Err(e, data=data)


def get_stake_account(
    *,
    address: str,
    solana_dir: str = "",
    url: str = "localhost",
    ssh_host: str | None = None,
    ssh_key_path: str | None = None,
    timeout: int = 60,
) -> Result[StakeAccount]:
    solana_dir = _solana_dir(solana_dir)
    cmd = f"{solana_dir}solana stake-account --output json -u {url} {address}"
    res = _exec_cmd(cmd, ssh_host, ssh_key_path, timeout)
    data = {"cmd": cmd, "stdout": res.stdout, "stderr": res.stderr}
    try:
        json_res = json.loads(res.stdout)
        return Ok(StakeAccount(**json_res), data=data)
    except Exception as e:
        return Err(e, data=data)


def transfer_with_private_key_file(
    *,
    recipient: str,
    amount: Decimal,
    private_key_path: str,
    solana_dir: str = "",
    url: str = "localhost",
    ssh_host: str | None = None,
    ssh_key_path: str | None = None,
    allow_unfunded_recipient: bool = True,
    timeout: int = 60,
) -> Result[str]:
    solana_dir = _solana_dir(solana_dir)
    cmd = f"{solana_dir}solana transfer {recipient} {amount} --from {private_key_path} --fee-payer {private_key_path}"
    if allow_unfunded_recipient:
        cmd += " --allow-unfunded-recipient"
    cmd += f" -u {url} --output json"
    res = _exec_cmd(cmd, ssh_host, ssh_key_path, timeout)
    data = {"cmd": cmd, "stdout": res.stdout, "stderr": res.stderr}
    try:
        json_res = json.loads(res.stdout)
        return Ok(json_res["signature"], data=data)
    except Exception as e:
        return Err(e, data=data)


def transfer_with_private_key_str(
    *,
    recipient: str,
    amount: Decimal,
    private_key: str,
    tmp_dir_path: str,
    solana_dir: str = "",
    url: str = "localhost",
    ssh_host: str | None = None,
    ssh_key_path: str | None = None,
    timeout: int = 60,
) -> Result[str]:
    # make private_key file
    private_key_path = Path(f"{tmp_dir_path}/solana__{random.randint(1, 10_000_000_000)}.json")
    private_key_path.write_text(private_key)

    try:
        return transfer_with_private_key_file(
            recipient=recipient,
            amount=amount,
            private_key_path=private_key_path.as_posix(),
            solana_dir=solana_dir,
            url=url,
            ssh_host=ssh_host,
            ssh_key_path=ssh_key_path,
            timeout=timeout,
        )
    finally:
        private_key_path.unlink()


def withdraw_from_vote_account(
    *,
    recipient: str,
    amount: Decimal | Literal["ALL"],
    vote_key_path: str,
    fee_payer_key_path: str,
    solana_dir: str = "",
    url: str = "localhost",
    ssh_host: str | None = None,
    ssh_key_path: str | None = None,
    timeout: int = 60,
) -> Result[str]:
    solana_dir = _solana_dir(solana_dir)
    cmd = f"{solana_dir}solana withdraw-from-vote-account --keypair {fee_payer_key_path} -u {url} --output json {vote_key_path} {recipient} {amount}"  # noqa: E501
    res = _exec_cmd(cmd, ssh_host, ssh_key_path, timeout)
    data = {"cmd": cmd, "stdout": res.stdout, "stderr": res.stderr}
    try:
        json_res = json.loads(res.stdout)
        return Ok(json_res["signature"], data=data)
    except Exception as e:
        return Err(e, data=data)


def get_validators_info(
    *,
    solana_dir: str = "",
    url: str = "localhost",
    ssh_host: str | None = None,
    ssh_key_path: str | None = None,
    timeout: int = 60,
) -> Result[list[ValidatorInfo]]:
    solana_dir = _solana_dir(solana_dir)
    cmd = f"{solana_dir}solana validator-info get --output json -u {url}"
    res = _exec_cmd(cmd, ssh_host, ssh_key_path, timeout)
    data = {"cmd": cmd, "stdout": res.stdout, "stderr": res.stderr}
    try:
        validators = []
        for v in json.loads(res.stdout):
            validators.append(  # noqa: PERF401
                ValidatorInfo(
                    info_address=v["infoPubkey"],
                    identity_address=v["identityPubkey"],
                    name=pydash.get(v, "info.name"),
                    keybase=pydash.get(v, "info.keybaseUsername"),
                    details=pydash.get(v, "info.details"),
                    website=pydash.get(v, "info.website"),
                ),
            )
        return Ok(validators, data=data)
    except Exception as e:
        return Err(e, data=data)


def get_vote_account_rewards(
    *,
    address: str,
    solana_dir: str = "",
    url: str = "localhost",
    ssh_host: str | None = None,
    ssh_key_path: str | None = None,
    num_rewards_epochs: int = 10,
    timeout: int = 60,
) -> Result[dict[int, float]]:
    solana_dir = _solana_dir(solana_dir)
    cmd = f"{solana_dir}solana vote-account {address} --with-rewards --num-rewards-epochs={num_rewards_epochs} -u {url}"
    cmd += " --output json 2>/dev/null"
    res = _exec_cmd(cmd, ssh_host, ssh_key_path, timeout)
    data = {"cmd": cmd, "stdout": res.stdout, "stderr": res.stderr}
    try:
        rewards: dict[int, float] = {}
        for r in reversed(json.loads(res.stdout)["epochRewards"]):
            rewards[r["epoch"]] = r["amount"] / 10**9
        return Ok(rewards, data=data)
    except Exception as e:
        return Err(e, data=data)


def get_stakes(
    *,
    vote_address: str = "",
    solana_dir: str = "",
    url: str = "localhost",
    ssh_host: str | None = None,
    ssh_key_path: str | None = None,
    timeout: int = 60,
) -> Result[list[Stake]]:
    solana_dir = _solana_dir(solana_dir)
    cmd = f"{solana_dir}solana stakes --output json -u {url} {vote_address}"
    res = _exec_cmd(cmd, ssh_host, ssh_key_path, timeout)
    data = {"stdout": res.stdout, "stderr": res.stderr}
    try:
        return Ok([Stake(**x) for x in json.loads(res.stdout)], data=data)
    except Exception as e:
        return Err(e, data=data)


def _exec_cmd(cmd: str, ssh_host: str | None, ssh_key_path: str | None, timeout: int) -> CommandResult:
    if ssh_host:
        return run_ssh_command(ssh_host, cmd, ssh_key_path, timeout=timeout)
    return run_command(cmd, timeout=timeout)


def _solana_dir(solana_dir: str) -> str:
    if solana_dir and not solana_dir.endswith("/"):
        solana_dir += "/"
    return solana_dir
