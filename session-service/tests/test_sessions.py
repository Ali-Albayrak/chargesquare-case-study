from decimal import Decimal

from app.clients.station_client import StationConnector
from app.models import Wallet
from app.wallet import get_balance


def test_start_session_happy_path(client, fake_station, viewer_headers):
    response = client.post(
        "/sessions",
        json={"userId": 7, "connectorId": 10},
        headers=viewer_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ACTIVE"
    assert body["tariffSnapshot"]["tariffId"] == 5
    assert Decimal(str(body["tariffSnapshot"]["pricePerKwh"])) == Decimal("8.50")

    fake_station.get_connector.assert_called_once_with(10)
    fake_station.occupy.assert_called_once_with(10)


def test_connector_occupied(client, fake_station, viewer_headers):
    fake_station.get_connector.return_value = StationConnector(
        connector_id=10,
        status="OCCUPIED",
        tariff_id=5,
        price_per_kwh=Decimal("8.50"),
        start_fee=Decimal("2.00"),
        currency="TRY",
    )
    response = client.post(
        "/sessions",
        json={"userId": 7, "connectorId": 10},
        headers=viewer_headers,
    )
    assert response.status_code == 409
    assert response.json()["error"] == "CONNECTOR_OCCUPIED"
    fake_station.occupy.assert_not_called()


def test_stop_session_happy_path(client, fake_station, db_session, viewer_headers):
    created = client.post(
        "/sessions",
        json={"userId": 7, "connectorId": 10},
        headers=viewer_headers,
    )
    session_id = created.json()["sessionId"]

    stopped = client.post(
        f"/sessions/{session_id}/stop",
        json={"energyKwh": 12.5},
        headers=viewer_headers,
    )
    assert stopped.status_code == 200
    body = stopped.json()
    assert body["status"] == "COMPLETED"
    assert Decimal(str(body["cost"])) == Decimal("108.25")
    assert Decimal(str(body["walletBalanceAfter"])) == Decimal("391.75")
    assert body["endedAt"] is not None

    fake_station.release.assert_called_once_with(10)

    got = client.get(f"/sessions/{session_id}", headers=viewer_headers)
    assert got.status_code == 200
    assert got.json()["status"] == "COMPLETED"
    assert Decimal(str(got.json()["walletBalanceAfter"])) == Decimal("391.75")

    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("391.75")


def test_stop_twice_no_double_charge(client, fake_station, db_session, viewer_headers):
    created = client.post(
        "/sessions",
        json={"userId": 7, "connectorId": 10},
        headers=viewer_headers,
    )
    session_id = created.json()["sessionId"]
    client.post(f"/sessions/{session_id}/stop", json={"energyKwh": 12.5}, headers=viewer_headers)
    fake_station.release.reset_mock()

    again = client.post(
        f"/sessions/{session_id}/stop",
        json={"energyKwh": 12.5},
        headers=viewer_headers,
    )
    assert again.status_code == 409
    assert again.json()["error"] == "SESSION_NOT_ACTIVE"
    fake_station.release.assert_not_called()

    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("391.75")


def test_stop_validation_negative_energy(client, fake_station, viewer_headers):
    created = client.post(
        "/sessions",
        json={"userId": 7, "connectorId": 10},
        headers=viewer_headers,
    )
    session_id = created.json()["sessionId"]
    response = client.post(
        f"/sessions/{session_id}/stop",
        json={"energyKwh": -1},
        headers=viewer_headers,
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "VALIDATION_ERROR"
    assert "energyKwh" in body["message"]
    fake_station.release.assert_not_called()


def test_stop_insufficient_balance(client, fake_station, db_session, viewer_headers):
    wallet = db_session.query(Wallet).filter(Wallet.user_id == 7).one()
    wallet.balance = Decimal("1.00")
    db_session.commit()

    created = client.post(
        "/sessions",
        json={"userId": 7, "connectorId": 10},
        headers=viewer_headers,
    )
    session_id = created.json()["sessionId"]

    response = client.post(
        f"/sessions/{session_id}/stop",
        json={"energyKwh": 12.5},
        headers=viewer_headers,
    )
    assert response.status_code == 409
    assert response.json()["error"] == "INSUFFICIENT_BALANCE"
    fake_station.release.assert_not_called()

    got = client.get(f"/sessions/{session_id}", headers=viewer_headers)
    assert got.json()["status"] == "ACTIVE"

    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("1.00")


def test_wallet_balance_after_frozen_on_session(client, db_session, viewer_headers):
    """Receipt balance is snapshotted at stop; later wallet changes must not rewrite it."""
    first = client.post(
        "/sessions",
        json={"userId": 7, "connectorId": 10},
        headers=viewer_headers,
    )
    first_id = first.json()["sessionId"]
    client.post(f"/sessions/{first_id}/stop", json={"energyKwh": 12.5}, headers=viewer_headers)

    second = client.post(
        "/sessions",
        json={"userId": 7, "connectorId": 11},
        headers=viewer_headers,
    )
    second_id = second.json()["sessionId"]
    client.post(f"/sessions/{second_id}/stop", json={"energyKwh": 0}, headers=viewer_headers)

    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("389.75")

    got_first = client.get(f"/sessions/{first_id}", headers=viewer_headers)
    assert Decimal(str(got_first.json()["walletBalanceAfter"])) == Decimal("391.75")

    listed = client.get("/users/7/sessions", headers=viewer_headers)
    assert listed.status_code == 200
    by_id = {row["sessionId"]: row for row in listed.json()}
    assert Decimal(str(by_id[first_id]["walletBalanceAfter"])) == Decimal("391.75")
    assert Decimal(str(by_id[second_id]["walletBalanceAfter"])) == Decimal("389.75")
