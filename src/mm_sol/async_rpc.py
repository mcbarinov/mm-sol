from typing import Any

from mm_std import Result, ahr


async def rpc_call(
    *,
    node: str,
    method: str,
    params: list[Any],
    id_: int = 1,
    timeout: float = 10,
    proxy: str | None = None,
) -> Result[Any]:
    data = {"jsonrpc": "2.0", "method": method, "params": params, "id": id_}
    if node.startswith("http"):
        return await _http_call(node, data, timeout, proxy)
    raise NotImplementedError("ws is not implemented")


async def _http_call(node: str, data: dict[str, object], timeout: float, proxy: str | None) -> Result[Any]:
    res = await ahr(node, method="POST", proxy=proxy, timeout=timeout, params=data, json_params=True)
    try:
        if res.is_error():
            return res.to_err_result()

        err = res.json.get("error", {}).get("message", "")
        if err:
            return res.to_err_result(f"service_error: {err}")
        if "result" in res.json:
            return res.to_ok_result(res.json["result"])

        return res.to_err_result("unknown_response")
    except Exception as e:
        return res.to_err_result(f"exception: {e!s}")


async def get_balance(node: str, address: str, timeout: float = 10, proxy: str | None = None) -> Result[int]:
    """Returns balance in lamports"""
    return (await rpc_call(node=node, method="getBalance", params=[address], timeout=timeout, proxy=proxy)).and_then(
        lambda r: r["value"]
    )
