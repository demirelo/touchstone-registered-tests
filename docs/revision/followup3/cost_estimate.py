"""Cost estimate of the churn replication (plan draft 2) from experiments/v2/benchmark/timings.json, the churn slowdown
measured for the churn arm (docs/revision/churn/churn_cost.py) and the memory-safe worker counts of the churn arm and
Run B. Two numbers per scenario: core-hours at 0.108 USD per core-hour, and billed pod time from a stage schedule
(waves at the stage's worker limit, stages in sequence) at 0.56 USD per hour; the estimate is the larger of the two.
Assumptions are named inline; review round 1 asked for the schedule, the gates, calibration, diagnostics, continuation
slowdown and a flag-share sensitivity.
Usage (repository root): python3 docs/revision/followup3/cost_estimate.py"""
import json
import math

T = json.load(open("experiments/v2/benchmark/timings.json"))["timings"]
U, POD, PREP = 0.108, 0.56, 0.6
MARKETS, RULES, MENU_RULES, RATES = 6, 4, 10, (0.03, 0.05)
SLOW = 8.62 / 6.48                     # the p = 0.05 slowdown, applied to every churn stage (conservative for 0.03)
CALIB_H = 0.25                         # assumption: six calibrations of 20 seeds each on the pod (not benchmarked)
W_SEARCH, W_EVAL, W_CONT = 16, 9, 5    # churn arm (search 16, evaluate and doubling 9); Run B continuation 5
EV = T["eval160"]["profit"] * 200 / 160
DIAG = 60.0


def waves(n: int, w: int) -> int:
    return math.ceil(n / w) if n else 0


def estimate(flag_share: float, rounds: int = 3) -> dict:
    cells = (1 + len(RATES)) * MARKETS * RULES                      # 72 evaluation cells
    menu_d2 = MARKETS * (MENU_RULES + 1)                            # ten matched rules plus C-thr(12), D2+H3
    menu_x7 = MARKETS * (MENU_RULES + 1)                            # the same in X7-SC; menu X7-SC winners get no doubling
    churn_cells = len(RATES) * MARKETS * RULES
    flagged = round(flag_share * cells)
    cont_round = (T["doubling"] + EV) * SLOW                        # one continuation round; round 1 repeats the doubling
    stages = {   # name: (core seconds, schedule seconds)
        "calibration": (CALIB_H * 3600, CALIB_H * 3600),
        "gates": (3 * (T["d2h3_cell"] + EV + T["doubling"]), 3 * (T["d2h3_cell"] + EV + T["doubling"])),   # p = 0 ordinary,
        # p = 0 through the churn path (injected churn zero), and one continuation round against its doubling record; serial
        "menu_x7": (menu_x7 * T["x7_cell"], waves(menu_x7, W_SEARCH) * T["x7_cell"]),
        "menu_d2h3": (menu_d2 * T["d2h3_cell"], waves(menu_d2, W_SEARCH) * T["d2h3_cell"]),
        "references": (MARKETS * RULES * T["reference"], MARKETS * RULES * T["reference"]),               # serial, as Run A
        "p0_eval_doubling": (MARKETS * RULES * (EV + T["doubling"]), waves(MARKETS * RULES, W_EVAL) * (EV + T["doubling"])),
        "churn_search": (churn_cells * T["d2h3_cell"] * SLOW, waves(churn_cells, W_SEARCH) * T["d2h3_cell"] * SLOW),
        "churn_eval_doubling": (churn_cells * (EV + T["doubling"]) * SLOW, waves(churn_cells, W_EVAL) * (EV + T["doubling"]) * SLOW),
        "continuation": (flagged * rounds * cont_round, waves(flagged, W_CONT) * rounds * cont_round),
        "diagnostics": (cells * 2 * DIAG, waves(cells * 2, W_EVAL) * DIAG),   # frozen and final winners
    }
    core_h = sum(c for c, _ in stages.values()) / 3600
    sched_h = sum(s for _, s in stages.values()) / 3600 + PREP
    usd_core, usd_pod = core_h * U, sched_h * POD
    est = max(usd_core, usd_pod)
    return {"flag_share": flag_share, "flagged_cells": flagged,
            "schedule_hours": {k: round(s / 3600, 2) for k, (_, s) in stages.items()},
            "core_hours": round(core_h, 1), "billed_pod_hours": round(sched_h, 1),
            "usd_core": round(usd_core, 2), "usd_pod": round(usd_pod, 2), "estimate_usd": round(est, 2),
            "estimate_x1.25": round(est * 1.25, 2)}


if __name__ == "__main__":
    print(json.dumps([estimate(0.30), estimate(0.50)], indent=1))
