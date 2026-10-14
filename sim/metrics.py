from __future__ import annotations

from .market import EpisodeResult


def summarize(res: EpisodeResult) -> dict[str, float]:
    served = int(res.served.sum())
    out = {
        "sstar": res.sstar, "W": res.W,
        "gross_eff": (res.W + res.audit_cost) / res.sstar,
        "net_eff": res.W / res.sstar,
        "audit_spend": res.audit_cost / res.sstar,
        "audit_cost": res.audit_cost,
        "audited_fraction": (int(res.audits.sum()) / served) if served else 0.0,
        "value": res.value, "cost": res.cost, "entry": res.entry, "buyer_surplus": res.buyer_surplus,
    }
    for i in range(len(res.profit)):
        out[f"profit_{i}"] = float(res.profit[i])
    return out


def gain(attack: EpisodeResult, ref: EpisodeResult, focal: int) -> float:
    n = len(attack.profit)
    return float((attack.profit[focal] - ref.profit[focal]) / (attack.sstar / n))


def _others(res: EpisodeResult, focal: int) -> float:
    return res.buyer_surplus + float(res.profit.sum() - res.profit[focal]) - res.audit_cost


def harm(attack: EpisodeResult, ref: EpisodeResult, focal: int) -> tuple[float, float]:
    accounting = ((ref.W - attack.W) + (attack.profit[focal] - ref.profit[focal])) / attack.sstar
    direct = (_others(ref, focal) - _others(attack, focal)) / attack.sstar
    return float(accounting), float(direct)
