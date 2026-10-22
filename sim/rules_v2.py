"""The revision-program rule set (design 3.5): the factorial cells and R4, the credibility comparator C* with its pacing
variants, the tuned whole systems, and B2 at its registered parameters. Public constants (design 5.1): the horizon T from
the market configuration (public by spec 4.0) and the ban length L from the rule's describe record."""
from __future__ import annotations

import json
from pathlib import Path

from .mechanisms.credibility import Credibility
from .mechanisms.factorial import NAMES as FACTORIAL_NAMES, make_factorial
from .mechanisms.proposed import Proposed
from .mechanisms.second_score import SecondScore

ROOT = Path(__file__).resolve().parents[1]
MATCHED = ["F000", "F001", "F010", "F011", "F100", "F101", "F110", "F111", "C*", "C*/S0", "C*/S2", "R4"]
CORE = ["F000", "F111", "C*", "R4"]
TUNED = ["B3-t", "R3-t", "R4-t", "C*-t"]
COMPARATOR_PACING = {"C*": "S1", "C*/S0": "S0", "C*/S2": "S2", "C*-t": "S1"}


def registered_b2_params() -> dict:
    return dict(json.loads((ROOT / "experiments/tuned/tuned_B2.json").read_text())["best_params"])


def make_rule(name: str, tol: float = 0.16, L: int = 10, cred: dict | None = None, b2_params: dict | None = None):
    if name in FACTORIAL_NAMES:
        return make_factorial(name, tol, L)
    if name in COMPARATOR_PACING:
        if cred is None:
            raise ValueError(f"{name} needs the comparator's variant, K, and M")
        return Credibility(cred["variant"], int(cred["K"]), tol, L, COMPARATOR_PACING[name], cred.get("M"))
    if name == "B3-t":
        return SecondScore(tol, L)
    if name == "R3-t":
        return Proposed("A", "T1", tol, L)
    if name == "R4-t":
        return make_factorial("R4", tol, L)
    if name == "B2":
        from .tuning import rule_from_params
        return rule_from_params("B2", b2_params if b2_params is not None else registered_b2_params())
    raise ValueError(f"unknown rule {name!r}")


def public_constants(rule, cfg) -> dict:
    return {"T": int(cfg.T), "L": int(rule.describe()["parameters"]["ban_length"])}
