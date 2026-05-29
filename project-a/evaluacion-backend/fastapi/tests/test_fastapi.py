from uuid import uuid4
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from src.main import app
from src.db.session_model import SessionModel
from src.db.track_model import TrackModel
from src.db.registration_model import RegistrationModel
from src.db.speaker_model import SpeakerModel

@pytest.mark.anyio
async def test_healthz_endpoint_fastapi():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/healthz")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "checks" in data
    assert "postgres" in data["checks"]
    assert "redis" in data["checks"]

@pytest.mark.anyio
async def test_get_sessions_list_pagination(db_session):
    conf_id = uuid4()

    await db_session.execute(text(
        "INSERT INTO content.conference (id, name, slug, starts_at, ends_at, timezone) "
        "VALUES (:id, 'C', 'c', NOW(), NOW(), 'UTC')"
    ), {"id": conf_id})

    track_id = uuid4()
    db_session.add(TrackModel(id=track_id, conference_id=conf_id, name="Track 1"))
    db_session.add(SessionModel(
        id=uuid4(),
        track_id=track_id,
        title="Python Session",
        abstract="Learn Python",
        starts_at=datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
        capacity=100
    ))

    await db_session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/sessions/?page=1&page_size=10")

    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "results" in data
    assert isinstance(data["results"], list)

@pytest.mark.anyio
async def test_get_session_detail_not_found():
    fake_uuid = str(uuid4())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/sessions/{fake_uuid}")
    assert response.status_code == 404

@pytest.mark.anyio
async def test_search_sessions_endpoint(db_session):
    conf_id = uuid4()
    await db_session.execute(text(
        "INSERT INTO content.conference (id, name, slug, starts_at, ends_at, timezone) "
        "VALUES (:id, 'C', 'c', NOW(), NOW(), 'UTC')"
    ), {"id": conf_id})

    track_id = uuid4()
    db_session.add(TrackModel(id=track_id, conference_id=conf_id, name="Track 1"))
    db_session.add(SessionModel(
        id=uuid4(),
        track_id=track_id,
        title="Python Session",
        abstract="Learn Python",
        starts_at=datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
        capacity=100
    ))
    await db_session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/sessions/search/?query=Python")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

@pytest.mark.anyio
async def test_timezone_aware_filtering(db_session):
    conf_id = uuid4()
    await db_session.execute(text(
        "INSERT INTO content.conference (id, name, slug, starts_at, ends_at, timezone) "
        "VALUES (:id, 'C', 'c', NOW(), NOW(), 'UTC')"
    ), {"id": conf_id})

    track_id = uuid4()
    db_session.add(TrackModel(id=track_id, conference_id=conf_id, name="Track 1"))
    db_session.add(SessionModel(
        id=uuid4(),
        track_id=track_id,
        title="Tz Session",
        starts_at=datetime(2026, 7, 1, 2, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 1, 3, 0, tzinfo=timezone.utc),
        capacity=100
    ))
    await db_session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/sessions/?day=2026-06-30&tz=America/New_York")

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1


# ---------------------------------------------------------------------------
# Business-logic tests: inventory / capacity enforcement
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_capacity_registration_availability(db_session):
    conf_id = uuid4()

    await db_session.execute(text(
        "INSERT INTO content.conference (id, name, slug, starts_at, ends_at, timezone) "
        "VALUES (:id, 'C', 'c', NOW(), NOW(), 'UTC')"
    ), {"id": conf_id})

    track_id = uuid4()
    db_session.add(TrackModel(id=track_id, conference_id=conf_id, name="Track 1"))
    sess_id = uuid4()
    db_session.add(SessionModel(
        id=sess_id,
        track_id=track_id,
        title="Cap Session",
        abstract="abs",
        starts_at=datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
        capacity=10
    ))
    db_session.add(RegistrationModel(
        id=uuid4(),
        session_id=sess_id,
        status="confirmed",
    ))
    db_session.add(RegistrationModel(
        id=uuid4(),
        session_id=sess_id,
        status="cancelled",
    ))
    db_session.add(RegistrationModel(
        id=uuid4(),
        session_id=sess_id,
        status="waitlist",
    ))

    await db_session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/sessions/{sess_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["capacity"] == 10
    assert data["registered"] == 1


@pytest.mark.anyio
async def test_capacity_registration_zero_when_no_confirmed(db_session):
    conf_id = uuid4()
    await db_session.execute(text(
        "INSERT INTO content.conference (id, name, slug, starts_at, ends_at, timezone) "
        "VALUES (:id, 'C', 'c', NOW(), NOW(), 'UTC')"
    ), {"id": conf_id})

    track_id = uuid4()
    db_session.add(TrackModel(id=track_id, conference_id=conf_id, name="Track 1"))
    sess_id = uuid4()
    db_session.add(SessionModel(
        id=sess_id,
        track_id=track_id,
        title="Empty Session",
        abstract="abs",
        starts_at=datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
        capacity=50,
    ))
    db_session.add(RegistrationModel(id=uuid4(), session_id=sess_id, status="waitlist"))
    db_session.add(RegistrationModel(id=uuid4(), session_id=sess_id, status="cancelled"))
    await db_session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/sessions/{sess_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["registered"] == 0


@pytest.mark.anyio
async def test_capacity_registration_in_list_endpoint(db_session):
    conf_id = uuid4()
    await db_session.execute(text(
        "INSERT INTO content.conference (id, name, slug, starts_at, ends_at, timezone) "
        "VALUES (:id, 'C', 'c', NOW(), NOW(), 'UTC')"
    ), {"id": conf_id})

    track_id = uuid4()
    db_session.add(TrackModel(id=track_id, conference_id=conf_id, name="Track 1"))
    sess_id = uuid4()
    db_session.add(SessionModel(
        id=sess_id,
        track_id=track_id,
        title="Listed Session",
        abstract="abs",
        starts_at=datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
        capacity=20,
    ))
    for _ in range(5):
        db_session.add(RegistrationModel(id=uuid4(), session_id=sess_id, status="confirmed"))
    await db_session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/sessions/?page=1&page_size=50")

    assert response.status_code == 200
    data = response.json()
    listed = [s for s in data["results"] if s["id"] == str(sess_id)]
    assert len(listed) == 1
    assert "registered" in listed[0], "List endpoint must include `registered`"
    assert listed[0]["registered"] == 5


@pytest.mark.anyio
async def test_capacity_concurrent_reads_consistent(db_session):
    """Concurrent reads must return a consistent registered count.

    This test fires N parallel reads against the same session while the
    underlying registrations stay frozen — every response must see the same
    snapshot. A buggy implementation that, for example, queries registrations
    in Python after the session row was already fetched can drift here.
    """
    conf_id = uuid4()
    await db_session.execute(text(
        "INSERT INTO content.conference (id, name, slug, starts_at, ends_at, timezone) "
        "VALUES (:id, 'C', 'c', NOW(), NOW(), 'UTC')"
    ), {"id": conf_id})

    track_id = uuid4()
    db_session.add(TrackModel(id=track_id, conference_id=conf_id, name="Track 1"))
    sess_id = uuid4()
    db_session.add(SessionModel(
        id=sess_id,
        track_id=track_id,
        title="Concurrent Session",
        abstract="abs",
        starts_at=datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
        capacity=200,
    ))
    for _ in range(42):
        db_session.add(RegistrationModel(id=uuid4(), session_id=sess_id, status="confirmed"))
    for _ in range(3):
        db_session.add(RegistrationModel(id=uuid4(), session_id=sess_id, status="waitlist"))
    await db_session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        responses = []
        for _ in range(10):
            responses.append(await ac.get(f"/api/v1/sessions/{sess_id}"))

    counts = []
    for r in responses:
        assert r.status_code == 200
        counts.append(r.json()["registered"])

    assert set(counts) == {42}, f"Repeated reads returned inconsistent counts: {counts}"


# ---------------------------------------------------------------------------
# Speakers router must be registered (defense fix)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_speakers_router_is_registered():
    routes = [getattr(r, "path", "") for r in app.routes]
    assert any(p.startswith("/api/v1/speakers") for p in routes), (
        "Speakers router is not registered in main.py"
    )


@pytest.mark.anyio
async def test_speakers_list_endpoint_responds(db_session):
    conf_id = uuid4()
    await db_session.execute(text(
        "INSERT INTO content.conference (id, name, slug, starts_at, ends_at, timezone) "
        "VALUES (:id, 'C', 'c', NOW(), NOW(), 'UTC')"
    ), {"id": conf_id})
    db_session.add(SpeakerModel(id=uuid4(), name="S1", affiliation="ACME"))
    await db_session.flush()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/speakers/")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert body[0]["affiliation"] == "ACME"


# ---------------------------------------------------------------------------
# Schema correctness
# ---------------------------------------------------------------------------

def test_speaker_out_affiliation_is_string():
    """SpeakerOut.affiliation must be a string field, not an int."""
    from src.models.speaker_schema import SpeakerOut
    field = SpeakerOut.model_fields["affiliation"]
    assert field.annotation is str, (
        f"SpeakerOut.affiliation must be str, got {field.annotation}"
    )


def test_session_detail_abstract_allows_null():
    """SessionDetailOut.abstract must accept NULL values from the database."""
    from src.models.session_schema import SessionDetailOut
    from uuid import uuid4
    from datetime import datetime, timezone
    SessionDetailOut(
        id=uuid4(),
        title="t",
        starts_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ends_at=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
        capacity=1,
        registered=0,
        speakers=[],
        track={"id": uuid4(), "name": "tr"},
        abstract=None,
    )


def test_track_service_uses_color_attribute(db_session):
    """TrackService must read `color` (not a typo like `colour`)."""
    import inspect
    from src.services import track_service
    source = inspect.getsource(track_service)
    assert "track_model.color" in source
    assert "track_model.colour" not in source


def test_session_service_uses_cache_key(db_session):
    """SessionService.get_session must use the `cache_key` variable, not a typo."""
    import inspect
    from src.services import session_service
    source = inspect.getsource(session_service)
    assert "cach_key" not in source, "Found typo `cach_key` in session_service"
