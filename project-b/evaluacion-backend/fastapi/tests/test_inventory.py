import asyncio
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from services.events import EventService
from services.events.interfaces import (
    CacheInterface,
    EventRepositoryInterface,
    EventSearchInterface,
)


class _NullCache(CacheInterface):
    async def get(self, key):
        return None

    async def set(self, key, value, ex=None):
        return None


class _FakeRepository(EventRepositoryInterface):
    def __init__(self, events_page, event_detail=None, tiers=None):
        self._events_page = events_page
        self._event_detail = event_detail
        self._tiers = tiers or []
        self.page_calls = 0
        self.detail_calls = 0
        self.tier_calls = 0

    async def get_events_count(self, query=None):
        return len(self._events_page)

    async def get_events_page(self, page, page_size, query=None, sort="date", request_time=None):
        self.page_calls += 1
        await asyncio.sleep(0)
        return [dict(r) for r in self._events_page]

    async def get_event_detail(self, event_id):
        self.detail_calls += 1
        await asyncio.sleep(0)
        return dict(self._event_detail) if self._event_detail else None

    async def get_event_tiers(self, event_id, request_time):
        self.tier_calls += 1
        await asyncio.sleep(0)
        return [dict(t) for t in self._tiers]


class _FakeSearch(EventSearchInterface):
    def __init__(self, repository):
        self.repository = repository

    async def search_events(self, query, page, page_size, sort="date", request_time=None):
        total = await self.repository.get_events_count(query=query)
        results = await self.repository.get_events_page(
            page=page, page_size=page_size, query=query, sort=sort, request_time=request_time
        )
        return total, results


@pytest.fixture
def request_time():
    return datetime(2026, 5, 29, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def list_row():
    return {
        "id": "evt-1",
        "title": "Concert",
        "starts_at": datetime(2026, 7, 10, 21, 0, 0, tzinfo=timezone.utc),
        "venue_name": "Teatro",
        "venue_city": "La Paz",
        "current_price": Decimal("75.50"),
        "current_tier_id": "tier-general",
        "total_quantity": 500,
        "sold": 80,
        "total_capacity": 500,
    }


@pytest.fixture
def detail_row():
    return {
        "id": "evt-1",
        "title": "Concert",
        "description": "Festival",
        "starts_at": datetime(2026, 7, 10, 21, 0, 0, tzinfo=timezone.utc),
        "venue_name": "Teatro",
        "venue_city": "La Paz",
        "total_capacity": 500,
    }


@pytest.fixture
def tier_rows():
    return [
        {
            "id": "tier-general",
            "name": "General",
            "price": Decimal("75.50"),
            "total_quantity": 300,
            "sold": 30,
        },
        {
            "id": "tier-vip",
            "name": "VIP",
            "price": Decimal("250.00"),
            "total_quantity": 120,
            "sold": 50,
        },
    ]


def _build_service(repository):
    return EventService(repository, _NullCache(), _FakeSearch(repository))


@pytest.mark.asyncio
async def test_list_events_computes_available(list_row, request_time):
    repo = _FakeRepository(events_page=[list_row])
    service = _build_service(repo)

    total, results = await service.list_events(
        page=1, page_size=20, query=None, sort="date", request_time=request_time
    )

    assert total == 1
    assert len(results) == 1
    item = results[0]
    assert item.total_capacity == 500
    assert item.available == 420, (
        "list_events must compute available as total_quantity - sold (500 - 80 = 420). "
        "Got %s" % item.available
    )


@pytest.mark.asyncio
async def test_get_event_aggregates_tier_availability(detail_row, tier_rows, request_time):
    repo = _FakeRepository(events_page=[], event_detail=detail_row, tiers=tier_rows)
    service = _build_service(repo)

    event = await service.get_event("evt-1", request_time=request_time)

    assert event is not None
    assert event.total_capacity == 500
    assert event.available == 340, (
        "get_event must aggregate per-tier (total_quantity - sold). "
        "Tiers: (300-30) + (120-50) = 340. Got %s" % event.available
    )
    tier_avail = {t.name: t.available for t in event.tiers}
    assert tier_avail == {"General": 270, "VIP": 70}


@pytest.mark.asyncio
async def test_inventory_never_negative_when_sold_exceeds_quantity(request_time):
    row = {
        "id": "evt-2",
        "title": "Sold Out",
        "starts_at": datetime(2026, 7, 10, 21, 0, 0, tzinfo=timezone.utc),
        "venue_name": "Teatro",
        "venue_city": "La Paz",
        "current_price": Decimal("10.00"),
        "current_tier_id": "tier-1",
        "total_quantity": 100,
        "sold": 150,
        "total_capacity": 100,
    }
    repo = _FakeRepository(events_page=[row])
    service = _build_service(repo)

    _, results = await service.list_events(
        page=1, page_size=20, query=None, sort="date", request_time=request_time
    )

    assert results[0].available == 0, "available must be clamped at 0, never negative"


@pytest.mark.asyncio
async def test_concurrent_reads_return_consistent_inventory(list_row, request_time):
    repo = _FakeRepository(events_page=[list_row])
    service = _build_service(repo)

    async def one_read():
        _, results = await service.list_events(
            page=1, page_size=20, query=None, sort="date", request_time=request_time
        )
        return results[0].available

    values = await asyncio.gather(*[one_read() for _ in range(50)])

    assert len(values) == 50
    assert all(v == 420 for v in values), (
        "All concurrent readers must see the same correctly-computed availability. "
        "Got distinct values: %s" % set(values)
    )


@pytest.mark.asyncio
async def test_concurrent_detail_reads_return_consistent_inventory(detail_row, tier_rows, request_time):
    repo = _FakeRepository(events_page=[], event_detail=detail_row, tiers=tier_rows)
    service = _build_service(repo)

    async def one_read():
        event = await service.get_event("evt-1", request_time=request_time)
        return event.available, tuple((t.name, t.available) for t in event.tiers)

    values = await asyncio.gather(*[one_read() for _ in range(50)])

    assert all(v[0] == 340 for v in values)
    assert all(dict(v[1]) == {"General": 270, "VIP": 70} for v in values)
