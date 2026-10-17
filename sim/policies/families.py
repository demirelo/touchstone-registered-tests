from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
from scipy.stats import qmc

from .adaptive import AdaptiveCheat
from .fixed_cheat import FixedCheat


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _logit(p: float) -> float:
    p = min(max(p, 1e-12), 1 - 1e-12)
    return float(np.log(p / (1 - p)))


def exact_key(knobs: dict) -> tuple:
    """Identity of a policy: exact values, sorted by name. Used by the archive, the bank, and candidate
    de-duplication, so two distinct policies never share an entry or drop each other."""
    return tuple(sorted((k, float(v)) for k, v in knobs.items()))


def knob_key(knobs: dict) -> tuple:
    """Rounded key (9 decimals) for grouping in reports only; never for de-duplication."""
    return tuple(sorted((k, round(float(v), 9)) for k, v in knobs.items()))


@dataclass(frozen=True)
class Family:
    name: str
    knobs: tuple[str, ...]            # bounded knobs in order, then the binary knobs, "clip" last
    bounds: dict                      # a knob absent here is binary: a logistic coordinate thresholded at 0.5
    factory: object

    @property
    def dim(self) -> int:
        return len(self.knobs)

    def is_binary(self, k: str) -> bool:
        return k not in self.bounds

    def transform(self, x: np.ndarray) -> dict:
        s = _sigmoid(np.asarray(x, dtype=float))
        out = {}
        for k, v in zip(self.knobs, s):
            if self.is_binary(k):
                out[k] = 1 if v >= 0.5 else 0
            else:
                lo, hi = self.bounds[k]
                out[k] = float(lo + (hi - lo) * v)
        return out

    def inverse(self, knobs: dict, near: float = 0.02) -> np.ndarray:
        """Approximate inverse for search starts only; never use it to evaluate an exact point."""
        x = []
        for k in self.knobs:
            if self.is_binary(k):
                x.append(_logit(1 - near if knobs[k] else near))
            else:
                lo, hi = self.bounds[k]
                x.append(_logit((knobs[k] - lo) / (hi - lo)))
        return np.array(x)

    def project(self, knobs: dict) -> dict:
        out = dict(knobs); out["clip"] = 1
        return out

    def make(self, knobs: dict):
        return self.factory(**knobs)

    def corners(self) -> list[dict]:
        seen, out = set(), []
        for bits in product((0, 1), repeat=self.dim):
            k = {}
            for name, b in zip(self.knobs, bits):
                k[name] = b if self.is_binary(name) else float(self.bounds[name][b])
            key = exact_key(k)
            if key not in seen:
                seen.add(key); out.append(k)
        return out

    def honest_point(self) -> dict:
        return {k: ((1 if k == "clip" else 0) if self.is_binary(k) else float(self.bounds[k][0])) for k in self.knobs}

    def registered_starts(self, settings: dict, twin: bool = False) -> list[np.ndarray]:
        near = float(settings["near_corner"])
        lo_x, hi_x = _logit(near), _logit(1 - near)
        honest = np.full(self.dim, lo_x); honest[self.knobs.index("clip")] = hi_x
        cheat = np.full(self.dim, hi_x)
        for name in ("s", "clip"):
            if name in self.knobs:
                cheat[self.knobs.index(name)] = lo_x
        sob = qmc.Sobol(d=self.dim, scramble=True, seed=int(settings["sobol_seed"])).random(4)[1:4]
        sobol = [np.array([_logit(float(v)) for v in row]) for row in sob]
        return ([honest, cheat] if twin else [cheat, honest]) + sobol      # a one-restart attack search starts where cheating is reachable; a twin search where truthful profit is positive


D1 = Family("D1", ("u", "m", "s", "w", "clip"),
            {"u": (0.0, 1.0), "m": (0.0, 1.0), "s": (0.0, 0.3), "w": (0.0, 2.0)}, FixedCheat)
D2 = Family("D2", ("u0", "m0", "s", "d", "r", "w", "clip"),
            {"u0": (0.0, 1.0), "m0": (0.0, 1.0), "s": (0.0, 0.3), "d": (0.0, 1.0), "r": (0.0, 0.2), "w": (0.0, 2.0)},
            AdaptiveCheat)
FAMILIES = {"D1": D1, "D2": D2}


def embed_d1_in_d2(k: dict) -> dict:
    return {"u0": k["u"], "m0": k["m"], "s": k["s"], "d": 0.0, "r": 0.0, "w": k["w"], "clip": k["clip"]}


def embed_d2_in_h3(k: dict) -> dict:
    """Amendment 2: the behaviour-preserving containment of D2 in D2+H3 (x = 0 never exits)."""
    return {**k, "x": 0}


def embed_d2_in_h3_exit(k: dict) -> dict:
    """Amendment 2: the additional replacement-policy transformation (x = 1 exits after a failed audit)."""
    return {**k, "x": 1}


H3_EMBEDDINGS = ("embed_d2_in_h3", "embed_d2_in_h3_exit")
