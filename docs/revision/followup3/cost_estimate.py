"""Cost estimate of the churn replication (plan draft 3, review r3 caveats applied) from experiments/v2/benchmark/timings.json, the churn slowdown
measured for the churn arm (docs/revision/churn/churn_cost.py) and the memory-safe worker counts of the churn arm and
Run B. Two numbers per scenario: core-hours at 0.108 USD per core-hour, and billed pod time from a stage schedule
(waves at the stage's worker limit, stages in sequence) at 0.56 USD per hour; the estimate is the larger of the two.
Assumptions are named inline; review round 1 asked for the schedule, the gates, calibration, diagnostics, continuation
slowdown and a flag-share sensitivity.
Usage (repository root): python3 docs/revision/followup3/cost_estimate.py"""
import json
import math

T = json.load(open("experiments/v2/benchmark/timings.json"))["timings"]
U, POD, PREP, PODS, TRANSFER_H = 0.108, 0.56, 0.6, 2, 0.2   # two pods, each with preparation and a transfer tail
MARKETS, RULES, MENU_RULES, RATES = 6, 4, 10, (0.03, 0.05)
SLOW = 8.62 / 6.48                     # the p = 0.05 slowdown, applied to every churn stage (conservative for 0.03)
CALIB_H = 0.25                         # assumption: six calibrations of 20 seeds each on the pod (not benchmarked)
W_SEARCH, W_EVAL, W_CONT = 16, 9, 5    # churn arm (search 16, evaluate and doubling 9); Run B continuation 5
EV = T["eval160"]["profit"] * 200 / 160
DIAG = 60.0


def waves(n: int, w: int) -> int:
    return math.ceil(n / w) if n else 0


DIRS = {"menu": (MARKETS * 3, 3), "cthr": (MARKETS, 1)}   # rate directories: (jobs, rules) of R3, C*, B3 and of C-thr(12)


def _dir_eval_doubling(n: int, rules: int, slow: float) -> tuple:
    """(core s, schedule s) of one directory's evaluation and doubling: the churn arm first runs one evaluation task per
    rule and one doubling task serially as its memory preflight (churn_v2.preflight_sample), then the rest in waves."""
    core = n * (EV + T["doubling"]) * slow
    sched = ((rules + waves(n - rules, W_EVAL)) * EV + (1 + waves(n - 1, W_EVAL)) * T["doubling"]) * slow
    return core, sched


def estimate(flag_share: float, rounds: int = 3) -> dict:
    cells = (1 + len(RATES)) * MARKETS * RULES                      # 72 evaluation cells
    menu_d2 = MARKETS * (MENU_RULES + 1)                            # ten matched rules plus C-thr(12), D2+H3
    menu_x7 = MARKETS * (MENU_RULES + 1)                            # the same in X7-SC; menu X7-SC winners get no doubling
    flagged = round(flag_share * cells)
    cont_round = (T["doubling"] + EV) * SLOW                        # one continuation round; round 1 repeats the doubling
    p0 = [_dir_eval_doubling(n, k, 1.0) for n, k in DIRS.values()]
    churn = [_dir_eval_doubling(n, k, SLOW) for _ in RATES for n, k in DIRS.values()]
    search = [(n * T["d2h3_cell"] * SLOW, waves(n, W_SEARCH) * T["d2h3_cell"] * SLOW) for _ in RATES for n, _ in DIRS.values()]
    diag_dirs = [(n * 2 * DIAG * s, waves(n, W_EVAL) * DIAG * s) for s in (1.0, SLOW, SLOW) for n, _ in DIRS.values()]
    r3_cont = round(flag_share * MARKETS * 2)                       # R3 menu cells at p = 0 and 0.05 with continued winners
    stages = {   # name: (core seconds, schedule seconds), in execution order (review r2: D2+H3 before X7-SC, gates after
        # their menu and reference inputs; implementation review r1: churn search per rate directory, 6 waves in all;
        # the serial memory preflight of each directory; the gate round always run; continued-winner diagnostics)
        "calibration": (CALIB_H * 3600, CALIB_H * 3600),
        "menu_d2h3": (menu_d2 * T["d2h3_cell"], waves(menu_d2, W_SEARCH) * T["d2h3_cell"]),
        "menu_x7": (menu_x7 * T["x7_cell"], waves(menu_x7, W_SEARCH) * T["x7_cell"]),     # needs the embedded D2+H3 winner
        "references": (MARKETS * RULES * T["reference"], MARKETS * RULES * T["reference"]),               # serial, as Run A
        "p0_eval_doubling": tuple(map(sum, zip(*p0))),
        "gate_churn_zero": (T["d2h3_cell"] + 2 * (EV + T["doubling"]), T["d2h3_cell"] + 2 * (EV + T["doubling"])),   # review
        # r3: one churn-zero search, evaluation and doubling against the ordinary menu search and its evaluation and doubling
        # (search, evaluate and doubling must agree); serial, after the p = 0 evaluation
        "churn_search": tuple(map(sum, zip(*search))),
        "churn_eval_doubling": tuple(map(sum, zip(*churn))),
        "diagnostics": tuple(map(sum, zip(*diag_dirs))),            # base and doubled winners of every directory
        "gate_churn_nonzero": (cont_round, cont_round),   # the first p = 0.05 cell's continuation round 1, always, serial
        "continuation": (flagged * rounds * cont_round, waves(flagged, W_CONT) * rounds * cont_round),
        "diagnostics_continued": (r3_cont * DIAG * SLOW, waves(r3_cont, W_EVAL) * DIAG * SLOW),
    }
    core_h = sum(c for c, _ in stages.values()) / 3600
    sched_h = sum(s for _, s in stages.values()) / 3600 + PODS * (PREP + TRANSFER_H)
    usd_core, usd_pod = core_h * U, sched_h * POD
    est = max(usd_core, usd_pod)
    return {"flag_share": flag_share, "flagged_cells": flagged,
            "schedule_hours": {k: round(s / 3600, 2) for k, (_, s) in stages.items()},
            "core_hours": round(core_h, 1), "billed_pod_hours": round(sched_h, 1),
            "usd_core": round(usd_core, 2), "usd_pod": round(usd_pod, 2), "estimate_usd": round(est, 2),
            "estimate_x1.25": round(est * 1.25, 2)}


if __name__ == "__main__":
    print(json.dumps([estimate(0.30), estimate(0.50)], indent=1))
