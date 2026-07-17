import os
from decimal import Decimal
from unittest.mock import MagicMock

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["STATION_SERVICE_URL"] = "http://station.test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.clients.station_client import StationConnector
from app.db import Base, engine, get_db
from app.main import app
from app.seed import seed_baseline
from app.services import session_service

TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def fake_station():
    client = MagicMock()
    client.get_connector.return_value = StationConnector(
        connector_id=10,
        status="AVAILABLE",
        tariff_id=5,
        price_per_kwh=Decimal("8.50"),
        start_fee=Decimal("2.00"),
        currency="TRY",
    )
    client.occupy.return_value = None
    client.release.return_value = None
    return client


@pytest.fixture()
def client(fake_station):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        seed_baseline(db)
    finally:
        db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    original_start = session_service.start_session
    original_stop = session_service.stop_session

    def start_with_fake(db, request, client=None):
        return original_start(db, request, client=fake_station)

    def stop_with_fake(db, session_id, request, client=None):
        return original_stop(db, session_id, request, client=fake_station)

    session_service.start_session = start_with_fake  # type: ignore[method-assign]
    session_service.stop_session = stop_with_fake  # type: ignore[method-assign]
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    session_service.start_session = original_start  # type: ignore[method-assign]
    session_service.stop_session = original_stop  # type: ignore[method-assign]
    app.dependency_overrides.clear()
