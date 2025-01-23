import sys

import pydash
from mm_std import BaseConfig, fatal, hr, print_json


def print_config_and_exit(exit_: bool, config: BaseConfig, exclude: set[str] | None = None) -> None:
    if exit_:
        print_json(config.model_dump(exclude=exclude))
        sys.exit(0)


def public_rpc_url(url: str | None) -> str:
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


def load_proxies_from_url(proxies_url: str) -> list[str]:
    try:
        res = hr(proxies_url)
        if res.is_error():
            fatal(f"Can't get proxies: {res.error}")
        proxies = [p.strip() for p in res.body.splitlines() if p.strip()]
        return pydash.uniq(proxies)
    except Exception as err:
        fatal(f"Can't get  proxies from the url: {err}")
