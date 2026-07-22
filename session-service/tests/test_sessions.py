from decimal import Decimal
from unittest.mock import MagicMock

from app.clients.station_client import StationConnector
from app.errors import AppError
from app.models import Wallet
from app.seed import WALLETS, seed_baseline
from app.wallet import get_balance


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_start_session_happy_path(client, fake_station, db_session):
    response = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    assert response.status_code == 201
    body = response.json()
    assert body["userId"] == 7
    assert body["connectorId"] == 10
    assert body["status"] == "ACTIVE"
    assert "startedAt" in body
    assert body["tariffSnapshot"]["tariffId"] == 5
    assert Decimal(str(body["tariffSnapshot"]["pricePerKwh"])) == Decimal("8.50")
    assert Decimal(str(body["tariffSnapshot"]["startFee"])) == Decimal("2.00")
    assert body["tariffSnapshot"]["currency"] == "TRY"
    assert body["currency"] == "TRY"

    fake_station.get_connector.assert_called_once_with(10)
    fake_station.occupy.assert_called_once_with(10)

    db_session.expire_all()
    balance = get_balance(db_session, 7)
    assert balance == Decimal("500.00")


def test_validation_error_missing_fields(client, fake_station):
    response = client.post("/sessions", json={})
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert "userId" in body["message"]
    assert "connectorId" in body["message"]
    fake_station.get_connector.assert_not_called()
    fake_station.occupy.assert_not_called()


def test_user_not_found_does_not_call_station(client, fake_station):
    response = client.post("/sessions", json={"userId": 999, "connectorId": 10})
    assert response.status_code == 404
    assert response.json()["error"] == "USER_NOT_FOUND"
    fake_station.get_connector.assert_not_called()
    fake_station.occupy.assert_not_called()


def test_connector_not_found(client, fake_station):
    fake_station.get_connector.side_effect = AppError(
        status_code=404,
        error="CONNECTOR_NOT_FOUND",
        message="Connector 10 was not found",
    )
    response = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    assert response.status_code == 404
    assert response.json()["error"] == "CONNECTOR_NOT_FOUND"
    fake_station.occupy.assert_not_called()


def test_connector_occupied(client, fake_station):
    fake_station.get_connector.return_value = StationConnector(
        connector_id=10,
        status="OCCUPIED",
        tariff_id=5,
        price_per_kwh=Decimal("8.50"),
        start_fee=Decimal("2.00"),
        currency="TRY",
    )
    response = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    assert response.status_code == 409
    assert response.json()["error"] == "CONNECTOR_OCCUPIED"
    fake_station.occupy.assert_not_called()


def test_station_unreachable(client, fake_station):
    fake_station.get_connector.side_effect = AppError(
        status_code=503,
        error="STATION_UNAVAILABLE",
        message="Station Service is unreachable",
    )
    response = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    assert response.status_code == 503
    assert response.json()["error"] == "STATION_UNAVAILABLE"


def test_get_session_and_not_found(client):
    created = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    session_id = created.json()["sessionId"]

    found = client.get(f"/sessions/{session_id}")
    assert found.status_code == 200
    assert found.json()["status"] == "ACTIVE"
    assert found.json()["tariffSnapshot"]["tariffId"] == 5

    missing = client.get("/sessions/99999")
    assert missing.status_code == 404
    assert missing.json()["error"] == "SESSION_NOT_FOUND"


def test_seed_does_not_overwrite_wallet_balance(client, db_session):
    wallet = db_session.query(Wallet).filter(Wallet.user_id == 7).one()
    wallet.balance = Decimal("100.00")
    db_session.commit()

    seed_baseline(db_session)

    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("100.00")
    assert db_session.query(Wallet).filter(Wallet.user_id == WALLETS[0]["user_id"]).count() == 1


def test_stop_session_happy_path(client, fake_station, db_session):
    created = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    session_id = created.json()["sessionId"]

    stopped = client.post(f"/sessions/{session_id}/stop", json={"energyKwh": 12.5})
    assert stopped.status_code == 200
    body = stopped.json()
    assert body["status"] == "COMPLETED"
    assert Decimal(str(body["energyKwh"])) == Decimal("12.5")
    assert Decimal(str(body["cost"])) == Decimal("108.25")
    assert Decimal(str(body["walletBalanceAfter"])) == Decimal("391.75")
    assert body["endedAt"] is not None
    assert body["currency"] == "TRY"

    fake_station.release.assert_called_once_with(10)
    fake_station.get_connector.assert_called_once_with(10)  # start only

    got = client.get(f"/sessions/{session_id}")
    assert got.status_code == 200
    assert got.json()["status"] == "COMPLETED"
    assert Decimal(str(got.json()["cost"])) == Decimal("108.25")
    assert Decimal(str(got.json()["walletBalanceAfter"])) == Decimal("391.75")

    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("391.75")


def test_stop_twice_no_double_charge(client, fake_station, db_session):
    created = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    session_id = created.json()["sessionId"]
    client.post(f"/sessions/{session_id}/stop", json={"energyKwh": 12.5})
    fake_station.release.reset_mock()

    again = client.post(f"/sessions/{session_id}/stop", json={"energyKwh": 12.5})
    assert again.status_code == 409
    assert again.json()["error"] == "SESSION_NOT_ACTIVE"
    fake_station.release.assert_not_called()

    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("391.75")


def test_stop_session_not_found(client, fake_station):
    response = client.post("/sessions/99999/stop", json={"energyKwh": 1})
    assert response.status_code == 404
    assert response.json()["error"] == "SESSION_NOT_FOUND"
    fake_station.release.assert_not_called()


def test_stop_validation_negative_energy(client, fake_station):
    created = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    session_id = created.json()["sessionId"]
    response = client.post(f"/sessions/{session_id}/stop", json={"energyKwh": -1})
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert "energyKwh" in body["message"]
    fake_station.release.assert_not_called()


def test_stop_validation_missing_energy(client, fake_station):
    created = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    session_id = created.json()["sessionId"]
    response = client.post(f"/sessions/{session_id}/stop", json={})
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert "energyKwh" in body["message"]
    fake_station.release.assert_not_called()


def test_stop_insufficient_balance(client, fake_station, db_session):
    wallet = db_session.query(Wallet).filter(Wallet.user_id == 7).one()
    wallet.balance = Decimal("1.00")
    db_session.commit()

    created = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    session_id = created.json()["sessionId"]

    response = client.post(f"/sessions/{session_id}/stop", json={"energyKwh": 12.5})
    assert response.status_code == 409
    assert response.json()["error"] == "INSUFFICIENT_BALANCE"
    fake_station.release.assert_not_called()

    got = client.get(f"/sessions/{session_id}")
    assert got.json()["status"] == "ACTIVE"

    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("1.00")


def test_stop_zero_energy(client, fake_station, db_session):
    created = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    session_id = created.json()["sessionId"]

    stopped = client.post(f"/sessions/{session_id}/stop", json={"energyKwh": 0})
    assert stopped.status_code == 200
    assert Decimal(str(stopped.json()["cost"])) == Decimal("2.00")
    assert Decimal(str(stopped.json()["walletBalanceAfter"])) == Decimal("498.00")

    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("498.00")


def test_stop_station_release_unavailable(client, fake_station, db_session):
    created = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    session_id = created.json()["sessionId"]
    fake_station.release.side_effect = AppError(
        status_code=503,
        error="STATION_UNAVAILABLE",
        message="Station Service is unreachable",
    )

    response = client.post(f"/sessions/{session_id}/stop", json={"energyKwh": 12.5})
    assert response.status_code == 503
    assert response.json()["error"] == "STATION_UNAVAILABLE"

    # Known gap: debit/COMPLETED may already be persisted before release fails
    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("391.75")
    got = client.get(f"/sessions/{session_id}")
    assert got.json()["status"] == "COMPLETED"


def test_list_user_sessions(client):
    created = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    session_id = created.json()["sessionId"]
    client.post(f"/sessions/{session_id}/stop", json={"energyKwh": 12.5})

    listed = client.get("/users/7/sessions")
    assert listed.status_code == 200
    body = listed.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["sessionId"] == session_id
    assert body[0]["status"] == "COMPLETED"
    assert Decimal(str(body[0]["walletBalanceAfter"])) == Decimal("391.75")

    empty = client.get("/users/999/sessions")
    assert empty.status_code == 200
    assert empty.json() == []


def test_wallet_balance_after_frozen_on_session(client, fake_station, db_session):
    """Receipt balance is snapshotted at stop; later wallet changes must not rewrite it."""
    first = client.post("/sessions", json={"userId": 7, "connectorId": 10})
    first_id = first.json()["sessionId"]
    client.post(f"/sessions/{first_id}/stop", json={"energyKwh": 12.5})

    # Second session on another connector further debits the live wallet.
    second = client.post("/sessions", json={"userId": 7, "connectorId": 11})
    second_id = second.json()["sessionId"]
    client.post(f"/sessions/{second_id}/stop", json={"energyKwh": 0})

    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("389.75")

    got_first = client.get(f"/sessions/{first_id}")
    assert Decimal(str(got_first.json()["walletBalanceAfter"])) == Decimal("391.75")

    listed = client.get("/users/7/sessions")
    by_id = {row["sessionId"]: row for row in listed.json()}
    assert Decimal(str(by_id[first_id]["walletBalanceAfter"])) == Decimal("391.75")
    assert Decimal(str(by_id[second_id]["walletBalanceAfter"])) == Decimal("389.75")
