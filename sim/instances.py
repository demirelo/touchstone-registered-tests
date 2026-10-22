"""Market instances and seed streams of the revision program (design 7.1, 7.2). A synthetic neighbourhood of the headline
market: N 10, J 50, T 200, sigma 0.05, no entry cost, v_min 0.6, beta 0.05, rho 0.2; per draw, sorted quality ceilings,
cost slopes falling with quality (plus noise), fixed costs, capacities, and the value ceiling. Every random input comes
from a domain-separated SHA-256 digest of a root: "dev-20261022" for the public development instances, the Bitcoin block
hash at height H for the fresh ones. Draw order inside an attempt: q_max (10), b_lo, b_hi, b noise (10), a (10), k (10),
v_max; attempts repeat in the same stream until the configuration validates."""
from __future__ import annotations

import hashlib

import numpy as np

from .calibrate import calibrate, cell_config
from .config import MarketConfig, ProviderParams

DEV_ROOT = "dev-20261022"
EVAL_RANGE = (30_000_000, 40_000_000)
COVERAGE_RANGE = (40_000_000, 60_000_000)
CALIBRATION_SEEDS = tuple(range(4000, 4020))
LIMIT = 10_000


class InstanceLimit(RuntimeError):
    pass


def digest(root: str, domain: str, n: int) -> bytes:
    return hashlib.sha256(f"{root}|touchstone-v2|{domain}|{int(n)}".encode("ascii")).digest()


def stream(root: str, i: int) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64(int.from_bytes(digest(root, "instance", i)[:16], "big")))


def draw_instance(rng: np.random.Generator, limit: int = LIMIT) -> tuple[MarketConfig, int]:
    for rejections in range(int(limit)):
        q = np.sort(rng.uniform(0.55, 1.0, 10)); b_lo = rng.uniform(0.18, 0.26); b_hi = rng.uniform(0.34, 0.46)
        noise = rng.uniform(-0.02, 0.02, 10); a = rng.uniform(0.0, 0.05, 10); k = rng.integers(4, 9, size=10); v_max = rng.uniform(1.2, 1.6)
        b = [b_hi - (b_hi - b_lo) * r / 9 + noise[r] for r in range(10)]
        providers = tuple(ProviderParams(q_max=float(q[r]), a=float(a[r]), b=float(b[r]), k=int(k[r])) for r in range(10))
        cfg = MarketConfig(N=10, J=50, T=200, sigma=0.05, e=0.0, v_min=0.6, v_max=float(v_max), providers=providers, alpha=0.05, budget=0.0)
        try:
            cfg.validate()
        except ValueError:
            continue
        return cfg, rejections
    raise InstanceLimit(f"no valid instance in {limit} draws")


def _draw_stream(root: str, i: int, limit: int) -> tuple[MarketConfig, int]:
    return draw_instance(stream(root, i), limit)


def markets(root: str, count: int, prefix: str = "fresh", limit: int = LIMIT) -> list[dict]:
    """Label <prefix><i> uses stream i; a stream that hits the limit gives its label the next unused index >= count."""
    out, spare = [], int(count)
    for i in range(int(count)):
        idx = i
        while True:
            try:
                cfg, rej = _draw_stream(root, idx, limit); break
            except InstanceLimit:
                idx, spare = spare, spare + 1
        out.append({"label": f"{prefix}{i}", "stream_index": idx, "cfg": cfg, "rejections": rej})
    return out


def dev_markets() -> list[dict]:
    return markets(DEV_ROOT, 2, prefix="dev")


def calibrated(cfg: MarketConfig, rho: float = 0.2, beta: float = 0.05) -> MarketConfig:
    return cell_config(cfg, calibrate(cfg, list(CALIBRATION_SEEDS)), rho=rho, beta=beta)


def _seeds(root: str, domain: str, n: int, lo: int, width: int) -> list[int]:
    out, seen, c = [], set(), 0
    while len(out) < int(n):
        v = lo + int.from_bytes(digest(root, domain, c)[:8], "big") % width; c += 1
        if v not in seen:
            seen.add(v); out.append(v)
    return out


def eval_seeds(root: str, label: str, n: int = 200) -> list[int]:
    return _seeds(root, "seeds/" + label, n, EVAL_RANGE[0], EVAL_RANGE[1] - EVAL_RANGE[0])


def coverage_pool(label: str, n: int = 20_000) -> list[int]:
    return _seeds(DEV_ROOT, "coverage/" + label, n, COVERAGE_RANGE[0], COVERAGE_RANGE[1] - COVERAGE_RANGE[0])


def identity_salt_hex(root: str) -> str:
    return digest(root, "salt", 0).hex()
