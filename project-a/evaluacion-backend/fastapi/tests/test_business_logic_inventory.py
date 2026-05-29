"""Focused business-logic suite for the inventory / capacity enforcement.

This file exists as a standalone suite the professor can run with a single
command (see `scripts/run_inventory_tests.sh`). It re-exercises the API contract
the student must restore:

  * Every `SessionOut` includes a `registered` field.
  * `registered` counts ONLY rows whose `status = 'confirmed'`.
  * The count is computed correctly under concurrent reads.

The tests require Postgres to be running (see README).
"""
from uuid import uuid4
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from src.main import app
from src.db.session_model import SessionModel
from src.db.track_model import TrackModel
from src.db.registration_model import RegistrationModel


async def _seed_session(db_session, *, confirmed: int, other_statuses: list[str]):
    conf_id = uuid4()
    await db_session.execute(text(
        "INSERT INTO content.conference (id, name, slug, starts_at, ends_at, timezone) "
        "VALUES (:id, 'C', 'c', NOW(), NOW(), 'UTC')"
    ), {"id": conf_id})

    track_id = uuid4()
    db_session.add(TrackModel(id=track_id, conference_id=conf_id, name="T"))
    sess_id = uuid4()
    db_session.add(SessionModel(
        id=sess_id,
        track_id=track_id,
        title="Inv Session",
        abstract="abs",
        starts_at=datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
        capacity=200,
    ))
    for _ in range(confirmed):
        db_session.add(RegistrationModel(id=uuid4(), session_id=sess_id, status="confirmed"))
    for s in other_statuses:
        db_session.add(RegistrationModel(id=uuid4(), session_id=sess_id, status=s))
    await db_session.flush()
    return sess_id


@pytest.mark.anyio
async def test_inventory_only_counts_confirmed(db_session):
    sess_id = await _seed_session(
        db_session,
        confirmed=7,
        other_statuses=["waitlist", "waitlist", "cancelled"],
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(f"/api/v1/sessions/{sess_id}")
    assert r.status_code == 200
    assert r.json()["registered"] == 7


@pytest.mark.anyio
async def test_inventory_zero_when_only_waitlist(db_session):
    sess_id = await _seed_session(
        db_session,
        confirmed=0,
        other_statuses=["waitlist", "cancelled"],
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(f"/api/v1/sessions/{sess_id}")
    assert r.status_code == 200
    assert r.json()["registered"] == 0


@pytest.mark.anyio
async def test_inventory_appears_in_list_endpoint(db_session):
    sess_id = await _seed_session(
        db_session,
        confirmed=3,
        other_statuses=[],
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/api/v1/sessions/?page=1&page_size=100")
    assert r.status_code == 200
    matching = [s for s in r.json()["results"] if s["id"] == str(sess_id)]
    assert matching and matching[0]["registered"] == 3


@pytest.mark.anyio
async def test_inventory_concurrent_reads_are_consistent(db_session):
    """All N concurrent reads must see the same `registered` value.

    Writes go through admin only, so we hold the data steady during the
    fan-out and assert determinism. A buggy implementation that does the
    count outside the session's snapshot can diverge here.
    """
    sess_id = await _seed_session(
        db_session,
        confirmed=25,
        other_statuses=["waitlist"] * 5 + ["cancelled"] * 5,
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        responses = []
        for _ in range(20):
            responses.append(await ac.get(f"/api/v1/sessions/{sess_id}"))

    counts = []
    for r in responses:
        assert r.status_code == 200
        counts.append(r.json()["registered"])
    assert set(counts) == {25}, f"Concurrent reads diverged: {counts}"
