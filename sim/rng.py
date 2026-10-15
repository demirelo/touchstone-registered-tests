from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .config import MarketConfig


@dataclass(frozen=True)
class Draws:
    """Every random input of an episode, a pure function of (seed, round); replacement identities add fixed
    streams keyed by entity, generation, round, and the identity salt."""
    values: np.ndarray        # (T, J)
    noise: np.ndarray         # (T, N, kmax)
    tie_key: np.ndarray       # (T, J, N) allocation tie-break keys; smaller wins
    audit_u: np.ndarray       # (T,) uniform for the audit count's stochastic rounding
    audit_key: np.ndarray     # (T, J) audit priority per job; smaller audited first
    policy_seed: np.ndarray   # (T, N)
    fresh_seed: np.ndarray    # (T, N) per-entity base for replacement identities' secrets (tie keys, entrant order, delivery noise)


def draws_for_round(cfg: MarketConfig, seed: int, t: int):
    g = np.random.default_rng(np.random.SeedSequence([int(seed), int(t)]))
    values = g.uniform(cfg.v_min, cfg.v_max, size=cfg.J)
    noise = g.normal(0.0, cfg.sigma, size=(cfg.N, cfg.kmax))
    tie_key = g.random(size=(cfg.J, cfg.N))
    audit_u = float(g.random())
    audit_key = g.random(size=cfg.J)
    policy_seed = g.integers(0, 2**31 - 1, size=cfg.N)
    fresh_seed = g.integers(0, 2**62, size=cfg.N)
    return values, noise, tie_key, audit_u, audit_key, policy_seed, fresh_seed


def make_draws(cfg: MarketConfig, seed: int) -> Draws:
    values = np.empty((cfg.T, cfg.J))
    noise = np.empty((cfg.T, cfg.N, cfg.kmax))
    tie_key = np.empty((cfg.T, cfg.J, cfg.N))
    audit_u = np.empty(cfg.T)
    audit_key = np.empty((cfg.T, cfg.J))
    policy_seed = np.empty((cfg.T, cfg.N), dtype=np.int64)
    fresh_seed = np.empty((cfg.T, cfg.N), dtype=np.int64)
    for t in range(cfg.T):
        v, n, tk, au, ak, ps, fs = draws_for_round(cfg, seed, t)
        values[t], noise[t], tie_key[t], audit_u[t], audit_key[t], policy_seed[t], fresh_seed[t] = v, n, tk, au, ak, ps, fs
    for arr in (values, noise, tie_key, audit_u, audit_key, policy_seed, fresh_seed):
        arr.setflags(write=False)
    return Draws(values, noise, tie_key, audit_u, audit_key, policy_seed, fresh_seed)


DEFAULT_SALT_PATH = Path(__file__).resolve().parents[1] / "experiments" / "identity_salt.hex"
SALT_ENV = "TOUCHSTONE_IDENTITY_SALT"
_SALT_CACHE: dict[str, bytes] = {}


def load_identity_salt(path: str | Path | None = None) -> bytes:
    """Harness secret for replacement identities' keys: 32 bytes, outside the config a rule may read.
    Resolution: the given path, else the file named by TOUCHSTONE_IDENTITY_SALT (the final salt, released
    after the freeze, lives at an untracked path), else the development salt in experiments/."""
    if path is None:
        path = os.environ.get(SALT_ENV) or DEFAULT_SALT_PATH
    key = str(path)
    if key not in _SALT_CACHE:
        salt = bytes.fromhex(Path(path).read_text().strip())
        if len(salt) != 32:
            raise ValueError("identity salt must be 32 bytes")
        _SALT_CACHE[key] = salt
    return _SALT_CACHE[key]


def _secret(salt: bytes, *parts) -> int:
    """Keyed one-way 64-bit digest; without the salt, the public streams (all functions of the episode seed) reveal nothing."""
    data = ":".join(str(int(x)) for x in parts).encode()
    return int.from_bytes(hashlib.blake2b(data, key=salt, digest_size=8).digest(), "little")


def identity_secret(salt: bytes, seed: int, t: int, fresh_seed_e: int, generation: int) -> int:
    return _secret(salt, 1, seed, t, fresh_seed_e, generation)


def retired_secret(salt: bytes, seed: int, t: int, identity: int) -> int:
    return _secret(salt, 2, seed, t, identity)


def entrant_rank(salt: bytes, seed: int, t: int, fresh_seed_e: int) -> int:
    """Order in which same-round exits are processed: a keyed secret per entity, so the ids of
    same-round entrants reveal nothing to a rule, even one that recovered the episode seed."""
    return _secret(salt, 3, seed, t, fresh_seed_e)


def replacement_noise(salt: bytes, seed: int, t: int, fresh_seed_e: int, generation: int, kmax: int, sigma: float) -> np.ndarray:
    """Delivery noise of a replacement identity's slots in round t: a salted stream, so an audited delivery
    cannot be matched to the entity's public noise stream by a rule that recovered the episode seed."""
    g = np.random.default_rng(np.random.SeedSequence(_secret(salt, 4, seed, t, fresh_seed_e, generation)))
    return g.normal(0.0, sigma, size=int(kmax))


def fresh_tie_keys(secrets, J: int) -> np.ndarray:
    """Tie-break keys for identities created by re-entry, (J, len(secrets)): column c is the
    uniform stream seeded by secrets[c]. A live replacement identity's secret depends on its
    entity's per-round fresh_seed and its generation only, so relabeling entities permutes
    the columns and creation order is irrelevant; the secret never reaches a rule."""
    out = np.empty((int(J), len(secrets)))
    for c, sec in enumerate(secrets):
        out[:, c] = np.random.default_rng(np.random.SeedSequence(int(sec))).random(int(J))
    out.setflags(write=False)
    return out
