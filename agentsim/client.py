from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import Any, AsyncIterator, Awaitable, Callable, Iterator, Optional

import httpx

from .exceptions import AgentSimError, OtpTimeoutError, from_api_error
from .models import OtpResult, ProvisionedNumber, SmsMessage

DEFAULT_BASE_URL = "https://api.agentsim.dev/v1"
DEFAULT_TIMEOUT = 60.0


class AgentSimClient:
    def __init__(self, api_key: str, *, base_url: str = DEFAULT_BASE_URL) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={"x-api-key": api_key, "Content-Type": "application/json"},
            timeout=DEFAULT_TIMEOUT,
        )

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise AgentSimError(f"Network error: {exc}") from exc

        if response.status_code == 204:
            return None

        body: dict[str, Any] = {}
        try:
            body = response.json()
        except Exception:
            pass

        if not response.is_success:
            code = body.get("error", "unknown_error")
            message = body.get("message", response.text)
            raise from_api_error(code, message, response.status_code, body)

        return body

    async def provision(
        self,
        *,
        agent_id: str,
        country: Optional[str] = None,
        service_url: Optional[str] = None,
        ttl_seconds: int = 3600,
        webhook_url: Optional[str] = None,
    ) -> "NumberSession":
        body: dict[str, Any] = {
            "agent_id": agent_id,
            "ttl_seconds": ttl_seconds,
        }
        if country is not None:
            body["country"] = country
        if service_url is not None:
            body["service_url"] = service_url
        if webhook_url:
            body["webhook_url"] = webhook_url

        data = await self._request("POST", "/sessions", json=body)
        provisioned = ProvisionedNumber.model_validate(data)
        return NumberSession(provisioned, self)

    async def release(self, session_id: str) -> None:
        await self._request("DELETE", f"/sessions/{session_id}")

    async def wait_for_otp(
        self,
        session_id: str,
        *,
        timeout: int = 60,
        auto_reroute: bool = False,
        max_reroutes: int = 2,
        on_reregistration_needed: Optional[Callable[[str, str], Awaitable[None]]] = None,
        _current_country: str = "US",
    ) -> OtpResult:
        """Wait for an OTP to arrive on the provisioned number.

        Raises ``OtpTimeoutError`` if no OTP is received within *timeout* seconds.
        Sessions that raise ``OtpTimeoutError`` are NOT billed.
        """
        if not auto_reroute:
            data = await self._request(
                "POST",
                f"/sessions/{session_id}/wait",
                json={"timeout_seconds": timeout},
                timeout=timeout + 10.0,
            )
            return OtpResult.model_validate(data)

        _FALLBACK_CHAIN = ["US", "GB", "DE", "FR", "NL", "EE"]
        current_idx = _FALLBACK_CHAIN.index(_current_country) if _current_country in _FALLBACK_CHAIN else -1
        reroute_chain = (
            _FALLBACK_CHAIN[current_idx + 1:] + _FALLBACK_CHAIN[:current_idx]
            if current_idx >= 0
            else list(_FALLBACK_CHAIN)
        )

        reroutes_used = 0
        chain_idx = 0

        while True:
            try:
                data = await self._request(
                    "POST",
                    f"/sessions/{session_id}/wait",
                    json={"timeout_seconds": timeout},
                    timeout=timeout + 10.0,
                )
                return OtpResult.model_validate(data)
            except OtpTimeoutError:
                if reroutes_used >= max_reroutes or chain_idx >= len(reroute_chain):
                    raise

                next_country = reroute_chain[chain_idx]
                chain_idx += 1
                reroutes_used += 1

                reroute_data = await self._request(
                    "POST",
                    f"/sessions/{session_id}/reroute",
                    json={"country": next_country},
                )
                new_number: str = reroute_data["new_number"]

                if on_reregistration_needed is not None:
                    await on_reregistration_needed(new_number, next_country)

    async def get_messages(self, session_id: str) -> list[SmsMessage]:
        data = await self._request("GET", f"/sessions/{session_id}/messages")
        return [SmsMessage.model_validate(m) for m in data.get("messages", [])]

    async def aclose(self) -> None:
        await self._client.aclose()


class NumberSession:
    def __init__(self, provisioned: ProvisionedNumber, client: AgentSimClient) -> None:
        self._provisioned = provisioned
        self._client = client
        self._released = False

    @property
    def session_id(self) -> str:
        return self._provisioned.session_id

    @property
    def number(self) -> str:
        return self._provisioned.number

    @property
    def country(self) -> str:
        return self._provisioned.country

    @property
    def expires_at(self) -> Any:
        return self._provisioned.expires_at

    async def wait_for_otp(
        self,
        *,
        timeout: int = 60,
        auto_reroute: bool = False,
        max_reroutes: int = 2,
        on_reregistration_needed: Optional[Callable[[str, str], Awaitable[None]]] = None,
    ) -> OtpResult:
        return await self._client.wait_for_otp(
            self.session_id,
            timeout=timeout,
            auto_reroute=auto_reroute,
            max_reroutes=max_reroutes,
            on_reregistration_needed=on_reregistration_needed,
            _current_country=self._provisioned.country,
        )

    async def messages(self) -> list[SmsMessage]:
        return await self._client.get_messages(self.session_id)

    async def release(self) -> None:
        if not self._released:
            self._released = True
            await self._client.release(self.session_id)

    async def __aenter__(self) -> "NumberSession":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.release()


@asynccontextmanager
async def _provision_ctx(
    client: AgentSimClient,
    *,
    agent_id: str,
    country: Optional[str] = None,
    service_url: Optional[str] = None,
    ttl_seconds: int = 3600,
    webhook_url: Optional[str] = None,
) -> AsyncIterator[NumberSession]:
    session = await client.provision(
        agent_id=agent_id,
        country=country,
        service_url=service_url,
        ttl_seconds=ttl_seconds,
        webhook_url=webhook_url,
    )
    try:
        yield session
    finally:
        await session.release()


def provision_sync(
    api_key: str,
    *,
    agent_id: str,
    country: Optional[str] = None,
    service_url: Optional[str] = None,
    ttl_seconds: int = 3600,
    webhook_url: Optional[str] = None,
    base_url: str = DEFAULT_BASE_URL,
) -> "_SyncNumberSessionCtx":
    return _SyncNumberSessionCtx(
        api_key=api_key,
        agent_id=agent_id,
        country=country,
        service_url=service_url,
        ttl_seconds=ttl_seconds,
        webhook_url=webhook_url,
        base_url=base_url,
    )


class _SyncNumberSessionCtx:
    def __init__(self, *, api_key: str, agent_id: str, **kwargs: Any) -> None:
        self._api_key = api_key
        self._agent_id = agent_id
        self._kwargs = kwargs
        self._session: Optional[NumberSession] = None

    def __enter__(self) -> "NumberSession":
        loop = asyncio.new_event_loop()
        self._loop = loop
        client = AgentSimClient(self._api_key, base_url=self._kwargs.get("base_url", DEFAULT_BASE_URL))
        self._client = client
        session = loop.run_until_complete(
            client.provision(agent_id=self._agent_id, **{
                k: v for k, v in self._kwargs.items() if k != "base_url"
            })
        )
        self._session = session
        return session

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            if self._session:
                self._loop.run_until_complete(self._session.release())
            self._loop.run_until_complete(self._client.aclose())
        except Exception:
            if exc_type is None:
                raise  # only propagate cleanup error if no original exception
        finally:
            self._loop.close()
