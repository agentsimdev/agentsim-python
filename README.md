<p align="center">
  <a href="https://agentsim.dev">
    <img src="https://agentsim.dev/logo.svg" alt="AgentSIM" width="80" />
  </a>
</p>

<h1 align="center">agentsim-sdk</h1>

<p align="center">
  <strong>Python SDK for AgentSIM — real SIM-backed phone numbers for AI agents</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/agentsim-sdk/"><img src="https://img.shields.io/pypi/v/agentsim-sdk?color=%2334D058&label=pypi" alt="PyPI version"></a>
  <a href="https://pypi.org/project/agentsim-sdk/"><img src="https://img.shields.io/pypi/pyversions/agentsim-sdk" alt="Python versions"></a>
  <a href="https://github.com/agentsimdev/agentsim-python/blob/main/LICENSE"><img src="https://img.shields.io/github/license/agentsimdev/agentsim-python" alt="License"></a>
</p>

<p align="center">
  <a href="https://docs.agentsim.dev">Docs</a> ·
  <a href="https://agentsim.dev/dashboard">Dashboard</a> ·
  <a href="https://github.com/agentsimdev/agentsim-examples">Examples</a> ·
  <a href="https://github.com/agentsimdev/agentsim-mcp">MCP Server</a>
</p>

---

Provision real carrier-routed mobile numbers, receive inbound SMS, and get parsed OTP codes — all from your AI agent. No VoIP. No human relay. Carrier lookup returns `mobile`.

## Install

```bash
pip install agentsim-sdk
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add agentsim-sdk
```

## Quick Start

```python
import agentsim

async with agentsim.provision(agent_id="checkout-bot", country="US") as num:
    await enter_phone_number(num.number)        # "+14155552671"
    otp = await num.wait_for_otp(timeout=60)
    await enter_otp(otp.otp_code)               # "391847"
# number auto-released
```

## Authentication

Set `AGENTSIM_API_KEY` in your environment, or call `configure()` at startup:

```python
agentsim.configure(api_key="asm_live_xxx")
```

Get your API key at [agentsim.dev/dashboard](https://agentsim.dev/dashboard).

## Usage

### Async (recommended)

```python
import agentsim

async with agentsim.provision(agent_id="signup-bot", country="US") as num:
    print(num.number)       # E.164 phone number
    print(num.session_id)   # session identifier

    otp = await num.wait_for_otp(timeout=60)
    print(otp.otp_code)     # "847291"
```

### Sync

```python
import agentsim

with agentsim.provision_sync(agent_id="checkout-bot") as num:
    otp = num.wait_for_otp_sync(timeout=60)
    print(otp.otp_code)
```

### Auto-reroute

If the first number doesn't receive an OTP (carrier cold-start filtering), automatically swap to a fresh number:

```python
async with agentsim.provision(agent_id="resilient-bot") as num:
    otp = await num.wait_for_otp(
        timeout=60,
        auto_reroute=True,
        max_reroutes=2,
        on_reregistration_needed=handle_new_number,
    )
```

## API Reference

### `agentsim.provision()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent_id` | `str` | required | Identifier for your agent |
| `country` | `str` | `"US"` | ISO 3166-1 alpha-2 country code |
| `ttl_seconds` | `int` | `3600` | Auto-release after N seconds |
| `webhook_url` | `str` | `None` | Receive OTPs via webhook |

Returns an async context manager. Provisions a number on enter, auto-releases on exit.

### `num.wait_for_otp()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timeout` | `int` | `60` | Max seconds to wait |
| `auto_reroute` | `bool` | `False` | Swap number on timeout |
| `max_reroutes` | `int` | `2` | Max reroute attempts |

Returns `OtpResult(otp_code, from_number, received_at)`.

### `num.release()`

Release the number early. Called automatically when the context manager exits.

## Error Handling

```python
from agentsim import OtpTimeoutError, PoolExhaustedError

try:
    async with agentsim.provision(agent_id="my-bot") as num:
        otp = await num.wait_for_otp(timeout=30)
except OtpTimeoutError:
    print("No OTP received — not billed")
except PoolExhaustedError:
    print("No numbers available in this country")
```

| Exception | HTTP | When |
|-----------|------|------|
| `AuthenticationError` | 401 | Missing or invalid API key |
| `ForbiddenError` | 403 | Key revoked or lacking permissions |
| `PoolExhaustedError` | 503 | No numbers available in requested country |
| `OtpTimeoutError` | 408 | No OTP arrived within timeout (not billed) |
| `RateLimitError` | 429 | Too many requests |
| `SessionNotFoundError` | 404 | Session expired or already released |
| `CountryNotAllowedError` | 403 | Country not on your plan |

## Pricing

- **Hobby**: 10 free sessions/month
- **Builder**: $0.99/session
- Sessions that time out (`OtpTimeoutError`) are **not billed**

## Links

- [Documentation](https://docs.agentsim.dev)
- [TypeScript SDK](https://github.com/agentsimdev/agentsim-typescript)
- [MCP Server](https://github.com/agentsimdev/agentsim-mcp)
- [Examples](https://github.com/agentsimdev/agentsim-examples)

## License

[MIT](LICENSE)
