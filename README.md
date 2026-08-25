# agentsim-sdk

We run the auth challenge so your agent doesn't die there. This Python SDK opens an SMS challenge, waits for the verdict, and closes the session. Import name is `agentsim`. Primary names: `open_challenge` / `wait_for_verdict`. `provision` / `wait_for_otp` are aliases that still work. There is no `AgentSIM()` class.

## Install

```bash
uv add agentsim-sdk
```

Or with pip:

```bash
pip install agentsim-sdk
```

## Quickstart

```python
import agentsim

async with agentsim.open_challenge(agent_id="checkout-bot", country="US") as num:
    await enter_phone_number(num.number)
    otp = await num.wait_for_verdict(timeout=60)
    await enter_otp(otp.otp_code)
```

## Auth

Set `AGENTSIM_API_KEY` in your environment, or call `agentsim.configure()` at startup:

```python
agentsim.configure(api_key="asm_live_xxx")
```

Get your API key at [console.agentsim.dev](https://console.agentsim.dev).

## API

### `agentsim.open_challenge(*, agent_id, country="US", service_url=None, ttl_seconds=3600, webhook_url=None)`

Returns an async context manager. Opens an SMS challenge on enter, auto-releases on exit. `provision` is an alias.

```python
async with agentsim.open_challenge(agent_id="checkout-bot", country="US") as num:
    print(num.number)
    print(num.session_id)
    otp = await num.wait_for_verdict(timeout=60)
    print(otp.otp_code)
```

### `num.wait_for_verdict(timeout=60, auto_reroute=False, max_reroutes=2, on_reregistration_needed=None)`

Long-polls until the SMS verdict arrives or `timeout` seconds elapse. `wait_for_otp` is an alias.

Returns: `OtpResult(otp_code, from_number, received_at)`

Raises: `OtpTimeoutError` if no verdict arrives within `timeout` seconds.

The shipped SDK does not include `wait_for_verdict_sync`. MCP agents should use `open_challenge` / `wait_for_verdict`.

## Error Reference

| Exception | When |
|-----------|------|
| `AuthenticationError` | Missing or invalid API key |
| `PoolExhaustedError` | No numbers available in requested country |
| `OtpTimeoutError` | No verdict arrived within `timeout` seconds |
| `RateLimitError` | Too many requests — back off and retry |
| `SessionNotFoundError` | Session expired or already released |

## Supported Countries

US
