import asyncio
import uuid
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from models.restaurant import Restaurant
from models.table_type import TableType
from models.reservation import Reservation


class FakeRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def setex(self, key, ttl, value):
        self.store[key] = value


@pytest_asyncio.fixture
async def session_maker():
    from sqlalchemy import event
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine.sync_engine, "connect")
    def _attach_content_schema(dbapi_conn, _):
        dbapi_conn.execute("ATTACH DATABASE ':memory:' AS content")

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield maker
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def seeded(session_maker):
    rest_id = uuid.uuid4()
    table_ids = [uuid.uuid4() for _ in range(3)]
    now = datetime(2026, 6, 10, 18, 0, 0)

    async with session_maker() as s:
        s.add(Restaurant(
            id=rest_id, name="R", description="d", address="a",
            created_at=now, updated_at=now,
        ))
        # capacities: 2, 4, 6
        for tid, cap, ttype in zip(table_ids, [2, 4, 6], ["shared", "private", "vip"]):
            s.add(TableType(
                id=tid, restaurant_id=rest_id, name=f"T{cap}",
                type=ttype, capacity=cap, description="d", price=10.0,
                created_at=now, updated_at=now,
            ))
        # reserve the 4-seat table at the requested slot
        s.add(Reservation(
            id=uuid.uuid4(), restaurant_id=rest_id,
            table_type_id=table_ids[1],
            starts_at=now, ends_at=now + timedelta(minutes=30),
            status="confirmed", created_at=now, updated_at=now,
        ))
        await s.commit()
    return {"rest_id": rest_id, "table_ids": table_ids, "now": now}


@pytest.mark.asyncio
async def test_reserved_table_is_excluded(session_maker, seeded):
    from services.getAvailability import GetAvailability
    async with session_maker() as s:
        svc = GetAvailability(s, FakeRedis())
        result = await svc.get_availability(
            date=seeded["now"].date(),
            time=seeded["now"].time(),
            party=2,
            table_type=None,
            tz="UTC",
        )
    returned_types = {slot.table_type for slot in result}
    assert "private" not in returned_types, (
        "Reserved table_type 'private' must NOT appear in availability"
    )
    assert {"shared", "vip"}.issubset(returned_types)


@pytest.mark.asyncio
async def test_party_size_filter(session_maker, seeded):
    from services.getAvailability import GetAvailability
    async with session_maker() as s:
        svc = GetAvailability(s, FakeRedis())
        result = await svc.get_availability(
            date=seeded["now"].date(),
            time=seeded["now"].time(),
            party=5,
            table_type=None,
            tz="UTC",
        )
    for slot in result:
        assert slot.seats >= 5


@pytest.mark.asyncio
async def test_overlapping_reservation_blocks_slot(session_maker, seeded):
    from services.getAvailability import GetAvailability
    overlap_time = seeded["now"] + timedelta(minutes=15)
    async with session_maker() as s:
        svc = GetAvailability(s, FakeRedis())
        result = await svc.get_availability(
            date=overlap_time.date(),
            time=overlap_time.time(),
            party=2,
            table_type=None,
            tz="UTC",
        )
    returned_types = {slot.table_type for slot in result}
    assert "private" not in returned_types


@pytest.mark.asyncio
async def test_non_overlapping_slot_returns_all(session_maker, seeded):
    from services.getAvailability import GetAvailability
    later = seeded["now"] + timedelta(hours=2)
    async with session_maker() as s:
        svc = GetAvailability(s, FakeRedis())
        result = await svc.get_availability(
            date=later.date(),
            time=later.time(),
            party=2,
            table_type=None,
            tz="UTC",
        )
    returned_types = {slot.table_type for slot in result}
    assert {"shared", "private", "vip"}.issubset(returned_types)


@pytest.mark.asyncio
async def test_concurrent_reads_are_consistent(session_maker, seeded):
    from services.getAvailability import GetAvailability
    fake = FakeRedis()

    async def one_call():
        async with session_maker() as s:
            svc = GetAvailability(s, fake)
            slots = await svc.get_availability(
                date=seeded["now"].date(),
                time=seeded["now"].time(),
                party=2,
                table_type=None,
                tz="UTC",
            )
            return tuple(sorted(slot.table_type for slot in slots))

    results = await asyncio.gather(*[one_call() for _ in range(20)])
    assert len(set(results)) == 1, (
        f"Concurrent reads returned inconsistent results: {set(results)}"
    )
    assert "private" not in results[0]


@pytest.mark.asyncio
async def test_cancelled_reservations_do_not_block(session_maker, seeded):
    from services.getAvailability import GetAvailability
    now = seeded["now"]
    rest_id = seeded["rest_id"]
    new_table_id = uuid.uuid4()
    async with session_maker() as s:
        s.add(TableType(
            id=new_table_id, restaurant_id=rest_id, name="Tcanc",
            type="bar", capacity=2, description="d", price=10.0,
            created_at=now, updated_at=now,
        ))
        s.add(Reservation(
            id=uuid.uuid4(), restaurant_id=rest_id,
            table_type_id=new_table_id,
            starts_at=now, ends_at=now + timedelta(minutes=30),
            status="cancelled", created_at=now, updated_at=now,
        ))
        await s.commit()
    async with session_maker() as s:
        svc = GetAvailability(s, FakeRedis())
        result = await svc.get_availability(
            date=now.date(), time=now.time(), party=2,
            table_type=None, tz="UTC",
        )
    returned_types = {slot.table_type for slot in result}
    assert "bar" in returned_types, (
        "Cancelled reservations must NOT block availability"
    )
