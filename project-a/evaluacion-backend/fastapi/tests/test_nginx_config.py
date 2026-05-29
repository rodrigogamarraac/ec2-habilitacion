"""Static checks on the nginx configuration.

These tests guard the nginx defense fixes. They do NOT spin up nginx; they
read the file and verify the structural properties the student must restore.
"""
import os
import re

NGINX_CONF = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "nginx", "nginx.conf",
)


def _read_conf() -> str:
    with open(NGINX_CONF, "r", encoding="utf-8") as f:
        return f.read()


def test_nginx_directives_terminated_with_semicolon():
    """Every simple directive (non-block) must end with `;`."""
    conf = _read_conf()
    bad = []
    for lineno, raw in enumerate(conf.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.endswith("{") or line.endswith("}"):
            continue
        if not line.endswith(";"):
            bad.append((lineno, raw.rstrip()))
    assert not bad, f"Lines missing trailing ';': {bad}"


def test_nginx_api_location_proxies_to_fastapi_port_8001():
    """The /api/ location must proxy to fastapi:8001 (not :8000)."""
    conf = _read_conf()

    api_block = re.search(
        r"location\s+/api/\s*\{(?P<body>[^}]*)\}",
        conf,
        re.DOTALL,
    )
    assert api_block, "Missing `location /api/ { ... }` block"

    body = api_block.group("body")
    assert re.search(r"fastapi\s*:\s*8001", body), (
        "The /api/ block must proxy to fastapi:8001"
    )
    assert not re.search(r"fastapi\s*:\s*8000", body), (
        "The /api/ block points to the wrong port (fastapi:8000)"
    )


def test_nginx_admin_location_proxies_to_django_port_8000():
    conf = _read_conf()
    admin_block = re.search(
        r"location\s+/admin/\s*\{(?P<body>[^}]*)\}",
        conf,
        re.DOTALL,
    )
    assert admin_block, "Missing `location /admin/ { ... }` block"
    assert re.search(r"django\s*:\s*8000", admin_block.group("body"))
