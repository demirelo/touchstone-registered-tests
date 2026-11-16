"""Tests for the churn-aware continuation adapter (plan section 4): every menu candidate is replayed under churn."""
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import continuation as K  # noqa: E402


@dataclass(frozen=True)
class Cand:
    name: str
    known_profit: object = None
    known_normalized: object = None


def test_select_reference_clears_cached_scores_under_churn(monkeypatch):
    import sim.reference as SR
    seen = []
    monkeypatch.setattr(SR, "select_reference", lambda cell, cands, cache: seen.append(list(cands)) or cands[0])
    monkeypatch.setattr(SR, "_rep_wrapped", False, raising=False)
    K.install_continuation()
    from sim.reference import select_reference           # the import run_cell does at call time
    cands = [Cand("abstain", 1.0, 1.0), Cand("menu1", 2.0, 0.5)]
    select_reference(SimpleNamespace(others=((1, None),)), cands, None)
    assert seen[-1][0].known_profit == 1.0                # the abstain candidate keeps its known value
    assert seen[-1][1].known_profit is None and seen[-1][1].known_normalized is None   # replayed under churn
    select_reference(SimpleNamespace(others=()), cands, None)
    assert seen[-1][1].known_profit == 2.0                # without churn the stored score is used


def test_install_is_idempotent(monkeypatch):
    import sim.reference as SR
    monkeypatch.setattr(SR, "select_reference", lambda cell, cands, cache: cands)
    monkeypatch.setattr(SR, "_rep_wrapped", False, raising=False)
    K.install_continuation(); first = SR.select_reference
    K.install_continuation()
    assert SR.select_reference is first


def test_run_cell_imports_select_reference_at_call_time():
    # the adapter relies on this: run_cell reads sim.reference.select_reference when it runs, not at module import
    import convergence_v2 as B
    src = inspect.getsource(B.run_cell)
    assert "from sim.reference import reference_candidates, select_reference" in src
    assert not hasattr(B, "select_reference")
