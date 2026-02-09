"""Shared CLI utilities: config printing, RPC URL resolution, and helpers."""

import time
from pathlib import Path

from loguru import logger
from mm_web3 import Nodes, Proxies, random_node, random_proxy
from pydantic import BaseModel
from solders.signature import Signature

from mm_sol.utils import get_client


class BaseConfigParams(BaseModel):
    """Base parameters shared by CLI commands that read a config file."""

    config_path: Path
    print_config_and_exit: bool


def public_rpc_url(url: str | None) -> str:
    """Resolve a shorthand network name (mainnet/testnet/devnet) to its full RPC URL."""
    if not url:
        return "https://api.mainnet-beta.solana.com"

    match url.lower():
        case "mainnet":
            return "https://api.mainnet-beta.solana.com"
        case "testnet":
            return "https://api.testnet.solana.com"
        case "devnet":
            return "https://api.devnet.solana.com"

    return url


def wait_confirmation(nodes: Nodes, proxies: Proxies, signature: Signature, log_prefix: str) -> bool:
    """Poll for transaction confirmation, returning True if confirmed within 30 seconds."""
    count = 0
    while True:
        try:
            node = random_node(nodes)
            proxy = random_proxy(proxies)
            client = get_client(node, proxy=proxy)
            res = client.get_transaction(signature)
            if res.value and res.value.slot:  # check for tx error
                return True
        except Exception as e:
            logger.error(f"{log_prefix}: can't get confirmation, error={e}")
        time.sleep(1)
        count += 1
        if count > 30:
            logger.error(f"{log_prefix}: can't get confirmation, timeout")
            return False
