from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ProvisionedNumber(BaseModel):
    session_id: str
    number: str
    country: str
    agent_id: str
    status: str
    expires_at: datetime
    created_at: Optional[datetime] = None

    @field_validator("expires_at", "created_at", mode="before")
    @classmethod
    def parse_datetime(cls, v: object) -> object:
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class OtpResult(BaseModel):
    otp_code: str
    from_number: Optional[str] = None
    received_at: datetime
    message_id: Optional[str] = None

    @field_validator("received_at", mode="before")
    @classmethod
    def parse_datetime(cls, v: object) -> object:
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class SmsMessage(BaseModel):
    id: str
    from_number: str
    to_number: str
    otp_code: Optional[str] = None
    otp_confidence: Optional[str] = None
    otp_method: Optional[str] = None
    otp_consumed: bool
    otp_consumed_at: Optional[datetime] = None
    webhook_delivered: bool
    received_at: datetime

    @field_validator("received_at", "otp_consumed_at", mode="before")
    @classmethod
    def parse_datetime(cls, v: object) -> object:
        if v is None:
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class UsageStats(BaseModel):
    total_provisioned: int = 0
    total_sms_received: int = 0
    total_otp_delivered: int = 0
    total_cost_usd_micro: int = 0
    by_agent: dict[str, dict[str, int]] = {}
