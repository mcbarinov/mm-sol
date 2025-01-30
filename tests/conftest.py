import os

import mm_crypto_utils
import pytest
from dotenv import load_dotenv
from typer.testing import CliRunner

load_dotenv(".env")


@pytest.fixture
def devnet_address_1() -> str:
    return os.getenv("DEVNET_ADDRESS_1")


@pytest.fixture
def devnet_address_2() -> str:
    return os.getenv("DEVNET_ADDRESS_2")


@pytest.fixture
def devnet_address_3() -> str:
    return os.getenv("DEVNET_ADDRESS_3")


@pytest.fixture
def devnet_private_1() -> str:
    return os.getenv("DEVNET_PRIVATE_1")


@pytest.fixture
def devnet_private_2() -> str:
    return os.getenv("DEVNET_PRIVATE_2")


@pytest.fixture
def devnet_private_3() -> str:
    return os.getenv("DEVNET_PRIVATE_3")


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
        return mm_crypto_utils.fetch_proxies_or_fatal(proxies_url)
    return []


@pytest.fixture
def random_proxy(proxies) -> str | None:
    return mm_crypto_utils.random_proxy(proxies)


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()
