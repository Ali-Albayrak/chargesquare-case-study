"""Baseline seed data (case-study IDs) separated from idempotent insert logic."""

import logging
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models import Connector, ConnectorStatus, Station, Tariff

logger = logging.getLogger(__name__)

# --- Seed data (easy to extend for users/wallets later) ---

STATIONS = [
    {"id": 1, "name": "Demo Station"},
]

TARIFFS = [
    {
        "id": 5,
        "price_per_kwh": Decimal("8.50"),
        "start_fee": Decimal("2.00"),
        "currency": "TRY",
    },
]

CONNECTORS = [
    {
        "id": 10,
        "station_id": 1,
        "tariff_id": 5,
        "type": "CCS2-DC",
        "power_kw": Decimal("60"),
        "status": ConnectorStatus.AVAILABLE,
    },
    {
        "id": 11,
        "station_id": 1,
        "tariff_id": 5,
        "type": "CCS2-DC",
        "power_kw": Decimal("60"),
        "status": ConnectorStatus.AVAILABLE,
    },
]

# -- Seed data end --


def ensure_exists(db: Session, model: type, instance: Any) -> bool:
    """Insert by primary key if missing. Never updates an existing row. Does not commit."""
    pk = instance.id
    if db.get(model, pk) is None:
        db.add(instance)
        return True
    return False


def seed_baseline(db: Session) -> None:
    """
    Idempotent ensure of baseline rows.

    Inserts missing stations/tariffs/connectors only; never overwrites live existing data.
    Commits the seed transaction when finished.
    """
    inserted = 0

    for row in STATIONS:
        if ensure_exists(db, Station, Station(**row)):
            logger.debug(f"Inserted station: {row}")
            inserted += 1

    for row in TARIFFS:
        if ensure_exists(db, Tariff, Tariff(**row)):
            logger.debug(f"Inserted tariff: {row}")
            inserted += 1

    for row in CONNECTORS:
        if ensure_exists(db, Connector, Connector(**row)):
            logger.debug(f"Inserted connector: {row}")
            inserted += 1

    db.commit()
    logger.info(
        "Seed complete — stations=%s tariffs=%s connectors=%s inserted=%s",
        len(STATIONS),
        len(TARIFFS),
        len(CONNECTORS),
        inserted,
    )
