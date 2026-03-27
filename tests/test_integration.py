from __future__ import annotations

import os
import re

import pytest

from agentsim.client import AgentSimClient

LIVE_API_KEY = os.environ.get("AGENTSIM_API_KEY")
LIVE_BASE_URL = "https://api.agentsim.dev/v1"

skip_without_key = pytest.mark.skipif(
    not LIVE_API_KEY,
    reason="AGENTSIM_API_KEY not set — skipping live integration tests",
)


@skip_without_key
@pytest.mark.asyncio
async def test_provision_and_release() -> None:
    """Provision a number and verify the session shape, then auto-release."""
    client = AgentSimClient(LIVE_API_KEY, base_url=LIVE_BASE_URL)  # type: ignore[arg-type]
    async with client.provision(agent_id="e2e-test", country="US") as session:
        assert session.number.startswith("+"), f"Expected E.164 number, got {session.number!r}"
        assert len(session.session_id) > 0, "session_id should not be empty"
        assert session.status == "active", f"Expected status 'active', got {session.status!r}"
    await client.aclose()


@skip_without_key
@pytest.mark.asyncio
async def test_provision_response_shape() -> None:
    """Verify provisioned number is valid E.164 format."""
    client = AgentSimClient(LIVE_API_KEY, base_url=LIVE_BASE_URL)  # type: ignore[arg-type]
    async with client.provision(agent_id="e2e-shape-test", country="US") as session:
        # E.164: + followed by digits only
        assert re.match(r"^\+\d+$", session.number), (
            f"Number {session.number!r} is not valid E.164 format"
        )
        assert len(session.session_id) > 0
    await client.aclose()
