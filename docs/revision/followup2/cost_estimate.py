"""Cost estimates of Run A (draft 3) and Run B (draft 3) from experiments/v2/benchmark/timings.json.
Usage (repository root): python3 docs/revision/followup2/cost_estimate.py"""
import json

t = json.load(open("experiments/v2/benchmark/timings.json"))["timings"]; u = 0.108; pod = 0.56; prep = 0.3
ev = lambda k: t["eval160"][k] * 200 / 160
h = lambda s: s / 3600
# Run A
a_core = 6 * (t["d2h3_cell"] + ev("profit") + t["doubling"] + t["x7_cell"] + ev("x7") + t["doubling_x7"] + t["reference"])
gate_a = t["d2h3_cell"] + ev("profit")                                   # the reset driver's reproduction gate on the pod
crit_a = t["d2h3_cell"] + t["x7_cell"] + 6 * t["reference"] + ev("x7") + t["doubling_x7"]   # six serial reference calls
billed_a = (h(gate_a) + h(crit_a) + prep) * pod
est_a = max(h(a_core) * u + h(gate_a) * u, billed_a)
print(f"A: {h(a_core):.2f} core-h ({h(a_core) * u:.2f} USD at 0.108); gate {h(gate_a):.2f} h; billed path {h(gate_a) + h(crit_a) + prep:.2f} h = {billed_a:.2f} USD; "
      f"estimate {est_a:.2f}, x1.25 {est_a * 1.25:.2f}; stop cap and reservation 3.00")
# Run B (draft 3): 10 D2+H3 and 9 X7-SC cells (14 flagged + 5 nesting X7-SC cells), up to 3 rounds, each round with
# its held-out evaluation allowance; the gate cells (headline X7-SC, fresh D2+H3) run serially first
rd = lambda x7: (t["doubling_x7"] if x7 else t["doubling"]) + ev("profit")
b_core = 3 * (10 * rd(False) + 9 * rd(True))
gate_b = rd(True) + rd(False)
crit_b = 3 * rd(True)                                                     # 16 workers: the 9 X7-SC cells start first
billed_b = (h(gate_b) + h(crit_b) + prep) * pod
est_b = max(h(b_core + gate_b) * u, billed_b)
print(f"B: {h(b_core):.2f} core-h ({h(b_core) * u:.2f} USD at 0.108); gate {h(gate_b):.2f} h serial; billed path {h(gate_b) + h(crit_b) + prep:.2f} h = {billed_b:.2f} USD; "
      f"estimate {est_b:.2f}, x1.25 {est_b * 1.25:.2f}; stop cap and reservation 4.25")
