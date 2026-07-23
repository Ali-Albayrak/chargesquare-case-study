from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

from app.models import SessionStatus

# Decimal in-process; float on the wire.
SafeDecimal = Annotated[
    Decimal,
    PlainSerializer(lambda v: float(v), return_type=float, when_used="json"),
]


class HealthResponse(BaseModel):
    status: str = "ok"


class StartSessionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(alias="userId")
    connector_id: int = Field(alias="connectorId")


class StopSessionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    energy_kwh: SafeDecimal = Field(alias="energyKwh")

    @field_validator("energy_kwh")
    @classmethod
    def energy_non_negative(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("energyKwh must be >= 0")
        return value


class TariffSnapshotOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tariff_id: int = Field(alias="tariffId")
    price_per_kwh: SafeDecimal = Field(alias="pricePerKwh")
    start_fee: SafeDecimal | None = Field(alias="startFee")
    currency: str


class SessionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    session_id: int = Field(alias="sessionId")
    user_id: int = Field(alias="userId")
    connector_id: int = Field(alias="connectorId")
    status: SessionStatus
    started_at: datetime = Field(alias="startedAt")
    ended_at: datetime | None = Field(default=None, alias="endedAt")
    energy_kwh: SafeDecimal | None = Field(default=None, alias="energyKwh")
    cost: SafeDecimal | None = Field(default=None, alias="cost")
    currency: str
    wallet_balance_after: SafeDecimal | None = Field(default=None, alias="walletBalanceAfter")
    tariff_snapshot: TariffSnapshotOut = Field(alias="tariffSnapshot")


class TopUpRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    amount: SafeDecimal = Field(gt=0)


class WalletOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: int = Field(alias="userId")
    balance: SafeDecimal
    currency: str
