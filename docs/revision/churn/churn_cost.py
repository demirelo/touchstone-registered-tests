"""Billed pod time of the churn arm (plan section 7), with the serial memory-preflight tasks (review r4).
Usage: uv run python docs/revision/churn/churn_cost.py
Per-job stage seconds are the benchmark values in churn_v2.STAGE_SECONDS; the churn slowdowns are the churn_timing.py
measurements (40 fresh0 evaluation seeds: 6.48 s without churn, 7.34 s at p = 0.01, 8.62 s at p = 0.05)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from churn_v2 import STAGE_SECONDS as S, _waves

SLOW = {0.01: 7.34 / 6.48, 0.05: 8.62 / 6.48}; JOBS = 18; RULES = 3; PREP_H = 0.6; USD_H = 0.56


def billed(workers_search=16, workers_eval=9, preflight=True):
    gate = S["search"] + S["evaluate"] + S["doubling"]                     # the p = 0 gate cell, serially
    sec = gate
    for s in SLOW.values():
        ke, kd = (RULES, 1) if preflight else (0, 0)
        sec += s * (S["search"] * _waves(JOBS, workers_search)
                    + S["evaluate"] * (ke + _waves(JOBS - ke, workers_eval))
                    + S["doubling"] * (kd + _waves(JOBS - kd, workers_eval))
                    + S["diagnostics"] * _waves(JOBS, workers_eval))
    h = sec / 3600 + PREP_H
    return {"stage_hours": round(sec / 3600, 2), "billed_hours": round(h, 2), "usd": round(h * USD_H, 2)}


if __name__ == "__main__":
    print(json.dumps({"without_preflight": billed(preflight=False), "with_preflight_9": billed(),
                      "with_preflight_2_workers": billed(workers_eval=2)}))
