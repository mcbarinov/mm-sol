import os

import pytest
from dotenv import load_dotenv

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
