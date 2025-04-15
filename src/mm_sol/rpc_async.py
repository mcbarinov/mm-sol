import json
from collections.abc import Sequence
from typing import Any

import websockets
from mm_std import DataResult, http_request


async def rpc_call(
    node: str,
    method: str,
    params: Sequence[object],
    timeout: float,
    proxy: str | None,
    id_: int = 1,
) -> DataResult[Any]:
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": id_}
    if node.startswith("http"):
        return await _http_call(node, data, timeout, proxy)
    return await _ws_call(node, data, timeout)


async def _http_call(node: str, data: dict[str, object], timeout: float, proxy: str | None) -> DataResult[Any]:
    res = await http_request(node, method="POST", proxy=proxy, timeout=timeout, json=data)
    if res.is_error():
        return res.to_data_result_err()
    try:
        parsed_body = res.parse_json_body()
        err = parsed_body.get("error", {}).get("message", "")
        if err:
            return res.to_data_result_err(f"service_error: {err}")
        if "result" in parsed_body:
            return res.to_data_result_ok(parsed_body["result"])
        return res.to_data_result_err("unknown_response")
    except Exception as err:
        return res.to_data_result_err(f"exception: {err}")


async def _ws_call(node: str, data: dict[str, object], timeout: float) -> DataResult[Any]:
    try:
        async with websockets.connect(node, open_timeout=timeout) as ws:
            await ws.send(json.dumps(data))
            response = json.loads(await ws.recv())

        err = response.get("error", {}).get("message", "")
        if err:
            return DataResult.err(f"service_error: {err}", {"res": response})
        if "result" in response:
            return DataResult.ok(response["result"], {"res": response})
        return DataResult.err("unknown_response", {"res": response})
    except TimeoutError:
        return DataResult.err("timeout")
    except Exception as err:
        return DataResult.exception(err)


async def get_block_height(node: str, timeout: float = 10, proxy: str | None = None) -> DataResult[int]:
    return await rpc_call(node=node, method="getBlockHeight", params=[], timeout=timeout, proxy=proxy)


async def get_balance(node: str, address: str, timeout: float = 10, proxy: str | None = None) -> DataResult[int]:
    """Returns balance in lamports"""
    return (await rpc_call(node=node, method="getBalance", params=[address], timeout=timeout, proxy=proxy)).map(
        lambda r: r["value"]
    )
