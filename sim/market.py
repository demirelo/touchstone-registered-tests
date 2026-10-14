from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

import numpy as np

from .checks import validate_assignment, validate_audits, validate_consequences, validate_payments
from .config import MarketConfig
from .firstbest import first_best_episode
from .ledger import Ledger
from .mechanisms.base import AuditRecord, Consequences, Offer, RoundRecord, StateView
from .policies.base import ProviderHistory, ProviderView, validate_action
from .rng import Draws, make_draws


@dataclass
class EpisodeResult:
    sstar: float
    profit: np.ndarray
    value: float
    cost: float
    entry: float
    audit_cost: float
    served: np.ndarray
    audits: np.ndarray
    failures: np.ndarray
    claims: np.ndarray
    efforts: np.ndarray
    buyer_surplus: float
    W: float
    history: tuple[RoundRecord, ...]
    ledger: Ledger


def run_episode(cfg: MarketConfig, rule, policies, seed: int, draws: Draws | None = None, sstar: float | None = None) -> EpisodeResult:
    cfg.validate()
    if len(policies) != cfg.N:
        raise ValueError("one policy per provider")
    d = draws if draws is not None else make_draws(cfg, seed)
    sstar_v = first_best_episode(cfg, d) if sstar is None else float(sstar)
    rule.bind(cfg)
    N, T, alpha = cfg.N, cfg.T, cfg.alpha
    allowance = int(np.floor(cfg.budget / alpha + 1e-12)) if alpha > 0 else 0
    ledger = Ledger(N, T)
    banned_until = np.zeros(N, dtype=np.int64)
    caps = np.array([p.k for p in cfg.providers], dtype=np.int64)
    a_arr = np.array([p.a for p in cfg.providers]); b_arr = np.array([p.b for p in cfg.providers])
    histories = [ProviderHistory() for _ in range(N)]
    posted = getattr(rule, "prices", None)
    memory: dict = {}
    records_all: list[RoundRecord] = []
    served = np.zeros((T, N), dtype=np.int64); audits = np.zeros(T, dtype=np.int64)
    failures = np.zeros((T, N), dtype=np.int64); claims = np.full((T, N), np.nan); efforts = np.zeros((T, N))
    value_total = 0.0
    tol = rule.tol

    for t in range(T):
        values_t = d.values[t].copy()
        offers: dict[int, Offer] = {}
        effort = np.zeros(N)
        for i in range(N):
            if t < banned_until[i]:
                continue
            act = policies[i].act(ProviderView(i=i, params=cfg.providers[i], t=t, posted_prices=posted,
                                               history=histories[i], policy_seed=int(d.policy_seed[t, i])))
            validate_action(act, cfg.providers[i])
            effort[i] = float(act.effort); efforts[t, i] = effort[i]
            if act.offer is not None:
                offers[i] = Offer(claim=float(act.offer.claim), bid=float(act.offer.bid))
                claims[t, i] = offers[i].claim
        tie_key = np.array(d.tie_key[t], copy=True); tie_key.setflags(write=False)
        memory["tie_key"] = tie_key
        values_ro = values_t.copy(); values_ro.setflags(write=False)
        hist = tuple(records_all)
        view = StateView(t=t, T=T, N=N, audits_left=allowance, audit_u=float(d.audit_u[t]), audit_key=d.audit_key[t],
                         banned_until=banned_until, bond=ledger.bond, capacity=caps, escrow={}, history=hist, memory=memory)
        try:
            assignment = dict(rule.allocate(values_ro, dict(offers), view))
            payments = dict(rule.price(dict(assignment), values_ro, dict(offers), view))
        except ValueError as exc:
            if "read-only" in str(exc):
                raise ValueError("rule attempted to write read-only state") from exc
            raise
        validate_assignment(assignment, values_t, offers, view)
        validate_payments(payments, assignment, values_t, offers)
        escrow: dict[int, float] = {}; owner: dict[int, int] = {}
        delivered: dict[int, float] = {}
        if assignment:
            jobs = np.fromiter(assignment.keys(), dtype=np.int64, count=len(assignment))
            provs = np.fromiter(assignment.values(), dtype=np.int64, count=len(assignment))
            pay = np.array([payments[j] for j in assignment], dtype=float)
            ledger.funding[t] += np.bincount(provs, weights=pay, minlength=N)
            escrow = dict(zip(jobs.tolist(), pay.tolist()))
            owner = dict(assignment)
            slots = np.zeros(len(provs), dtype=np.int64); seen = np.zeros(N, dtype=np.int64)
            for n, i in enumerate(provs.tolist()):
                slots[n] = seen[i]; seen[i] += 1
            y = effort[provs] + d.noise[t, provs, slots]
            value_total += float((values_t[jobs] * y).sum())
            counts = np.bincount(provs, minlength=N)
            ledger.cost[t] += counts * (a_arr + b_arr * effort)
            served[t] = counts
            delivered = dict(zip(jobs.tolist(), y.tolist()))
        view_a = StateView(t=t, T=T, N=N, audits_left=allowance, audit_u=float(d.audit_u[t]), audit_key=d.audit_key[t],
                           banned_until=banned_until, bond=ledger.bond, capacity=caps, escrow=escrow, history=hist, memory=memory)
        to_audit = list(rule.audit(dict(assignment), view_a))
        validate_audits(to_audit, assignment, view_a)
        records = tuple(AuditRecord(job=j, provider=assignment[j], delivered=delivered[j], claim=offers[assignment[j]].claim,
                                    failed=(tol is not None and delivered[j] < offers[assignment[j]].claim - tol))
                        for j in to_audit)
        allowance -= len(records)
        ledger.charge_audit(t, alpha * len(records))
        audits[t] = len(records)
        cons = rule.enforce(records, view_a)
        if not isinstance(cons, Consequences):
            raise TypeError("enforce must return a Consequences object")
        validate_consequences(cons, records, escrow, owner, ledger.bond, ledger.recent_receipts(), set(offers.keys()))
        failed_jobs_of: dict[int, list[int]] = {}
        for r in records:
            if r.failed:
                failures[t, r.provider] += 1
                failed_jobs_of.setdefault(r.provider, []).append(r.job)
        for ident, rounds in cons.bans.items():
            banned_until[ident] = max(int(banned_until[ident]), t + int(rounds) + 1)
        refunded = np.zeros(N)
        for j, amt in cons.refunds.items():
            refunded[owner[j]] += amt
        ledger.settle(t, escrow, owner, cons, failed_jobs_of)
        ledger.check_conservation(escrow_outstanding=0.0)
        frozen_cons = Consequences(refunds=MappingProxyType(dict(cons.refunds)), bans=MappingProxyType(dict(cons.bans)),
                                   holdbacks=MappingProxyType(dict(cons.holdbacks)), forfeits=MappingProxyType(dict(cons.forfeits)),
                                   releases=MappingProxyType(dict(cons.releases)))
        records_all.append(RoundRecord(t=t, offers=MappingProxyType(dict(offers)), assignment=MappingProxyType(dict(assignment)),
                                       payments=MappingProxyType(dict(payments)), audits=records, consequences=frozen_cons))
        audited_by = np.bincount([r.provider for r in records], minlength=N) if records else np.zeros(N, dtype=np.int64)
        for i in range(N):
            histories[i].append(int(served[t, i]), float(ledger.funding[t, i]), int(audited_by[i]), int(failures[t, i]),
                                float(refunded[i]), int(banned_until[i]))

    ledger.terminal_settlement()
    ledger.check_conservation(escrow_outstanding=0.0)
    cost = float(ledger.cost.sum()); entry = float(ledger.entry.sum())
    audit_cost = min(float(ledger.audit_cost.sum()), float(cfg.budget))   # integer audits; never above B by rounding
    W = value_total - cost - entry - audit_cost
    buyer_surplus = value_total - float(ledger.funding.sum()) + ledger.buyer_credit()
    return EpisodeResult(sstar=sstar_v, profit=ledger.profit(), value=value_total, cost=cost, entry=entry,
                         audit_cost=audit_cost, served=served, audits=audits, failures=failures, claims=claims,
                         efforts=efforts, buyer_surplus=buyer_surplus, W=W, history=tuple(records_all), ledger=ledger)
