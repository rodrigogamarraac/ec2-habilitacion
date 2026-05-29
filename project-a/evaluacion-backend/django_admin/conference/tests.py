import uuid
from datetime import datetime, timezone
import pytest
from django.core.management import call_command
from django.test import Client
from conference.models import Conference, Registration, Session, Speaker, Track

def make_conference(**kwargs):
    defaults = dict(
        name="Test Conf",
        slug=f"test-conf-{uuid.uuid4().hex[:8]}",
        starts_at=datetime(2026, 7, 1, 9, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 5, 18, tzinfo=timezone.utc),
        timezone="UTC",
    )

    defaults.update(kwargs)
    return Conference.objects.create(**defaults)


def make_track(conference, **kwargs):
    defaults = dict(name="Backend", conference=conference)
    defaults.update(kwargs)

    return Track.objects.create(**defaults)


def make_session(track, **kwargs):
    defaults = dict(
        track=track,
        title="Intro to Python",
        abstract="Learn Python basics",
        starts_at=datetime(2026, 7, 1, 10, tzinfo=timezone.utc),
        ends_at=datetime(2026, 7, 1, 11, tzinfo=timezone.utc),
        capacity=50,
    )

    defaults.update(kwargs)
    return Session.objects.create(**defaults)


@pytest.mark.django_db
def test_conference_has_uuid_pk():
    conf = make_conference()
    assert isinstance(conf.pk, uuid.UUID)


@pytest.mark.django_db
def test_conference_has_timestamps():
    conf = make_conference()
    assert conf.created is not None
    assert conf.modified is not None


@pytest.mark.django_db
def test_session_capacity_stored():
    conf = make_conference()
    track = make_track(conf)
    session = make_session(track, capacity=30)
    session.refresh_from_db()
    assert session.capacity == 30


@pytest.mark.django_db
def test_registration_status_choices():
    conf = make_conference()
    track = make_track(conf)
    session = make_session(track)

    reg = Registration.objects.create(
        session=session,
        user_email="alice@example.com",
        status=Registration.Status.CONFIRMED,
    )

    assert reg.status == "confirmed"
    reg.status = Registration.Status.WAITLIST
    reg.save()
    reg.refresh_from_db()
    assert reg.status == "waitlist"


@pytest.mark.django_db
def test_track_belongs_to_conference():
    conf = make_conference()
    track = make_track(conf, name="Frontend")

    assert track.conference_id == conf.pk


@pytest.mark.django_db
def test_session_speaker_many_to_many():
    conf = make_conference()
    track = make_track(conf)
    session = make_session(track)
    speaker1 = Speaker.objects.create(name="Bob", affiliation="ACME")
    speaker2 = Speaker.objects.create(name="Carol", affiliation="ACME")
    session.speakers.add(speaker1, speaker2)

    assert session.speakers.count() == 2


@pytest.mark.django_db
def test_registration_cascade_delete():
    conf = make_conference()
    track = make_track(conf)
    session = make_session(track)

    Registration.objects.create(
        session=session,
        user_email="x@x.com",
        status=Registration.Status.CONFIRMED,
    )
    
    assert Registration.objects.filter(session=session).count() == 1
    session.delete()
    assert Registration.objects.filter(session_id=session.pk).count() == 0


@pytest.mark.django_db
def test_healthz_endpoint_returns_ok():
    client = Client()
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.django_db
def test_seed_data_idempotent():
    call_command("seed_data", verbosity=0)
    call_command("seed_data", verbosity=0)
    assert Conference.objects.filter(slug="djangocon-2026").count() == 1
    assert Session.objects.count() == 300
