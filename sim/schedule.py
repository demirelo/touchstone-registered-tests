"""The one place that says how many runs a cell needs. manifest.py sums it; sweep.py executes it
and checks its run counter against it (spec 5.3: the manifest is authoritative). Exact entries are
what the sweep always runs; bounds cover data-dependent work (bank candidates with unknown values)."""
from __future__ import annotations

from dataclasses import dataclass

N_CORNERS = {"D1": 32, "D2": 128, "D2+H3": 256}
N_PROJECTED_CORNERS = {"D1": 16, "D2": 64}


@dataclass(frozen=True)
class Budget:
    restarts: int
    evals: int
    n_train: int
    n_val: int


SMOKE_BUDGET = Budget(restarts=1, evals=16, n_train=1, n_val=2)


def budget_from_locked(locked: dict) -> Budget:
    s = locked["search"]
    return Budget(restarts=int(s["restarts"]), evals=int(s["evals_per_restart"]),
                  n_train=len(locked["seeds"]["dev_train"]), n_val=len(locked["seeds"]["dev_val"]))


def search_runs(b: Budget) -> int:
    return b.restarts * b.evals * b.n_train


def cell_runs(family_name: str, b: Budget) -> dict[str, int]:
    """Exact runs of one full cell: twin search and its projection, attack search with two incumbents and its
    projection, reference selection (honest-max is the only registered candidate without a known value),
    corner controls, and the dev-val evaluation of attack, clipped attack, reference, and honest-max."""
    s = search_runs(b)
    return {"twin": s, "twin_projection": b.n_train, "attack": s, "incumbents": 2 * b.n_train, "attack_projection": b.n_train,
            "reference": b.n_train, "corners": N_CORNERS[family_name] * b.n_train, "evaluation": 4 * b.n_val}


STAGE_KEYS = {"search": ("twin", "twin_projection", "attack", "incumbents", "attack_projection", "corners"),
              "evaluate": ("evaluation",)}


def stage_runs(family_name: str, stage: str, b: Budget) -> int:
    runs = cell_runs(family_name, b)
    return sum(runs[k] for k in STAGE_KEYS[stage])


def bank_stage_bound(n_unknown: int, b: Budget) -> int:
    """Every member without a known value as an attack (corners are known from the search stage),
    plus a re-evaluation and a projection when the incumbent is replaced."""
    return (n_unknown + 2) * b.n_train


def reference_bound(n_projected: int, b: Budget) -> int:
    """Honest-max plus every projected bank member with an unknown value."""
    return (1 + n_projected) * b.n_train


def doubling_bound(n_projected: int, b: Budget) -> int:
    """Two fixed-clip searches at half the budget, each with a projection, plus two reference selections."""
    half = b.restarts * (b.evals // 2) * b.n_train
    return 2 * (half + b.n_train) + 2 * reference_bound(n_projected, b)


def all_deviators_runs(locked: dict, N: int, b: Budget) -> int:
    """Attack and twin procedures (spec 5.3 counts both), each: sweeps x N x (search + projection + current value) x seeds;
    plus both final profiles evaluated on dev-val. The smoke budget caps evaluations and seeds the way sweep.py does."""
    ad = locked["all_deviators"]
    evals = min(int(ad["evals"]), b.evals) * int(ad["restarts"]); seeds = min(int(ad["seeds"]), b.n_train)
    return 2 * (int(ad["sweeps"]) * N * (evals + 2) * seeds) + 2 * b.n_val


def tuning_point_runs(locked: dict) -> int:
    tg = locked["tuning"]
    s = tg["inner_restarts"] * tg["inner_evals"] * tg["inner_seeds"]; n = tg["inner_seeds"]
    return 2 * s + n + 2 * n + n + n + 4 * n     # twin, attack, twin projection, incumbents, attack projection, honest, in-sample evaluation


def tuning_recheck_runs(b: Budget) -> int:
    s = search_runs(b); n = b.n_train
    return 2 * s + n + 2 * n + n + n + 4 * b.n_val


def tuning_grid_sizes(locked: dict) -> dict[str, int]:
    tg = locked["tuning"]
    return {"B1": 27, "B2": 27 * len(tg["tol"]) * len(tg["L"]), "B3": len(tg["tol"]) * len(tg["L"])}


def bank_members(n_dev_cells_per_family: int) -> dict:
    """Bank composition per target family: members are the best-found attacks of the development cells of each
    family plus the target family's exact corners (known from the search stage, so they cost no bank run);
    D1 members enter D2 through the embedding."""
    m = n_dev_cells_per_family
    return {"D1": {"n_unknown": m, "n_projected": m + N_PROJECTED_CORNERS["D1"]},
            "D2": {"n_unknown": 2 * m, "n_projected": 2 * m + N_PROJECTED_CORNERS["D2"]}}
