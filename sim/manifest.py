from __future__ import annotations

from dataclasses import dataclass, asdict

from .schedule import (Budget, all_deviators_runs, bank_members, bank_stage_bound, budget_from_locked, cell_runs,
                       doubling_bound, tuning_grid_sizes, tuning_point_runs, tuning_recheck_runs)


@dataclass(frozen=True)
class CellSpec:
    section: str
    rule: str
    family: str
    beta: float
    rho: float
    position: str
    kind: str
    runs: int
    exact: bool
    post_lock: bool
    name: str
    params_override: dict | None = None


def cell_name(section: str, rule: str, family: str, beta: float, rho: float, position: str) -> str:
    return f"{rule}_{family}_beta{beta}_rho{rho}_{position}_{section}"


def _full_cells(locked: dict, rules: list[str], b: Budget, post_lock: bool) -> list[CellSpec]:
    betas = [float(x) for x in locked["beta_grid"]]; bh = float(locked["beta_headline"]); rho0 = float(locked["rho"]["default"])
    cells: list[CellSpec] = []
    for rule in rules:
        for fam in ("D1", "D2"):
            for beta in betas:
                for pos in (locked["positions"] if beta == bh else ["median"]):
                    cells.append(CellSpec("development", rule, fam, beta, rho0, pos, "full_cell", sum(cell_runs(fam, b).values()), True, post_lock,
                                          cell_name("development", rule, fam, beta, rho0, pos)))
        for rho in [float(r) for r in locked["rho"]["sweep"] if float(r) != rho0]:
            cells.append(CellSpec("rho_sweep", rule, "D2", bh, rho, "median", "full_cell", sum(cell_runs("D2", b).values()), True, post_lock,
                                  cell_name("rho_sweep", rule, "D2", bh, rho, "median")))
        if rule in locked["no_ban_rules"]:
            cells.append(CellSpec("no_ban", rule, "D2", bh, rho0, "median", "full_cell", sum(cell_runs("D2", b).values()), True, post_lock,
                                  cell_name("no_ban", rule, "D2", bh, rho0, "median"), params_override={"L": 0}))
        cells.append(CellSpec("h3", rule, "D2+H3", bh, rho0, "median", "full_cell", sum(cell_runs("D2+H3", b).values()), True, post_lock,
                              cell_name("h3", rule, "D2+H3", bh, rho0, "median")))
    return cells


def _bank_total(cells: list[CellSpec], b: Budget) -> int:
    n_dev = len([c for c in cells if c.section == "development" and c.family == "D1"])
    m = bank_members(n_dev)
    total = 0
    for c in cells:
        if c.kind == "full_cell" and c.family in m:      # targets: every D1 and D2 full cell; controls, tuning, all-deviators rows are not cells
            total += bank_stage_bound(m[c.family]["n_unknown"], b) + m[c.family]["n_projected"] * b.n_train
    return total


def enumerate_manifest(locked: dict, rules: list[str], budget: Budget | None = None) -> list[CellSpec]:
    b = budget or budget_from_locked(locked)
    bh = float(locked["beta_headline"]); rho0 = float(locked["rho"]["default"]); N = int(locked["market"]["N"])
    cells = _full_cells(locked, rules, b, post_lock=False)
    m = bank_members(len([c for c in cells if c.section == "development" and c.family == "D1"]))
    for rule in rules:
        for fam, pos in locked["doubling_cells"]:
            cells.append(CellSpec("controls", rule, fam, bh, rho0, pos, "doubling_check", doubling_bound(m[fam]["n_projected"], b), False, False,
                                  cell_name("controls", rule, fam, bh, rho0, pos)))
        cells.append(CellSpec("all_deviators", rule, "D2", bh, rho0, "all", "iterated_br_attack_and_twin", all_deviators_runs(locked, N, b), True, False,
                              cell_name("all_deviators", rule, "D2", bh, rho0, "all")))
        grid = tuning_grid_sizes(locked)[rule]
        cells.append(CellSpec("tuning", rule, "D2", bh, rho0, "median", "grid_and_recheck",
                              grid * tuning_point_runs(locked) + int(locked["tuning"]["recheck_top"]) * tuning_recheck_runs(b), True, False,
                              cell_name("tuning", rule, "D2", bh, rho0, "median")))
    pre_bank = _bank_total(cells, b)
    cells.append(CellSpec("bank", "all", "D1+D2", bh, rho0, "all", "bank_pass_and_candidates", pre_bank, False, False, "bank_pre_lock"))
    with_proposed = _full_cells(locked, rules + ["proposed"], b, post_lock=True)
    cells.append(CellSpec("bank_post_lock", "proposed", "D1+D2", bh, rho0, "all", "bank_pass_and_candidates",
                          _bank_total(with_proposed, b) - pre_bank, False, True, "bank_post_lock"))
    cells.append(CellSpec("all_deviators_post_lock", "proposed", "D2", bh, rho0, "all", "iterated_br_attack_and_twin",
                          all_deviators_runs(locked, N, b), True, True, cell_name("all_deviators", "proposed", "D2", bh, rho0, "all")))
    for fam in ("D1", "D2"):
        for pos in locked["positions"]:
            cells.append(CellSpec("ablation", "proposed", fam, bh, rho0, pos, "full_cell", sum(cell_runs(fam, b).values()), True, True,
                                  cell_name("ablation", "proposed", fam, bh, rho0, pos)))
    return cells


def totals(cells: list[CellSpec]) -> dict[str, int]:
    t: dict[str, int] = {}
    for c in cells:
        t[c.section] = t.get(c.section, 0) + c.runs
        key = "post_lock" if c.post_lock else "pre_lock"
        t[key] = t.get(key, 0) + c.runs
        if not c.post_lock:
            k2 = "pre_lock_exact" if c.exact else "pre_lock_upper_bound"
            t[k2] = t.get(k2, 0) + c.runs
    return t


def rows(cells: list[CellSpec]) -> list[dict]:
    return [asdict(c) for c in cells]
