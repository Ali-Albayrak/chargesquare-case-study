from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import httpx

from app.config import settings
from app.errors import AppError


@dataclass(frozen=True)
class StationConnector:
    connector_id: int
    status: str
    tariff_id: int
    price_per_kwh: Decimal
    start_fee: Decimal | None
    currency: str


class StationClient:
    def __init__(self, base_url: str | None = None, timeout: float = 5.0) -> None:
        self.base_url = (base_url or settings.station_service_url).rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str) -> httpx.Response:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                return client.request(method, url)
        except httpx.RequestError as exc:
            raise AppError(
                status_code=503,
                error="STATION_UNAVAILABLE",
                message=f"Station Service is unreachable: {exc}",
            ) from exc

    def get_connector(self, connector_id: int) -> StationConnector:
        response = self._request("GET", f"/connectors/{connector_id}")
        return self._parse_connector_response(response, connector_id)

    def occupy(self, connector_id: int) -> None:
        response = self._request("POST", f"/connectors/{connector_id}/occupy")
        if response.status_code == 200:
            return
        self._raise_mapped_error(response, connector_id)

    def release(self, connector_id: int) -> None:
        response = self._request("POST", f"/connectors/{connector_id}/release")
        if response.status_code == 200:
            return
        # Release conflicts/unknowns still surface as fail-fast dependency errors for Stage 1
        if response.status_code in (404, 409):
            raise AppError(
                status_code=503,
                error="STATION_UNAVAILABLE",
                message=f"Station Service returned unexpected status {response.status_code} on release",
            )
        self._raise_mapped_error(response, connector_id)

    def _parse_connector_response(self, response: httpx.Response, connector_id: int) -> StationConnector:
        if response.status_code == 200:
            body = response.json()
            tariff = body["tariff"]
            return StationConnector(
                connector_id=body["connectorId"],
                status=body["status"],
                tariff_id=tariff["tariffId"],
                price_per_kwh=Decimal(str(tariff["pricePerKwh"])),
                start_fee=None if tariff.get("startFee") is None else Decimal(str(tariff["startFee"])),
                currency=tariff["currency"],
            )
        self._raise_mapped_error(response, connector_id)
        raise AssertionError("unreachable")

    def _raise_mapped_error(self, response: httpx.Response, connector_id: int) -> None:
        if response.status_code == 404:
            raise AppError(
                status_code=404,
                error="CONNECTOR_NOT_FOUND",
                message=f"Connector {connector_id} was not found",
            )
        if response.status_code == 409:
            raise AppError(
                status_code=409,
                error="CONNECTOR_OCCUPIED",
                message=f"Connector {connector_id} is not AVAILABLE",
            )
        raise AppError(
            status_code=503,
            error="STATION_UNAVAILABLE",
            message=f"Station Service returned unexpected status {response.status_code}",
        )


station_client = StationClient()
