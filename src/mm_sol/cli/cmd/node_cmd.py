import mm_print

from mm_sol import rpc
from mm_sol.cli import cli_utils


async def run(urls: list[str], proxy: str | None) -> None:
    result = {}
    for url in [cli_utils.public_rpc_url(u) for u in urls]:
        result[url] = (await rpc.get_block_height(url, proxy=proxy, timeout=10)).value_or_error()
    mm_print.json(data=result)
