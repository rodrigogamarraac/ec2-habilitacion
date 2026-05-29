import importlib


def test_main_module_imports():
    mod = importlib.import_module("main")
    assert hasattr(mod, "app"), "main.py must expose a FastAPI 'app' instance"


def test_expected_router_prefixes_present():
    mod = importlib.import_module("main")
    routes = {getattr(r, "path", None) for r in mod.app.router.routes}

    assert "/api/v1/healthz" in routes
    assert "/api/v1/tables/types" in routes
    assert "/api/v1/reservations/availability/" in routes
    assert "/api/v1/menu/" in routes, (
        f"Expected /api/v1/menu/ to be registered, got routes: {sorted(p for p in routes if p)}"
    )
    assert "/api/v1/restaurants/" in routes
    assert "/api/v1/restaurants/{id}/menu" in routes


def test_reservations_router_module_name_is_correct():
    importlib.import_module("api.v1.reservations")


def test_table_types_router_uses_existing_dependency():
    mod = importlib.import_module("api.v1.table_types")
    services = importlib.import_module("services.getAllTableTypes")
    assert hasattr(services, "get_all_table_types")
    assert mod.router is not None
