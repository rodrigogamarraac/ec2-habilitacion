import re
from pathlib import Path

import pytest

from main import app
from api.v1.models.event import TierOut


REPO_ROOT = Path(__file__).resolve().parents[2]


def _route_paths():
    return {getattr(r, "path", None) for r in app.router.routes}


def test_events_router_is_mounted_at_plural_prefix():
    paths = _route_paths()
    assert "/api/v1/events/" in paths, (
        "Events router must be included with prefix '/api/v1/events'. "
        "Found routes: %s" % sorted(p for p in paths if p)
    )
    assert "/api/v1/events/{event_id}" in paths
    assert "/api/v1/events/search/" in paths


def test_no_singular_event_prefix_leaked():
    paths = _route_paths()
    bad = [p for p in paths if p and p.startswith("/api/v1/event/")]
    assert not bad, (
        "Router prefix must be plural '/api/v1/events', not '/api/v1/event'. "
        "Offending routes: %s" % bad
    )


def test_tier_out_available_is_int():
    field = TierOut.model_fields["available"]
    assert field.annotation is int, (
        "TierOut.available must be typed as int. Got: %r" % field.annotation
    )


def test_monitor_healthz_does_not_reference_undefined_symbols():
    source = (REPO_ROOT / "fastapi" / "src" / "api" / "v1" / "monitor.py").read_text()
    assert '"status": status' not in source, (
        "monitor.healthz returns an undefined 'status' variable. "
        "Replace it with the literal string \"healthy\"."
    )


def test_nginx_api_location_points_to_fastapi_8000():
    nginx_conf = (REPO_ROOT / "nginx" / "nginx.conf").read_text()
    api_block = re.search(r"location\s+/api/\s*\{([^}]*)\}", nginx_conf, re.DOTALL)
    assert api_block, "Could not find 'location /api/' block in nginx.conf"
    body = api_block.group(1)
    proxy_pass = re.search(r"proxy_pass\s+(\S+);", body)
    assert proxy_pass, "location /api/ is missing a proxy_pass directive"
    assert proxy_pass.group(1) == "http://fastapi:8000", (
        "location /api/ must proxy to http://fastapi:8000. Got: %s" % proxy_pass.group(1)
    )
