from mm_std import print_json

from mm_sol import rpc


def run(urls: list[str], proxy: str | None) -> None:
    for url in urls:
        res = rpc.get_block_height(url, proxy=proxy, timeout=10)
        print_json({url: res.ok_or_err()})
