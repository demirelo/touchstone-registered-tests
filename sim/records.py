"""JSON records for the sweep stages: configs, search results with archives, candidates."""
from __future__ import annotations

import numpy as np

from .cell import Abstain
from .config import MarketConfig, ProviderParams
from .policies.families import Family, exact_key
from .policies.honest import HonestMax
from .reference import Candidate
from .search import ArchiveEntry, SearchResult


def cfg_to_dict(cfg: MarketConfig) -> dict:
    return {"N": cfg.N, "J": cfg.J, "T": cfg.T, "sigma": cfg.sigma, "e": cfg.e, "v_min": cfg.v_min, "v_max": cfg.v_max,
            "providers": [[p.q_max, p.a, p.b, p.k] for p in cfg.providers], "alpha": cfg.alpha, "budget": cfg.budget}


def cfg_from_dict(d: dict) -> MarketConfig:
    return MarketConfig(N=int(d["N"]), J=int(d["J"]), T=int(d["T"]), sigma=float(d["sigma"]), e=float(d["e"]), v_min=float(d["v_min"]),
                        v_max=float(d["v_max"]), providers=tuple(ProviderParams(float(q), float(a), float(b), int(k)) for q, a, b, k in d["providers"]),
                        alpha=float(d["alpha"]), budget=float(d["budget"]))


def search_to_json(res: SearchResult) -> dict:
    return {"best_x": [float(v) for v in np.asarray(res.best_x)], "best_knobs": res.best_knobs, "best_f": res.best_f, "best_source": res.best_source,
            "restart_bests": [float(v) for v in res.restart_bests], "evals": res.evals, "incumbent_scores": res.incumbent_scores,
            "projection_f": res.projection_f, "replaced_by_projection": res.replaced_by_projection,
            "archive": [{"knobs": e.knobs, "f": e.f, "per_seed_profit": [float(v) for v in e.per_seed_profit],
                         "per_seed_normalized": [float(v) for v in e.per_seed_normalized], "inflated": bool(e.inflated), "source": e.source}
                        for e in res.archive.values()]}


def search_from_json(d: dict) -> SearchResult:
    archive = {exact_key(e["knobs"]): ArchiveEntry(knobs=e["knobs"], f=float(e["f"]), per_seed_profit=np.array(e["per_seed_profit"]),
                                                   per_seed_normalized=np.array(e["per_seed_normalized"]), inflated=bool(e["inflated"]), source=e["source"])
               for e in d["archive"]}
    return SearchResult(best_x=np.array(d["best_x"]), best_knobs=d["best_knobs"], best_f=float(d["best_f"]), best_source=d["best_source"],
                        restart_bests=list(d["restart_bests"]), evals=int(d["evals"]), trace=[], incumbent_scores=dict(d["incumbent_scores"]),
                        projection_f=float(d["projection_f"]), replaced_by_projection=bool(d["replaced_by_projection"]), archive=archive)


def candidate_to_json(c: Candidate) -> dict:
    return {"name": c.name, "knobs": c.knobs}


def candidate_from_record(family: Family, d: dict) -> Candidate:
    if d["knobs"] is None:
        return Candidate(d["name"], Abstain if d["name"] == "abstain" else HonestMax, None)
    knobs = dict(d["knobs"])
    return Candidate(d["name"], lambda: family.make(knobs), knobs)
