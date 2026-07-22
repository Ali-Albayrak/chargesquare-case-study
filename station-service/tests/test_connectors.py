from decimal import Decimal


def test_get_connector_found(client):
    response = client.get("/connectors/10")
    assert response.status_code == 200
    body = response.json()
    assert body["connectorId"] == 10
    assert body["status"] == "AVAILABLE"
    assert Decimal(str(body["tariff"]["pricePerKwh"])) == Decimal("8.50")
    assert Decimal(str(body["tariff"]["startFee"])) == Decimal("2.00")
    assert body["tariff"]["currency"] == "TRY"


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


def test_occupy_unknown_connector(client):
    response = client.post("/connectors/999/occupy")
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
        assert "startFee" in item["tariff"]
