import os

import mm_web3
import pytest
from dotenv import load_dotenv
from mm_web3 import fetch_proxies_sync
from typer.testing import CliRunner

load_dotenv()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def devnet_address_1() -> str:
    value = os.getenv("DEVNET_ADDRESS_1")
    if value is None:
        pytest.skip("DEVNET_ADDRESS_1 environment variable not set")
    return value


@pytest.fixture
def devnet_address_2() -> str:
    value = os.getenv("DEVNET_ADDRESS_2")
    if value is None:
        pytest.skip("DEVNET_ADDRESS_2 environment variable not set")
    return value


@pytest.fixture
def devnet_address_3() -> str:
    value = os.getenv("DEVNET_ADDRESS_3")
    if value is None:
        pytest.skip("DEVNET_ADDRESS_3 environment variable not set")
    return value


@pytest.fixture
def devnet_private_1() -> str:
    value = os.getenv("DEVNET_PRIVATE_1")
    if value is None:
        pytest.skip("DEVNET_PRIVATE_1 environment variable not set")
    return value


@pytest.fixture
def devnet_private_2() -> str:
    value = os.getenv("DEVNET_PRIVATE_2")
    if value is None:
        pytest.skip("DEVNET_PRIVATE_2 environment variable not set")
    return value


@pytest.fixture
def devnet_private_3() -> str:
    value = os.getenv("DEVNET_PRIVATE_3")
    if value is None:
        pytest.skip("DEVNET_PRIVATE_3 environment variable not set")
    return value


@pytest.fixture
def mainnet_node() -> str:
    value = os.getenv("MAINNET_NODE")
    if value is None:
        pytest.skip("MAINNET_NODE environment variable not set")
    return value


@pytest.fixture
def testnet_node() -> str:
    value = os.getenv("TESTNET_NODE")
    if value is None:
        pytest.skip("TESTNET_NODE environment variable not set")
    return value


@pytest.fixture
def usdt_token_address() -> str:
    value = os.getenv("USDT_TOKEN_ADDRESS")
    if value is None:
        pytest.skip("USDT_TOKEN_ADDRESS environment variable not set")
    return value


@pytest.fixture
def usdt_owner_address() -> str:
    value = os.getenv("USDT_OWNER_ADDRESS")
    if value is None:
        pytest.skip("USDT_OWNER_ADDRESS environment variable not set")
    return value


@pytest.fixture
def binance_wallet():
    return "2ojv9BAiHUrvsm9gxDe7fJSzbNZSJcxZvf8dqmWGHG8S"


@pytest.fixture(scope="session")
def proxies() -> list[str]:
    proxies_url = os.getenv("PROXIES_URL")
    if proxies_url:
        return fetch_proxies_sync(proxies_url).unwrap("Failed to fetch proxies from URL")
    return []


@pytest.fixture
def random_proxy(proxies) -> str | None:
    return mm_web3.random_proxy(proxies)


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()
