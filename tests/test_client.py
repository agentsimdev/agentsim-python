from __future__ import annotations

import pytest
import respx
import httpx

from agentsim.client import AgentSimClient
from agentsim.exceptions import OtpTimeoutError, PoolExhaustedError

BASE = "https://api.agentsim.dev/v1"

PROVISION_RESPONSE = {
    "session_id": "sess-abc123",
    "number": "+15551234567",
    "country": "US",
    "agent_id": "test-bot",
    "status": "active",
    "expires_at": "2026-03-16T20:00:00Z",
}


@respx.mock
async def test_provision_returns_session() -> None:
    respx.post(f"{BASE}/sessions").mock(
        return_value=httpx.Response(201, json=PROVISION_RESPONSE)
    )
    client = AgentSimClient("test-key")
    session = await client.provision(agent_id="test-bot", country="US")
    assert session.number == "+15551234567"
    assert session.session_id == "sess-abc123"
    await client.aclose()


@respx.mock
async def test_provision_pool_exhausted() -> None:
    respx.post(f"{BASE}/sessions").mock(
        return_value=httpx.Response(
            503,
            json={"error": "pool_exhausted", "message": "No US numbers available"},
        )
    )
    client = AgentSimClient("test-key")
    with pytest.raises(PoolExhaustedError):
        await client.provision(agent_id="test-bot", country="US")
    await client.aclose()


@respx.mock
async def test_wait_for_otp_returns_code() -> None:
    respx.post(f"{BASE}/sessions").mock(
        return_value=httpx.Response(201, json=PROVISION_RESPONSE)
    )
    respx.post(f"{BASE}/sessions/sess-abc123/wait").mock(
        return_value=httpx.Response(
            200,
            json={
                "otp_code": "123456",
                "from_number": "+15550000000",
                "received_at": "2026-03-16T18:00:00Z",
                "message_id": "msg-xyz",
            },
        )
    )
    client = AgentSimClient("test-key")
    session = await client.provision(agent_id="test-bot", country="US")
    result = await client.wait_for_otp(session.session_id, timeout=30)
    assert result.otp_code == "123456"
    await client.aclose()


@respx.mock
async def test_wait_for_otp_timeout() -> None:
    respx.post(f"{BASE}/sessions").mock(
        return_value=httpx.Response(201, json=PROVISION_RESPONSE)
    )
    respx.post(f"{BASE}/sessions/sess-abc123/wait").mock(
        return_value=httpx.Response(
            408,
            json={
                "error": "otp_timeout",
                "message": "No OTP received within timeout",
            },
        )
    )
    client = AgentSimClient("test-key")
    session = await client.provision(agent_id="test-bot", country="US")
    with pytest.raises(OtpTimeoutError):
        await client.wait_for_otp(session.session_id, timeout=30)
    await client.aclose()


@respx.mock
async def test_release_session() -> None:
    respx.post(f"{BASE}/sessions").mock(
        return_value=httpx.Response(201, json=PROVISION_RESPONSE)
    )
    respx.delete(f"{BASE}/sessions/sess-abc123").mock(
        return_value=httpx.Response(204)
    )
    client = AgentSimClient("test-key")
    session = await client.provision(agent_id="test-bot", country="US")
    await session.release()  # should complete without exception
    await client.aclose()
