"""Cost estimate of the churn replication (plan draft 1) from experiments/v2/benchmark/timings.json and the churn
slowdowns measured in docs/revision/churn/churn_cost.py. Core-hours at 0.108 USD per core-hour, as the earlier
follow-ups; the pod-time check uses 16 vCPU at 0.56 USD per hour. Conservative choices are named inline.
Usage (repository root): python3 docs/revision/followup3/cost_estimate.py"""
import json

t = json.load(open("experiments/v2/benchmark/timings.json"))["timings"]
U, POD, VCPU, PREP = 0.108, 0.56, 16, 0.6
MARKETS, RULES, MENU_RULES = 6, 4, 10              # R3, C*, C-thr(12), B3; the registered menu has the rule plus 9 bank rules
RATES = (0.03, 0.05)
SLOW = 8.62 / 6.48                                  # the p = 0.05 slowdown, used for both rates (conservative for 0.03)
FLAG_SHARE, ROUNDS = 0.30, 3                        # churn arm: 21 of 72 flagged; continued search up to three rounds
ev = lambda k: t["eval160"][k] * 200 / 160
h = lambda s: s / 3600


def estimate() -> dict:
    menu = MARKETS * (MENU_RULES * (t["d2h3_cell"] + t["x7_cell"]))                 # matched rules' D2+H3 and X7-SC winners
    runner = MARKETS * (t["d2h3_cell"] + t["x7_cell"])                              # C-thr(12) has its own searches
    refs = MARKETS * RULES * t["reference"]
    p0 = MARKETS * RULES * (ev("profit") + t["doubling"])                           # the p = 0 D2+H3 cell is the menu record
    churn = len(RATES) * MARKETS * RULES * SLOW * (t["d2h3_cell"] + ev("profit") + t["doubling"] + 60)
    cells = (1 + len(RATES)) * MARKETS * RULES
    cont = round(FLAG_SHARE * cells) * ROUNDS * (t["doubling"] + ev("profit"))
    parts = {"menu": menu, "runner_up": runner, "references": refs, "p0_eval_doubling": p0, "churn": churn, "continued": cont}
    core_h = h(sum(parts.values()))
    usd = core_h * U + PREP * POD
    return {"core_hours": {k: round(h(v), 1) for k, v in parts.items()}, "total_core_hours": round(core_h, 1),
            "pod_hours_at_16_vcpu": round(core_h / VCPU + PREP, 1), "usd": round(usd, 2), "usd_x1.25": round(usd * 1.25, 2),
            "watchdog_x1.3": round(usd * 1.3, 2)}


if __name__ == "__main__":
    print(json.dumps(estimate(), indent=1))
