import json
from collections.abc import Sequence
from typing import Any

import websockets
from mm_crypto_utils import Nodes, Proxies, retry_with_node_and_proxy
from mm_std import Result, http_request


async def rpc_call(
    node: str,
    method: str,
    params: Sequence[object],
    timeout: float,
    proxy: str | None,
    id_: int = 1,
) -> Result[Any]:
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": id_}
    if node.startswith("http"):
        return await _http_call(node, data, timeout, proxy)
    return await _ws_call(node, data, timeout)


async def _http_call(node: str, data: dict[str, object], timeout: float, proxy: str | None) -> Result[Any]:
    res = await http_request(node, method="POST", proxy=proxy, timeout=timeout, json=data)
    if res.is_error():
        return res.to_result_failure()
    try:
        parsed_body = res.parse_json_body()
        err = parsed_body.get("error", {}).get("message", "")
        if err:
            return res.to_result_failure(f"service_error: {err}")
        if "result" in parsed_body:
            return res.to_result_success(parsed_body["result"])
        return res.to_result_failure("unknown_response")
    except Exception as e:
        return res.to_result_failure(e)


async def _ws_call(node: str, data: dict[str, object], timeout: float) -> Result[Any]:
    response = None
    try:
        async with websockets.connect(node, open_timeout=timeout) as ws:
            await ws.send(json.dumps(data))
            response = json.loads(await ws.recv())

        err = response.get("error", {}).get("message", "")
        if err:
            return Result.failure(f"service_error: {err}", {"response": response})
        if "result" in response:
            return Result.success(response["result"], {"response": response})
        return Result.failure("unknown_response", {"response": response})
    except TimeoutError:
        return Result.failure("timeout", {"response": response})
    except Exception as e:
        return Result.failure(e, {"response": response})


async def get_block_height(node: str, timeout: float = 10, proxy: str | None = None) -> Result[int]:
    return await rpc_call(node=node, method="getBlockHeight", params=[], timeout=timeout, proxy=proxy)


async def get_balance(node: str, address: str, timeout: float = 5, proxy: str | None = None) -> Result[int]:
    """Returns balance in lamports"""
    return (await rpc_call(node=node, method="getBalance", params=[address], timeout=timeout, proxy=proxy)).map(
        lambda r: r["value"]
    )


async def get_balance_with_retries(
    retries: int, nodes: Nodes, proxies: Proxies, *, address: str, timeout: float = 5
) -> Result[int]:
    """
    Retry get_balance with different nodes and proxies
    """
    return await retry_with_node_and_proxy(
        retries,
        nodes,
        proxies,
        lambda node, proxy: get_balance(node=node, address=address, timeout=timeout, proxy=proxy),
    )
