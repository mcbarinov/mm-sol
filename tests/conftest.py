import os

import pydash
import pytest
from dotenv import load_dotenv
from mm_std import fatal, hr

from mm_solana import utils

load_dotenv(".env")


@pytest.fixture
def mainnet_node():
    return os.getenv("MAINNET_NODE")


@pytest.fixture
def testnet_node():
    return os.getenv("TESTNET_NODE")


@pytest.fixture
def usdt_token_address():
    return os.getenv("USDT_TOKEN_ADDRESS")


@pytest.fixture
def usdt_owner_address():
    return os.getenv("USDT_OWNER_ADDRESS")


@pytest.fixture
def binance_wallet():
    return "2ojv9BAiHUrvsm9gxDe7fJSzbNZSJcxZvf8dqmWGHG8S"


@pytest.fixture
def proxy() -> str:
    return os.getenv("PROXY")


@pytest.fixture(scope="session")
def proxies() -> list[str]:
    proxies_url = os.getenv("PROXIES_URL")
    if proxies_url:
        res = hr(proxies_url)
        if res.is_error():
            fatal(f"Can't get proxies: {res.error}")
        proxies = [p.strip() for p in res.body.splitlines() if p.strip()]
        return pydash.uniq(proxies)
    return []


@pytest.fixture
def random_proxy(proxies: list[str]) -> str | None:
    return utils.get_proxy(proxies)
