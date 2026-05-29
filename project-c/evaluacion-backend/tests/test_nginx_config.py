import re
from pathlib import Path

NGINX = Path(__file__).resolve().parent.parent / "nginx" / "nginx.conf"


def _read():
    return NGINX.read_text()


def test_all_directive_lines_end_with_semicolon():
    text = _read()
    offenders = []
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.endswith("{") or line.endswith("}") or line.endswith(";"):
            continue
        offenders.append((i, raw))
    assert not offenders, (
        "Lines missing semicolons:\n" + "\n".join(f"  L{i}: {l}" for i, l in offenders)
    )


def test_api_proxy_pass_targets_correct_upstream():
    text = _read()
    match = re.search(r"location\s+/api/v1/\s*\{[^}]*?proxy_pass\s+([^;\s]+)", text, re.DOTALL)
    assert match, "/api/v1/ location must define proxy_pass"
    target = match.group(1)
    assert target == "http://api:8000/api/v1/", (
        f"/api/v1/ proxy_pass must be http://api:8000/api/v1/, got {target}"
    )


def test_admin_proxy_pass_targets_correct_upstream():
    text = _read()
    match = re.search(r"location\s+/admin/\s*\{[^}]*?proxy_pass\s+([^;\s]+)", text, re.DOTALL)
    assert match, "/admin/ location must define proxy_pass"
    target = match.group(1)
    assert target == "http://admin:8000/admin/", (
        f"/admin/ proxy_pass must be http://admin:8000/admin/, got {target}"
    )
