from __future__ import annotations

from dataclasses import replace

import numpy as np

from .base import AuditRecord, Consequences, Mechanism, Offers, StateView

ENFORCEMENT_FIELDS = ("failed_audit", "ban_length", "holdback")


class EnforcementAblation(Mechanism):
    """Spec 8: the rule's allocation, pricing, audit selection and tolerance with
    another rule's enforcement. The harness applies only the consequences
    returned here, so the economic state is the ablated one by construction."""

    def __init__(self, rule: Mechanism, enforcer: Mechanism) -> None:
        self.rule, self.enforcer = rule, enforcer
        self.name = f"ablation({rule.name}|{enforcer.name})"
        self.tol = rule.tol
        self.prices = getattr(rule, "prices", None)

    def allocate(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        return self.rule.allocate(values_t, offers, view)

    def price(self, assignment, values_t, offers, view) -> dict[int, float]:
        return self.rule.price(assignment, values_t, offers, view)

    def audit(self, assignment, view) -> list[int]:
        return self.rule.audit(assignment, view)

    def bind(self, cfg) -> None:
        self.rule.bind(cfg); self.enforcer.bind(cfg)
        self._enforcer_memory: dict = {}

    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences:
        self.rule.enforce(records, view)          # side effects on the rule's memory only; its consequences are discarded
        try:
            return self.enforcer.enforce(records, replace(view, memory=self._enforcer_memory))
        except KeyError as exc:                   # the enforcer's allocate never runs, so its memory holds only what its own enforce wrote
            raise ValueError("an ablation enforcer must not depend on allocation-time memory") from exc

    def describe(self) -> dict:
        d = dict(self.rule.describe())
        e = self.enforcer.describe()
        params = dict(d.get("parameters", {}))
        for k in ENFORCEMENT_FIELDS:
            d[k] = e[k]
            params.pop(k, None)
            if k in e.get("parameters", {}):
                params[k] = e["parameters"][k]                  # the enforcer's figures for its fields; the rule keeps its audit tolerance
        d["parameters"] = params
        return d


def exclusion_by_allocation(res, after_failure: bool = True) -> dict[int, int]:
    """Rounds in which an identity offered, was not banned, and got no job; by default only
    after its first failed audit (spec 8: exclusion through allocation priority). With
    after_failure=False every identity's unserved eligible offers count: the competition baseline."""
    first_fail: dict[int, int] = {}
    for rec in res.history:
        for r in rec.audits:
            if r.failed and r.provider not in first_fail:
                first_fail[r.provider] = rec.t
    counts = {i: 0 for i in range(res.n_identities)}
    banned_until: dict[int, int] = {}
    for rec in res.history:
        served = set(rec.assignment.values())
        for i in rec.offers:
            eligible = rec.t >= banned_until.get(i, 0) and i not in served
            if eligible and (not after_failure or (i in first_fail and rec.t > first_fail[i])):
                counts[i] += 1
        for i, rounds in rec.consequences.bans.items():
            banned_until[i] = max(banned_until.get(i, 0), rec.t + int(rounds) + 1)
    return counts
