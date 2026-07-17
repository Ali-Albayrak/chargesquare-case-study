from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

from app.models import ConnectorStatus

Money = Annotated[
    Decimal,
    PlainSerializer(lambda v: float(v), return_type=float, when_used="json"),
]


class HealthResponse(BaseModel):
    status: str = "ok"


class TariffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    tariff_id: int = Field(alias="tariffId")
    price_per_kwh: Money = Field(alias="pricePerKwh")
    start_fee: Money | None = Field(alias="startFee")
    currency: str


class ConnectorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    connector_id: int = Field(alias="connectorId")
    station_id: int = Field(alias="stationId")
    type: str
    power_kw: Money = Field(alias="powerKw")
    status: ConnectorStatus
    tariff: TariffOut


class ConnectorStatusOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    connector_id: int = Field(alias="connectorId")
    status: ConnectorStatus
