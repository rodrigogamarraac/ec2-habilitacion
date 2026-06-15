from fastapi.testclient import TestClient

from app.main import EVENTS, app

client = TestClient(app)


def test_healthz_returns_ok():
    response = client.get("/api/v1/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_events_returns_ticket_availability():
    response = client.get("/api/v1/events")

    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    assert "available" in events[0]
    assert "sold_out" in events[0]


def test_get_event_detail_returns_ticket_tiers():
    response = client.get("/api/v1/events/neon-nights")

    assert response.status_code == 200
    event = response.json()
    assert event["id"] == "neon-nights"
    assert len(event["tiers"]) == 3
    assert event["available"] > 0


def test_create_order_decreases_available_tickets():
    before = EVENTS["neon-nights"].tiers["general"].available

    response = client.post(
        "/api/v1/orders",
        json={
            "event_id": "neon-nights",
            "ticket_type": "general",
            "quantity": 2,
            "customer_name": "Rodrigo Gamarra",
            "customer_email": "rodrigo@example.com",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["quantity"] == 2
    assert body["remaining"] == before - 2


def test_create_order_rejects_when_capacity_is_not_enough():
    response = client.post(
        "/api/v1/orders",
        json={
            "event_id": "neon-nights",
            "ticket_type": "backstage",
            "quantity": 10,
            "customer_name": "Rodrigo Gamarra",
            "customer_email": "rodrigo@example.com",
        },
    )

    assert response.status_code == 409
    assert "Not enough tickets" in response.json()["detail"]
