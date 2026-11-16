"""Churn-aware continuation adapter (replication-plan.md, section 4; review r1 blocker). `convergence_v2.run_cell` imports
`sim.reference.select_reference` at call time, so `churn_v2.install()` (which wraps only `revision_v2.select_reference`)
does not reach it, and frozen menu candidates would keep their no-churn training scores. install_continuation() installs
churn and wraps the sim.reference function the same way: under churn every candidate except abstain is replayed.
Call it in the parent and in every worker (pool initializer) before run_cell."""
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE.parent / "churn", HERE.parent / "followup2"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def install_continuation() -> None:
    import churn_v2
    import sim.reference as SR
    churn_v2.install()
    if getattr(SR, "_rep_wrapped", False):
        return
    orig = SR.select_reference

    def select_reference(cell, candidates, cache):
        if cell.others:
            candidates = [c if c.name == "abstain" else replace(c, known_profit=None, known_normalized=None) for c in candidates]
        return orig(cell, candidates, cache)

    SR.select_reference = select_reference
    SR._rep_wrapped = True
