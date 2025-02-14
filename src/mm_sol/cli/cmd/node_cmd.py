from mm_std import print_json

from mm_sol import rpc
from mm_sol.cli import cli_utils


def run(urls: list[str], proxy: str | None) -> None:
    result = {}
    for url in [cli_utils.public_rpc_url(u) for u in urls]:
        result[url] = rpc.get_block_height(url, proxy=proxy, timeout=10).ok_or_err()
    print_json(data=result)
