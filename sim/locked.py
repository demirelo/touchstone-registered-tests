from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from .config import MarketConfig, ProviderParams

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "experiments" / "locked.yaml"


def load_locked(path: str | Path = DEFAULT_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def seeds(locked: dict, namespace: str) -> list[int]:
    s = locked["seeds"][namespace]
    if s is None:
        raise ValueError(f"seed namespace {namespace!r} is not available in this repo")
    return [int(x) for x in s]


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def settings_hash(locked: dict) -> str:
    """Hash of every experimental setting: the whole file except the version label and the blocks written at the lock
    (tuned and calibration by the lock tooling, identity_salt_sha256 by the separate session), so installing them
    at the lock keeps the pre-lock artifacts valid."""
    bound = {k: v for k, v in locked.items() if k not in ("version", "tuned", "calibration", "identity_salt_sha256")}
    return hashlib.sha256(json.dumps(bound, sort_keys=True).encode()).hexdigest()


def market_config_from_locked(locked: dict) -> MarketConfig:
    mk = locked["market"]; pt = mk["providers"]
    providers = tuple(ProviderParams(q_max=float(q), a=float(a), b=float(b), k=int(k))
                      for q, a, b, k in zip(pt["q_max"], pt["a"], pt["b"], pt["k"]))
    return MarketConfig(N=int(mk["N"]), J=int(mk["J"]), T=int(mk["T"]), sigma=float(mk["sigma"]), e=float(mk["e"]),
                        v_min=float(mk["v_min"]), v_max=float(mk["v_max"]), providers=providers, alpha=0.0, budget=0.0)
