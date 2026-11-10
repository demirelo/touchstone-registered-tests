"""Cost estimates of Run A and Run B from experiments/v2/benchmark/timings.json. Usage: python3 docs/revision/followup2/cost_estimate.py (from the repository root)."""
import json
t = json.load(open("experiments/v2/benchmark/timings.json"))["timings"]; u = 0.108; pod = 0.56
ev = lambda k: t["eval160"][k] * 200 / 160
a_cell = {"D2+H3": t["d2h3_cell"] + ev("profit") + t["doubling"], "X7-SC": t["x7_cell"] + ev("x7") + t["doubling_x7"]}
a = 6 * (a_cell["D2+H3"] + a_cell["X7-SC"] + t["reference"])
print("A: per market core-s", round(a / 6, 1), "total core-h", round(a / 3600, 2), "USD at 0.108/core-h", round(a / 3600 * u, 2))
# wall: per market the critical path D2+H3 search -> X7 search -> reference -> eval -> X7 doubling; 6 markets in parallel on 16 vCPU (12 cells)
wall = t["d2h3_cell"] + t["x7_cell"] + t["reference"] + ev("x7") + t["doubling_x7"]
print("A: critical path h", round(wall / 3600, 2), "billed at 0.56/h", round(wall / 3600 * pod, 2), "(+0.3 h prep and tail:", round((wall / 3600 + 0.3) * pod, 2), ")")
b = 3 * (10 * t["doubling"] + 4 * t["doubling_x7"])
print("B: 14 cells x 3 rounds core-h", round(b / 3600, 2), "USD at 0.108/core-h", round(b / 3600 * u, 2))
wb = 3 * t["doubling_x7"]
print("B: critical path (an X7 cell, 3 rounds) h", round(wb / 3600, 2), "billed at 0.56/h", round(wb / 3600 * pod, 2), "(+0.3 h:", round((wb / 3600 + 0.3) * pod, 2), ")")
