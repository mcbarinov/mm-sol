import importlib.metadata

from mm_crypto_utils import Proxies
from rich.live import Live
from rich.table import Table

from mm_sol.balance import get_sol_balance_with_retries
from mm_sol.converters import lamports_to_sol


def get_version() -> str:
    return importlib.metadata.version("mm-sol")


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


def print_balances(
    rpc_nodes: list[str],
    addresses: list[str],
    *,
    proxies: Proxies = None,
    round_ndigits: int = 5,
) -> None:
    table = Table(title="balances")
    table.add_column("n")
    table.add_column("address")
    table.add_column("balance, sol")
    with Live(table, refresh_per_second=0.5):
        for count, address in enumerate(addresses):
            balance = get_sol_balance_with_retries(rpc_nodes, address, proxies=proxies, retries=5).map_or_else(
                lambda err: err,
                lambda ok: str(lamports_to_sol(ok, round_ndigits)),
            )
            row: list[str] = [str(count), address, balance]
            table.add_row(*row)
