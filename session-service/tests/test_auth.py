from decimal import Decimal


def test_login_success(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    body = response.json()
    assert body["tokenType"] == "bearer"
    assert body["role"] == "ADMIN"
    assert body["accessToken"]


def test_login_failure(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["error"] == "UNAUTHORIZED"


def test_read_requires_token(client):
    response = client.get("/users/7/sessions")
    assert response.status_code == 401
    assert response.json()["error"] == "UNAUTHORIZED"


def test_viewer_can_read(client, viewer_headers):
    response = client.get("/users/7/sessions", headers=viewer_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_viewer_forbidden_top_up(client, viewer_headers):
    response = client.post(
        "/users/7/wallet/top-up",
        json={"amount": 10},
        headers=viewer_headers,
    )
    assert response.status_code == 403
    assert response.json()["error"] == "FORBIDDEN"


def test_admin_top_up(client, admin_headers, db_session):
    from app.wallet import get_balance

    response = client.post(
        "/users/7/wallet/top-up",
        json={"amount": 50},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["userId"] == 7
    assert Decimal(str(body["balance"])) == Decimal("550.00")
    assert body["currency"] == "TRY"

    db_session.expire_all()
    assert get_balance(db_session, 7) == Decimal("550.00")


def test_viewer_can_start_and_stop(client, viewer_headers, fake_station):
    started = client.post(
        "/sessions",
        json={"userId": 7, "connectorId": 10},
        headers=viewer_headers,
    )
    assert started.status_code == 201
    fake_station.occupy.assert_called_once_with(10)

    session_id = started.json()["sessionId"]
    stopped = client.post(
        f"/sessions/{session_id}/stop",
        json={"energyKwh": 1},
        headers=viewer_headers,
    )
    assert stopped.status_code == 200
    fake_station.release.assert_called_once_with(10)
