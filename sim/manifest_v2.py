"""The protocol-v2 manifest (design draft 7: 8.1, 8.1a, 8.2, 6.5, 6.6, 6.7), read from experiments/revision-v2-manifest.yaml:
the 287 search cells and 3 diagnostic cells, the 98 doubling checks, the 14 fixed-attack cross-evaluations, the execution
priority, the pre-stated cut order, per context the records a final freeze requires and the reference-bank rules, the
distinct-rule check (design 3.4), and the question-to-cell map (design 8.1a)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import json
import math

import yaml

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "experiments/revision-v2-manifest.yaml"
Q1_Q4_RULES = ("F000", "F111", "C*")
FACTORIAL = ("F000", "F001", "F010", "F011", "F100", "F101", "F110", "F111")
MATCHED = ("F000", "F001", "F010", "F011", "F100", "F101", "F110", "F111", "C*", "C*/S0")
FIXED = MATCHED + ("C*/S2", "R4")                    # rules at the fixed pair (R4 and C*/S2 only in the rho = 1 repair block)
MENU_FAMILIES = ("D2+H3", "X7-SC")
SECONDARY = ("B3-t", "R3-t", "C*-t")
CORE = ("F000", "F111", "C*")
J, L_FIXED = 50, 10


@lru_cache(maxsize=1)
def doc() -> dict:
    return yaml.safe_load(PATH.read_text())


CUT_ORDER = tuple(doc()["cut_order"])


def context(market: str, rho: float = 0.2) -> str:
    return f"{market}@rho{rho:g}" if rho != 0.2 else f"{market}@rho0.2"


def _cell(block, market, rho, rule, family, objective, c=None, schedule=None) -> dict:
    ctx = context(market, rho)
    cid = f"{ctx}|{rule}|{family}|{objective}" + (f"|c{c}_{schedule}" if c is not None else "")
    return {"id": cid, "block": block, "market": market, "context": ctx, "rho": rho, "rule": rule, "family": family, "objective": objective,
            "c": c, "schedule": schedule}


def _families(b: dict, market: str) -> list:
    if "families_by_market" in b:
        return b["families_by_market"]["headline" if market == "headline" else "fresh"]
    return b["families"]


def headline_a_tot(rho: float) -> int:
    """A_tot = floor(beta S_hat / (rho m)) = floor((beta / rho) n_FB) on the headline calibration (design 3.4)."""
    n_fb = float(json.loads((ROOT / "experiments/calibration.json").read_text())["n_FB"])
    return int(math.floor(0.05 / float(rho) * n_fb + 1e-12))


def _descriptor(rule: str, a_tot: int) -> tuple:
    """(selection, pacing schedule) of a rule at the fixed pair; rules with their own parameters are unique."""
    if rule in FACTORIAL:
        pacing = ("reserve", min(J * L_FIXED, a_tot)) if rule[3] == "1" else ("spread",)
        return (("factorial", rule[1], rule[2]), pacing)
    if rule == "R4":
        return (("factorial", "1", "1"), ("reserve", min(J * L_FIXED, a_tot // 2)))
    if rule in ("C*", "C*/S0", "C*/S2"):
        pacing = {"C*": ("reserve", min(J * L_FIXED, a_tot)), "C*/S0": ("spread",), "C*/S2": ("reserve", min(J * L_FIXED, a_tot // 2))}[rule]
        return (("credibility",), pacing)
    return (("own", rule), ("own", rule))


def distinct_rule_problems(cs: list[dict], a_tot: dict) -> list[str]:
    """Design 3.4: no two rules compared in one block and context may have the same selection and pacing schedule."""
    seen: dict = {}; out = []
    for c in cs:
        key = (c["block"], c["context"], _descriptor(c["rule"], int(a_tot[c["context"]])))
        other = seen.setdefault(key, c["rule"])
        if other != c["rule"]:
            out.append(f"{c['block']} {c['context']}: {other} and {c['rule']} have the same selection and pacing")
    return sorted(set(out))


def cells() -> list[dict]:
    d = doc(); out = []
    for name, b in d["blocks"].items():
        markets = d["markets"] if b["markets"] == "all" else b["markets"]
        rho = float(b.get("rho", 0.2))
        objectives = b.get("objectives", [b.get("objective")])
        for m in markets:
            for r in b["rules"]:
                for f in _families(b, m):
                    for o in objectives:
                        if "c" in b:
                            out.extend(_cell(name, m, rho, r, f, o, c, s) for c in b["c"] for s in b["schedules"])
                        else:
                            out.append(_cell(name, m, rho, r, f, o))
    problems = distinct_rule_problems(out, {c["context"]: headline_a_tot(c["rho"]) for c in out})
    if problems:
        raise ValueError(f"manifest refused: {problems}")
    return out


def menu_families(ctx: str, rule: str) -> tuple[str, ...]:
    """Design 6.4: the secondary whole systems on fresh markets have the reduced D2+H3 menu; every other reference both."""
    return ("D2+H3",) if rule in SECONDARY and ctx.startswith("fresh") else MENU_FAMILIES


def _cut(cell: dict, spec: dict) -> bool:
    if spec.get("markets") == "fresh" and not cell["market"].startswith("fresh"):
        return False
    return all(cell[k] == v for k, v in (("block", spec.get("block")), ("family", spec.get("family")), ("rule", spec.get("rule"))) if v is not None)


def effective(cuts: int = 0, h4_excluded: bool = False) -> list[dict]:
    out = cells()
    for spec in CUT_ORDER[: int(cuts)]:
        out = [c for c in out if not _cut(c, spec)]
    if h4_excluded:
        out = [c for c in out if c["family"] != "H4"]
    return out


def doublings() -> list[str]:
    out = []
    for c in cells():
        if c["market"] == "headline" and c["rho"] == 0.2 and c["block"] in ("matched", "welfare", "coalition", "coalition_roles"):
            out.append(c["id"])
        elif c["market"].startswith("fresh") and c["block"] == "matched" and c["rule"] in Q1_Q4_RULES:
            out.append(c["id"])
    return out


def cross_evaluations() -> list[tuple[str, str]]:
    return [(context(m), f) for m in doc()["markets"] for f in MENU_FAMILIES]


def priority(cell: dict) -> int:
    if cell["block"] == "matched":
        return 0 if cell["rule"] in Q1_Q4_RULES else 1
    if cell["block"] in ("welfare", "coalition", "coalition_roles", "diagnostic") or (cell["block"] == "extras" and cell["family"] in ("X5-AG/v2", "H4")):
        return 2
    return 3


def bank_rules(ctx: str, family: str, cuts: int = 0, h4_excluded: bool = False) -> list[str]:
    present = {c["rule"] for c in effective(cuts, h4_excluded) if c["context"] == ctx and c["family"] == family and c["objective"] == "profit"}
    return [r for r in FIXED if r in present]


def required(ctx: str, cuts: int = 0, h4_excluded: bool = False) -> list[str]:
    cs = [c for c in effective(cuts, h4_excluded) if c["context"] == ctx and c["block"] != "diagnostic"]   # diagnostics run after the freeze
    req = [c["id"] for c in cs]
    rules = sorted({c["rule"] for c in cs if c["objective"] != "coalition"}, key=lambda r: (r not in FIXED, r))
    req += [f"reference/{ctx}/{r}" for r in rules]
    groups: dict = {}
    for c in cs:
        if c["objective"] in ("total", "min"):
            groups.setdefault(f"{c['rule']}_c{c['c']}", set()).add(c["schedule"] if c["family"] == "X6-SE/v2" else None)
    for tag, schedules in groups.items():                  # design draft 7, 6.3: one coalition group per rule and c
        req += [f"joint_twin/{ctx}/{tag}_{s}" for s in ("synchronised", "staggered") if s in schedules]
        req += [f"{kind}/{ctx}/{tag}" for kind in ("joint_reference_pre", "joint_reference", "coalition_select")]
    env_rules = sorted({c["rule"] for c in cs if c["block"] == "extras"})
    req += [f"envelope/{ctx}/{r}" for r in env_rules]
    if any(c["block"] == "matched" for c in cs) and ctx in {context(m) for m in doc()["markets"]}:
        req += [f"bank/{ctx}/{f}" for f in MENU_FAMILIES]
    return req


def _ids(pred, cuts: int = 0, h4_excluded: bool = False) -> list[str]:
    return [c["id"] for c in effective(cuts, h4_excluded) if pred(c)]


def _fresh(c: dict) -> bool:
    return c["market"].startswith("fresh")


QUESTIONS = {
    "Q1": {"cells": lambda c: _fresh(c) and c["block"] == "matched" and c["rule"] in ("F111", "C*") and c["family"] in MENU_FAMILIES,
           "checks": lambda c: _fresh(c) and c["block"] == "matched" and c["rule"] in ("F111", "C*") and c["family"] in MENU_FAMILIES},
    "Q2": {"cells": lambda c: c["block"] == "matched" and c["rule"] in FACTORIAL and c["rho"] == 0.2,
           "checks": lambda c: c["market"] == "headline" and c["block"] == "matched" and c["rule"] in FACTORIAL},
    "Q3": {"cells": lambda c: c["rho"] == 0.2 and c["rule"] in CORE and (c["block"] in ("welfare", "coalition", "coalition_roles", "diagnostic")
                                                                         or c["family"] in ("D2+H3", "X7-SC", "X5-AG/v2", "H4") and c["block"] in ("matched", "extras")),
           "checks": lambda c: c["rule"] in CORE and c["rho"] == 0.2 and (c["block"] in ("welfare", "coalition", "coalition_roles") or c["block"] == "matched")},
    "Q4": {"cells": lambda c: _fresh(c) and c["block"] == "matched" and c["rule"] in ("F000", "F111") and c["family"] == "D2+H3",
           "checks": lambda c: _fresh(c) and c["block"] == "matched" and c["rule"] in ("F000", "F111") and c["family"] == "D2+H3"},
    "repair": {"cells": lambda c: c["block"] == "repair", "checks": lambda c: False},
    "whole": {"cells": lambda c: c["block"] == "tuned", "checks": lambda c: False},
}


def question_cells(name: str, cuts: int = 0, h4_excluded: bool = False) -> dict:
    """Design 8.1a: the cells a question needs and the scheduled doubling checks it depends on (cross-evaluations for Q2)."""
    q = QUESTIONS[name]; dbl = set(doublings())
    out = {"cells": _ids(q["cells"], cuts, h4_excluded), "checks": [i for i in _ids(q["checks"], cuts, h4_excluded) if i in dbl]}
    if name == "Q2":
        out["cross"] = [f"cross/{ctx}/{f}" for ctx, f in cross_evaluations()]
    return out

