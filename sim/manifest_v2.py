"""The protocol-v2 manifest (design 8.1, 8.2, 6.5, 6.6), read from experiments/revision-v2-manifest.yaml: the 374 search
cells, the 132 doubling checks, the 14 fixed-attack cross-evaluations, the execution priority, the pre-stated cut order,
and, per context, the records a final freeze requires and the reference-bank rules."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "experiments/revision-v2-manifest.yaml"
Q1_Q4_RULES = ("F000", "F111", "C*", "R4", "C*/S2")
FACTORIAL = ("F000", "F001", "F010", "F011", "F100", "F101", "F110", "F111")
MATCHED = ("F000", "F001", "F010", "F011", "F100", "F101", "F110", "F111", "C*", "C*/S0", "C*/S2", "R4")
MENU_FAMILIES = ("D2+H3", "X7-SC")


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


def cells() -> list[dict]:
    d = doc(); out = []
    for name, b in d["blocks"].items():
        markets = d["markets"] if b["markets"] == "all" else b["markets"]
        rho = float(b.get("rho", 0.2))
        objectives = b.get("objectives", [b.get("objective")])
        for m in markets:
            for r in b["rules"]:
                for f in b["families"]:
                    for o in objectives:
                        if name == "coalition":
                            out.extend(_cell(name, m, rho, r, f, o, c, s) for c in b["c"] for s in b["schedules"])
                        else:
                            out.append(_cell(name, m, rho, r, f, o))
    return out


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
        if c["market"] == "headline" and c["rho"] == 0.2 and (c["block"] in ("welfare", "coalition") or (c["block"] == "matched")):
            out.append(c["id"])
        elif c["market"].startswith("fresh") and c["block"] == "matched" and c["rule"] in Q1_Q4_RULES:
            out.append(c["id"])
    return out


def cross_evaluations() -> list[tuple[str, str]]:
    return [(context(m), f) for m in doc()["markets"] for f in MENU_FAMILIES]


def priority(cell: dict) -> int:
    if cell["block"] == "matched":
        return 0 if cell["rule"] in Q1_Q4_RULES else 1
    if cell["block"] in ("welfare", "coalition") or (cell["block"] == "extras" and cell["family"] in ("X5-AG/v2", "H4")):
        return 2
    return 3


def bank_rules(ctx: str, family: str, cuts: int = 0, h4_excluded: bool = False) -> list[str]:
    present = {c["rule"] for c in effective(cuts, h4_excluded) if c["context"] == ctx and c["family"] == family and c["objective"] == "profit"}
    return [r for r in MATCHED if r in present]


def required(ctx: str, cuts: int = 0, h4_excluded: bool = False) -> list[str]:
    cs = [c for c in effective(cuts, h4_excluded) if c["context"] == ctx]
    req = [c["id"] for c in cs]
    rules = sorted({c["rule"] for c in cs if c["objective"] != "coalition"}, key=lambda r: (r not in MATCHED, r))
    req += [f"reference/{ctx}/{r}" for r in rules]
    for c in cs:
        if c["objective"] in ("total", "min"):
            tag = f"{c['rule']}_c{c['c']}_{c['schedule']}"
            for kind in ("joint_twin", "joint_reference"):
                rid = f"{kind}/{ctx}/{tag}"
                if rid not in req:
                    req.append(rid)
    env_rules = sorted({c["rule"] for c in cs if c["block"] == "extras"})
    req += [f"envelope/{ctx}/{r}" for r in env_rules]
    if any(c["block"] == "matched" for c in cs) and ctx in {context(m) for m in doc()["markets"]}:
        req += [f"bank/{ctx}/{f}" for f in MENU_FAMILIES]
    return req
