import importlib

import pytest


@pytest.fixture(autouse=True)
def _reload_registry_after_each_test():
    """sim.registry reads its paths from the environment at import time; tests that monkeypatch them reload it, so
    reload it again after every test (the environment is restored by then) so no test order sees a stale path."""
    yield
    try:
        import sim.registry as reg
        importlib.reload(reg)
    except Exception:
        pass
