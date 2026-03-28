# agentsim-sdk

Autonomous OTP relay for AI agents. AgentSIM provisions real carrier-routed phone numbers, receives inbound SMS, and delivers parsed OTP codes back to your agent — no human relay needed.

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

async with agentsim.provision(agent_id="checkout-bot", country="US") as num:
    await enter_phone_number(num.number)          # "+14155552671"
    otp = await num.wait_for_otp(timeout=60)
    await enter_otp(otp.otp_code)                 # "391847"
# number auto-released
```

## Auth

Set `AGENTSIM_API_KEY` in your environment, or call `agentsim.configure()` at startup:

```python
agentsim.configure(api_key="asm_live_xxx")
```

Get your API key at [console.agentsim.dev](https://console.agentsim.dev).

## API

### `agentsim.provision(*, agent_id, country="US", service_url=None, ttl_seconds=3600, webhook_url=None)`

Returns an async context manager. Provisions a number on enter, auto-releases on exit (even if the body raises).

```python
async with agentsim.provision(agent_id="stripe-setup", country="US") as num:
    print(num.number)   # E.164 phone number
    print(num.session_id)
    otp = await num.wait_for_otp(timeout=30)
    print(otp.otp_code)
```

### `num.wait_for_otp(timeout=60, auto_reroute=False, max_reroutes=2, on_reregistration_needed=None)`

Long-polls until an OTP arrives or `timeout` seconds elapse.

Returns: `OtpResult(otp_code, from_number, received_at)`

Raises: `OtpTimeoutError` if no OTP arrives within `timeout` seconds.

Set `auto_reroute=True` to automatically provision a replacement number in another country if no OTP arrives. `on_reregistration_needed` is an async callback `(new_number: str, country: str) -> None` called when re-registration on the target service is required.

### `agentsim.provision_sync(...)` / `num.wait_for_otp_sync(timeout=60)`

Synchronous variants for non-async codebases:

```python
with agentsim.provision_sync(agent_id="x") as num:
    otp = num.wait_for_otp_sync(timeout=60)
```

## Error Reference

| Exception | When |
|-----------|------|
| `AuthenticationError` | Missing or invalid API key |
| `PoolExhaustedError` | No numbers available in requested country |
| `OtpTimeoutError` | No OTP arrived within `timeout` seconds |
| `RateLimitError` | Too many requests — back off and retry |
| `SessionNotFoundError` | Session expired or already released |
| `CountryNotAllowedError` | Country not available on current plan |

## Supported Countries

US