from __future__ import annotations


class AgentSimError(Exception):
    """Base exception for all AgentSIM errors."""

    code: str = "unknown_error"
    status_code: int | None = None

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class AuthenticationError(AgentSimError):
    """Invalid or missing API key."""
    code = "unauthorized"
    status_code = 401


class ForbiddenError(AgentSimError):
    """API key revoked or lacking permissions."""
    code = "forbidden"
    status_code = 403


class PoolExhaustedError(AgentSimError):
    """No numbers available in the requested country pool."""
    code = "pool_exhausted"
    status_code = 503

    def __init__(
        self,
        message: str = "No numbers available in the requested country pool.",
        *,
        code: str | None = None,
        status_code: int | None = None,
        country: str = "",
        available_countries: list[str] | None = None,
    ) -> None:
        super().__init__(message, code=code, status_code=status_code)
        self.country = country
        self.available_countries = available_countries or []


class SessionNotFoundError(AgentSimError):
    """Session ID does not exist or is not owned by this account."""
    code = "not_found"
    status_code = 404


class OtpTimeoutError(AgentSimError):
    """No OTP arrived within the requested timeout window."""
    code = "otp_timeout"
    status_code = 408


class RateLimitError(AgentSimError):
    """Too many requests — rate limit exceeded."""
    code = "rate_limited"
    status_code = 429


class CountryNotAllowedError(AgentSimError):
    """Requested country is not available on the account's current plan."""
    code = "country_not_allowed_on_plan"
    status_code = 403

    def __init__(
        self,
        message: str = "Country not available on your current plan.",
        *,
        code: str | None = None,
        status_code: int | None = None,
        country: str = "",
        plan: str = "",
        allowed: list[str] | None = None,
    ) -> None:
        super().__init__(message, code=code, status_code=status_code)
        self.country = country
        self.plan = plan
        self.allowed = allowed or []


class ValidationError(AgentSimError):
    """Request body failed validation."""
    code = "validation_error"
    status_code = 422


class ApiError(AgentSimError):
    """Unexpected API error not covered by a specific subclass."""
    code = "internal_error"
    status_code = 500


_CODE_TO_EXCEPTION: dict[str, type[AgentSimError]] = {
    "unauthorized": AuthenticationError,
    "forbidden": ForbiddenError,
    "pool_exhausted": PoolExhaustedError,
    "not_found": SessionNotFoundError,
    "otp_timeout": OtpTimeoutError,
    "rate_limited": RateLimitError,
    "validation_error": ValidationError,
    "country_not_allowed_on_plan": CountryNotAllowedError,
}


def from_api_error(
    code: str, message: str, status_code: int, data: dict | None = None
) -> AgentSimError:
    if code == "pool_exhausted":
        country = data.get("country", "") if data else ""
        available_countries = data.get("available_countries", []) if data else []
        return PoolExhaustedError(
            message,
            code=code,
            status_code=status_code,
            country=country,
            available_countries=available_countries,
        )
    if code == "country_not_allowed_on_plan":
        return CountryNotAllowedError(
            message,
            code=code,
            status_code=status_code,
            country=data.get("country", "") if data else "",
            plan=data.get("plan", "") if data else "",
            allowed=data.get("allowed", []) if data else [],
        )
    cls = _CODE_TO_EXCEPTION.get(code, ApiError)
    return cls(message, code=code, status_code=status_code)
