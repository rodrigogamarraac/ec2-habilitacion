from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from models.events import EventDetail, EventListItem, Tier, Venue
from services.events import EventService


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


MOCK_VENUE = Venue(name="Equinoccio", city="La Paz")
MOCK_TIER = Tier(name="General Admission", price=Decimal("50.00"), available=100)
MOCK_EVENT_LIST_ITEM = EventListItem(
    id="evt-123",
    title="Simple Event",
    starts_at=datetime.now(timezone.utc),
    venue=MOCK_VENUE,
    current_price=Decimal("50.00"),
    current_tier_id="tier-1",
    available=100,
    total_capacity=500,
)
MOCK_EVENT_DETAIL = EventDetail(
    id="evt-123",
    title="Simple Event",
    starts_at=datetime.now(timezone.utc),
    venue=MOCK_VENUE,
    description="This is a simple event description",
    current_price=Decimal("50.00"),
    current_tier_id="tier-1",
    available=100,
    total_capacity=500,
    tiers=[MOCK_TIER],
)


def test_healthz_endpoint(client):
    with patch("db.postgres.get_pool") as mock_pg, patch("db.redis.get_redis") as mock_rd:
        mock_conn = AsyncMock()
        mock_pg.return_value.acquire.return_value.__aenter__.return_value = mock_conn

        mock_redis_client = AsyncMock()
        mock_rd.return_value = mock_redis_client

        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["postgres"] == "healthy"
        assert data["redis"] == "healthy"


def test_list_events_endpoint(client):
    with patch.object(EventService, "list_events", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = (1, [MOCK_EVENT_LIST_ITEM])

        response = client.get("/api/v1/events/")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["title"] == "Simple Event"
        assert float(data["results"][0]["current_price"]) == 50.00


def test_search_events_endpoint(client):
    with patch.object(EventService, "list_events", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = (1, [MOCK_EVENT_LIST_ITEM])

        response = client.get("/api/v1/events/search/?query=Simple")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["title"] == "Simple Event"


def test_event_details_found(client):
    with patch.object(EventService, "get_event", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = MOCK_EVENT_DETAIL

        response = client.get("/api/v1/events/evt-123")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "evt-123"
        assert data["title"] == "Simple Event"
        assert data["description"] == "This is a simple event description"
        assert len(data["tiers"]) == 1
        assert data["tiers"][0]["name"] == "General Admission"
        assert data["tiers"][0]["available"] == 100


def test_event_details_not_found(client):
    with patch.object(EventService, "get_event", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None

        response = client.get("/api/v1/events/non-existent-id")
        assert response.status_code == 404
        assert response.json()["detail"] == "event not found"
