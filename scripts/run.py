from __future__ import annotations

import argparse, csv, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.mechanisms.second_score import SecondScore
from sim.metrics import summarize
from sim.policies.honest import HonestMax


def make_rule(name: str):
    return {"B1": lambda: PostedPrices(0.25, 0.40, 0.55),
            "B2": lambda: PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10),
            "B3": lambda: SecondScore(tol=0.12, L=10)}[name]()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", required=True, choices=["B1", "B2", "B3"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--budget", type=float, default=0.0)
    ap.add_argument("--T", type=int, default=200)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    c = MarketConfig.default()
    cfg = MarketConfig(N=c.N, J=c.J, T=args.T, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                       providers=c.providers, alpha=c.alpha, budget=args.budget)
    res = run_episode(cfg, make_rule(args.rule), [HonestMax() for _ in range(cfg.N)], args.seed)
    row = {"rule": args.rule, "seed": args.seed, **summarize(res)}
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        w.writeheader()
        w.writerow({k: (f"{v:.12g}" if isinstance(v, float) else v) for k, v in row.items()})


if __name__ == "__main__":
    main()
