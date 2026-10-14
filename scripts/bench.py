from __future__ import annotations

import platform, statistics, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.config import MarketConfig
from sim.firstbest import first_best_episode
from sim.market import run_episode
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.policies.honest import HonestMax
from sim.rng import make_draws

GATE_MS = 45.0


def cpu_model() -> str:
    try:
        if sys.platform == "darwin":
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
    except Exception:
        pass
    return platform.processor() or platform.machine()


def bench_episode_ms(n_runs: int = 20, warmups: int = 3) -> float:
    c = MarketConfig.default()
    base = MarketConfig(N=c.N, J=c.J, T=200, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=0.0)
    s_hat = statistics.mean(first_best_episode(base, make_draws(base, s)) for s in range(5))
    cfg = MarketConfig(N=c.N, J=c.J, T=200, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                       providers=c.providers, alpha=c.alpha, budget=0.05 * s_hat)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    pols = [HonestMax() for _ in range(cfg.N)]
    draws = make_draws(cfg, 0)
    sstar = first_best_episode(cfg, draws)
    for _ in range(warmups):
        run_episode(cfg, rule, pols, 0, draws=draws, sstar=sstar)
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        run_episode(cfg, rule, pols, 0, draws=draws, sstar=sstar)
        times.append((time.perf_counter() - t0) * 1000.0)
    return statistics.median(times)


if __name__ == "__main__":
    ms = bench_episode_ms()
    print(f"median T=200 B2 episode at B=0.05*S_hat: {ms:.1f} ms (gate {GATE_MS} ms) on {cpu_model()}")
    sys.exit(0 if ms <= GATE_MS else 1)
