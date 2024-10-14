from types import TracebackType
from typing import Self

import httpx
from httpx_socks import SyncProxyTransport
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
from solana.rpc.providers.core import _after_request_unparsed  # noqa: RUF100 # noqa
from solana.rpc.providers.http import HTTPProvider
from solders.rpc.requests import Body


class ProxyClient(Client):
    def __init__(
        self,
        endpoint: str | None = None,
        commitment: Commitment | None = None,
        timeout: float = 10,
        extra_headers: dict[str, str] | None = None,
        *,
        proxy: str | None = None,
        **kwargs: dict[str, object],
    ) -> None:
        """Init API client."""
        super().__init__(commitment)
        self._provider: ProxyHTTPProvider = ProxyHTTPProvider(
            endpoint=endpoint, timeout=timeout, extra_headers=extra_headers, proxy=proxy, **kwargs
        )

    def __enter__(self) -> Self:
        self._provider.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        self._provider.__exit__(exc_type, exc_value, traceback)

    def close(self) -> None:
        self._provider.close()


class ProxyHTTPProvider(HTTPProvider):
    def __init__(
        self,
        endpoint: str | None = None,
        extra_headers: dict[str, str] | None = None,
        timeout: float = 10,
        *,
        proxy: str | None = None,
        **kwargs: dict[str, object],
    ) -> None:
        super().__init__(endpoint=endpoint, extra_headers=extra_headers, timeout=timeout, **kwargs)
        self.session = Session(proxy, timeout=timeout)
        self._proxy = proxy

    def __str__(self) -> str:
        return f"HTTP RPC connection {self.endpoint_uri} | proxy={self._proxy}"

    def make_request_unparsed(self, body: Body) -> str:
        request_kwargs = self._before_request(body=body)
        raw_response = self.session.post(**request_kwargs)
        return _after_request_unparsed(raw_response)

    def make_batch_request_unparsed(self, reqs: tuple[Body, ...]) -> str:
        """Make an async HTTP request to an http rpc endpoint."""
        request_kwargs = self._before_batch_request(reqs)
        raw_response = self.session.post(**request_kwargs)
        return _after_request_unparsed(raw_response)

    def is_connected(self) -> bool:
        """Health check."""
        try:
            response = self.session.get(self.health_uri)
            response.raise_for_status()
        except (OSError, httpx.HTTPError) as err:
            self.logger.error("Health check failed with error: %s", str(err))
            return False

        return response.status_code == httpx.codes.OK

    def __enter__(self) -> Self:
        self.session.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        self.session.__exit__(exc_type, exc_value, traceback)

    def close(self) -> None:
        self.session.close()


class Session(httpx.Client):
    def __init__(
        self, proxy: str | None = None, follow_redirects: bool = True, timeout: float = 10, **kwargs: dict[str, object]
    ) -> None:
        if proxy:
            if proxy.startswith("http"):
                kwargs["proxy"] = proxy  # type: ignore[assignment]
            elif proxy.startswith("socks"):
                kwargs["transport"] = SyncProxyTransport.from_url(proxy)
            else:
                raise ValueError(f"Unsupported proxy type: {proxy}")
        # super().__init__(follow_redirects=follow_redirects, timeout=Timeout(timeout), **kwargs)  # type: ignore[arg-type]
        super().__init__(follow_redirects=follow_redirects, **kwargs)  # type: ignore[arg-type]


def get_client(
    endpoint: str,
    commitment: Commitment | None = None,
    extra_headers: dict[str, str] | None = None,
    proxy: str | None = None,
    timeout: float = 10,
    **kwargs: dict[str, object],
) -> ProxyClient:
    return ProxyClient(endpoint, timeout=timeout, proxy=proxy, commitment=commitment, extra_headers=extra_headers, **kwargs)
