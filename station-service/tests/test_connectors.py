from decimal import Decimal

from app.models import Connector, ConnectorStatus, Station, Tariff
from app.seed import CONNECTORS, STATIONS, TARIFFS, seed_baseline


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_connector_found(client):
    response = client.get("/connectors/10")
    assert response.status_code == 200
    body = response.json()
    assert body["connectorId"] == 10
    assert body["stationId"] == 1
    assert body["status"] == "AVAILABLE"
    assert "startFee" in body["tariff"]
    assert body["tariff"]["tariffId"] == 5
    assert Decimal(str(body["tariff"]["pricePerKwh"])) == Decimal("8.50")
    assert Decimal(str(body["tariff"]["startFee"])) == Decimal("2.00")
    assert body["tariff"]["currency"] == "TRY"


def test_get_connector_not_found(client):
    response = client.get("/connectors/999")
    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "CONNECTOR_NOT_FOUND"
    assert "message" in body


def test_occupy_release_lifecycle(client):
    occupy = client.post("/connectors/10/occupy")
    assert occupy.status_code == 200
    assert occupy.json() == {"connectorId": 10, "status": "OCCUPIED"}

    conflict = client.post("/connectors/10/occupy")
    assert conflict.status_code == 409
    assert conflict.json()["error"] == "CONNECTOR_OCCUPIED"

    release = client.post("/connectors/10/release")
    assert release.status_code == 200
    assert release.json() == {"connectorId": 10, "status": "AVAILABLE"}

    release_again = client.post("/connectors/10/release")
    assert release_again.status_code == 200
    assert release_again.json() == {"connectorId": 10, "status": "AVAILABLE"}


def test_occupy_unknown_connector(client):
    response = client.post("/connectors/999/occupy")
    assert response.status_code == 404
    assert response.json()["error"] == "CONNECTOR_NOT_FOUND"


def test_release_unknown_connector(client):
    response = client.post("/connectors/999/release")
    assert response.status_code == 404
    assert response.json()["error"] == "CONNECTOR_NOT_FOUND"


def test_list_station_connectors(client):
    response = client.get("/stations/1/connectors")
    assert response.status_code == 200
    body = response.json()
    ids = {item["connectorId"] for item in body}
    assert ids == {10, 11}
    for item in body:
        assert item["status"] == "AVAILABLE"
        assert item["tariff"]["tariffId"] == 5
        assert "startFee" in item["tariff"]


def test_list_station_not_found(client):
    response = client.get("/stations/999/connectors")
    assert response.status_code == 404
    assert response.json()["error"] == "STATION_NOT_FOUND"


def test_seed_does_not_overwrite_occupied_status(client, db_session):
    occupy = client.post("/connectors/10/occupy")
    assert occupy.status_code == 200

    seed_baseline(db_session)

    response = client.get("/connectors/10")
    assert response.status_code == 200
    assert response.json()["status"] == "OCCUPIED"

    assert db_session.get(Connector, 10).status == ConnectorStatus.OCCUPIED
    # Baseline ids remain unique after second seed (SC-007)
    connector_ids = {c["id"] for c in CONNECTORS}
    assert db_session.query(Connector).filter(Connector.id.in_(connector_ids)).count() == len(CONNECTORS)
    assert {c.id for c in db_session.query(Connector).all()} == connector_ids
    assert db_session.query(Station).filter(Station.id == STATIONS[0]["id"]).count() == 1
    assert db_session.query(Tariff).filter(Tariff.id == TARIFFS[0]["id"]).count() == 1
