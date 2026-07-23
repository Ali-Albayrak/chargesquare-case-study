from decimal import Decimal


def test_get_connector_found(client, viewer_headers):
    response = client.get("/connectors/10", headers=viewer_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["connectorId"] == 10
    assert body["status"] == "AVAILABLE"
    assert Decimal(str(body["tariff"]["pricePerKwh"])) == Decimal("8.50")
    assert Decimal(str(body["tariff"]["startFee"])) == Decimal("2.00")
    assert body["tariff"]["currency"] == "TRY"


def test_occupy_release_lifecycle(client, admin_headers):
    occupy = client.post("/connectors/10/occupy", headers=admin_headers)
    assert occupy.status_code == 200
    assert occupy.json() == {"connectorId": 10, "status": "OCCUPIED"}

    conflict = client.post("/connectors/10/occupy", headers=admin_headers)
    assert conflict.status_code == 409
    assert conflict.json()["error"] == "CONNECTOR_OCCUPIED"

    release = client.post("/connectors/10/release", headers=admin_headers)
    assert release.status_code == 200
    assert release.json() == {"connectorId": 10, "status": "AVAILABLE"}


def test_occupy_unknown_connector(client, admin_headers):
    response = client.post("/connectors/999/occupy", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["error"] == "CONNECTOR_NOT_FOUND"


def test_list_station_connectors(client, viewer_headers):
    response = client.get("/stations/1/connectors", headers=viewer_headers)
    assert response.status_code == 200
    body = response.json()
    ids = {item["connectorId"] for item in body}
    assert ids == {10, 11}
    for item in body:
        assert item["status"] == "AVAILABLE"
        assert "startFee" in item["tariff"]


def test_read_requires_token(client):
    response = client.get("/connectors/10")
    assert response.status_code == 401
    assert response.json()["error"] == "UNAUTHORIZED"


def test_viewer_forbidden_occupy(client, viewer_headers):
    response = client.post("/connectors/10/occupy", headers=viewer_headers)
    assert response.status_code == 403
    assert response.json()["error"] == "FORBIDDEN"
