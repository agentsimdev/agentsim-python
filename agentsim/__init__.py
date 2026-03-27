"""AgentSIM Python SDK — autonomous OTP relay for AI agents."""

from __future__ import annotations

import os
from typing import Optional

from .client import AgentSimClient, NumberSession, _SyncNumberSessionCtx
from .exceptions import (
    AgentSimError,
    AuthenticationError,
    ForbiddenError,
    OtpTimeoutError,
    PoolExhaustedError,
    RateLimitError,
    SessionNotFoundError,
    ValidationError,
    ApiError,
)
from .models import OtpResult, ProvisionedNumber, SmsMessage, UsageStats

__all__ = [
    "configure",
    "provision",
    "provision_sync",
    "AgentSimClient",
    "NumberSession",
    "AgentSimError",
    "AuthenticationError",
    "ForbiddenError",
    "OtpTimeoutError",
    "PoolExhaustedError",
    "RateLimitError",
    "SessionNotFoundError",
    "ValidationError",
    "ApiError",
    "OtpResult",
    "ProvisionedNumber",
    "SmsMessage",
    "UsageStats",
]

_default_api_key: Optional[str] = os.environ.get("AGENTSIM_API_KEY")
_default_base_url: str = os.environ.get("AGENTSIM_BASE_URL", "https://api.agentsim.dev/v1")


class _AsyncProvisionCtx:
    """Wraps the async provision coroutine so `async with agentsim.provision(...)` works."""

    __slots__ = ("_coro", "_session")

    def __init__(self, coro: object) -> None:
        self._coro = coro
        self._session: Optional[NumberSession] = None

    async def __aenter__(self) -> NumberSession:
        self._session = await self._coro  # type: ignore[misc]
        return self._session

    async def __aexit__(self, *args: object) -> None:
        if self._session is not None:
            await self._session.__aexit__(*args)


def configure(*, api_key: str, base_url: Optional[str] = None) -> None:
    """Set module-level defaults used by `provision()` and `provision_sync()`."""
    global _default_api_key, _default_base_url
    _default_api_key = api_key
    if base_url:
        _default_base_url = base_url


def provision(
    *,
    agent_id: str,
    country: Optional[str] = None,
    service_url: Optional[str] = None,
    ttl_seconds: int = 3600,
    webhook_url: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> NumberSession:
    """Async context manager — provision a number, auto-release on exit.

    Starts a billable session. $0.99 per session on the Builder plan.
    Free on Hobby (10 sessions/month limit). Sessions that raise
    ``OtpTimeoutError`` are NOT billed.

    Usage::

        async with agentsim.provision(agent_id="checkout-bot") as num:
            otp = await num.wait_for_otp(timeout=60)
    """
    resolved_key = api_key or _default_api_key
    if not resolved_key:
        raise AuthenticationError(
            "No API key provided. Set AGENTSIM_API_KEY or call agentsim.configure(api_key=...)."
        )
    client = AgentSimClient(resolved_key, base_url=base_url or _default_base_url)
    return _AsyncProvisionCtx(client.provision(
        agent_id=agent_id,
        country=country,
        service_url=service_url,
        ttl_seconds=ttl_seconds,
        webhook_url=webhook_url,
    ))


def provision_sync(
    *,
    agent_id: str,
    country: Optional[str] = None,
    service_url: Optional[str] = None,
    ttl_seconds: int = 3600,
    webhook_url: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> _SyncNumberSessionCtx:
    """Synchronous context manager — provision a number, auto-release on exit.

    Starts a billable session. $0.99 per session on the Builder plan.
    Free on Hobby (10 sessions/month limit). Sessions that raise
    ``OtpTimeoutError`` are NOT billed.

    Usage::

        with agentsim.provision_sync(agent_id="checkout-bot") as num:
            otp = num.wait_for_otp_sync(timeout=60)
    """
    resolved_key = api_key or _default_api_key
    if not resolved_key:
        raise AuthenticationError(
            "No API key provided. Set AGENTSIM_API_KEY or call agentsim.configure(api_key=...)."
        )
    from .client import provision_sync as _ps

    return _ps(
        resolved_key,
        agent_id=agent_id,
        country=country,
        service_url=service_url,
        ttl_seconds=ttl_seconds,
        webhook_url=webhook_url,
        base_url=base_url or _default_base_url,
    )
