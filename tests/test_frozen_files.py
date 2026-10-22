"""The registered and frozen files stay byte-identical to the revision branch base (plan 2026-10-22-revision-build, Global Constraints)."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = "2a288f5"
FROZEN = ("sim/mechanisms/proposed.py", "sim/mechanisms/second_score.py", "sim/mechanisms/audit_random.py", "sim/policies/exploratory.py",
          "sim/policies/adaptive.py", "sim/policies/identity.py", "sim/search.py", "sim/reference.py", "sim/market.py",
          "scripts/explore_attackers.py", "experiments/locked.yaml", "experiments/proposed.yaml")


@pytest.mark.parametrize("path", FROZEN)
def test_frozen_files_unchanged(path):
    base = subprocess.run(["git", "show", f"{BASE}:{path}"], cwd=ROOT, capture_output=True, check=True).stdout
    assert (ROOT / path).read_bytes() == base
