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
from .rng import Draws, entrant_rank, fresh_tie_keys, identity_secret, load_identity_salt, make_draws, replacement_noise, retired_secret


@dataclass
class EpisodeResult:
    sstar: float
    profit: np.ndarray            # per entity, summed over its identities
    value: float
    cost: float
    entry: float
    audit_cost: float
    served: np.ndarray            # (T, N) per entity
    audits: np.ndarray
    failures: np.ndarray          # (T, N) per entity
    claims: np.ndarray            # (T, N) per entity, nan when no offer
    efforts: np.ndarray           # (T, N) per entity
    buyer_surplus: float
    W: float
    history: tuple[RoundRecord, ...]
    ledger: Ledger
    n_identities: int
    entity_of: tuple[int, ...]    # identity -> entity
    identity_round: tuple[int, ...]   # identity -> creation round (0 for initial identities)
    identity_generation: tuple[int, ...]   # identity -> 0 for initial, 1 for the first replacement, ...
    identity_profit: np.ndarray   # per identity


def _frozen(cons: Consequences) -> Consequences:
    return Consequences(refunds=MappingProxyType(dict(cons.refunds)), bans=MappingProxyType(dict(cons.bans)),
                        holdbacks=MappingProxyType(dict(cons.holdbacks)), forfeits=MappingProxyType(dict(cons.forfeits)),
                        releases=MappingProxyType(dict(cons.releases)))


def run_episode(cfg: MarketConfig, rule, policies, seed: int, draws: Draws | None = None, sstar: float | None = None,
                identity_salt: bytes | None = None) -> EpisodeResult:
    cfg.validate()
    salt = load_identity_salt() if identity_salt is None else identity_salt
    if len(policies) != cfg.N:
        raise ValueError("one policy per entity")
    d = draws if draws is not None else make_draws(cfg, seed)
    sstar_v = first_best_episode(cfg, d) if sstar is None else float(sstar)
    rule.bind(cfg)
    N, T, J, alpha = cfg.N, cfg.T, cfg.J, cfg.alpha
    allowance = int(np.floor(cfg.budget / alpha + 1e-12)) if alpha > 0 else 0
    ledger = Ledger(N, T)
    caps_entity = np.array([p.k for p in cfg.providers], dtype=np.int64)
    a_arr = np.array([p.a for p in cfg.providers]); b_arr = np.array([p.b for p in cfg.providers])
    # identity bookkeeping; the arrays below are per identity. `alive` is harness-private and never reaches a rule.
    entity_of: list[int] = list(range(N))
    identity_of: list[int] = list(range(N))
    identity_round: list[int] = [0] * N
    generation: list[int] = [0] * N
    gen_of_entity = [0] * N
    alive: list[bool] = [True] * N
    banned_until = np.zeros(N, dtype=np.int64)
    caps_id = caps_entity.copy()
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
        effort_e = np.zeros(N)
        actions = []
        for e in range(N):   # pass 1: every entity acts under its current identity
            act = policies[e].act(ProviderView(i=e, params=cfg.providers[e], t=t, posted_prices=posted,
                                               history=histories[e], policy_seed=int(d.policy_seed[t, e]), identity=identity_of[e]))
            validate_action(act, cfg.providers[e])
            actions.append(act)
            effort_e[e] = float(act.effort); efforts[t, e] = effort_e[e]
        exiting = [e for e in range(N) if actions[e].exit]
        if exiting:   # pass 2: exits in the order of a salted per-entity rank, so same-round entrants' ids carry no entity information
            for e in sorted(exiting, key=lambda e: entrant_rank(salt, seed, t, int(d.fresh_seed[t, e]))):
                # retire the current identity now; the fresh identity makes this round's offer and pays e now
                alive[identity_of[e]] = False
                new = len(entity_of)
                gen_of_entity[e] += 1
                entity_of.append(e); identity_of[e] = new; identity_round.append(t); generation.append(gen_of_entity[e]); alive.append(True)
                caps_id = np.append(caps_id, caps_entity[e]); banned_until = np.append(banned_until, 0)
                ledger.grow(new + 1)
                ledger.charge_entry(t, new, cfg.e)
        for e in range(N):   # pass 3: offers under the current identity
            ident = identity_of[e]; act = actions[e]
            if t < banned_until[ident] or act.offer is None:
                continue
            offers[ident] = Offer(claim=float(act.offer.claim), bid=float(act.offer.bid))
            claims[t, e] = offers[ident].claim
        offers = dict(sorted(offers.items()))    # id order, never entity order: a rule must not learn which entity a new id belongs to
        M = len(entity_of)
        ent_arr = np.array(entity_of, dtype=np.int64)
        if M == N:
            tie_key = np.array(d.tie_key[t], copy=True)
        else:   # replacement identities: one-way keyed streams; live ones by (entity secret, generation), retired ones by identity
            secrets = [identity_secret(salt, seed, t, int(d.fresh_seed[t, entity_of[i]]), generation[i]) if alive[i] else retired_secret(salt, seed, t, i)
                       for i in range(N, M)]
            tie_key = np.concatenate([d.tie_key[t], fresh_tie_keys(secrets, J)], axis=1)
        tie_key.setflags(write=False)
        memory["tie_key"] = tie_key
        values_ro = values_t.copy(); values_ro.setflags(write=False)
        hist = tuple(records_all)
        view = StateView(t=t, T=T, N=M, audits_left=allowance, audit_u=float(d.audit_u[t]), audit_key=d.audit_key[t],
                         banned_until=banned_until, bond=ledger.bond, capacity=caps_id, escrow={}, history=hist, memory=memory)
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
            ids = np.fromiter(assignment.values(), dtype=np.int64, count=len(assignment))
            ents = ent_arr[ids]
            pay = np.array([payments[j] for j in assignment], dtype=float)
            ledger.funding[t] += np.bincount(ids, weights=pay, minlength=M)
            escrow = dict(zip(jobs.tolist(), pay.tolist()))
            owner = dict(assignment)
            slots = np.zeros(len(ents), dtype=np.int64); seen = np.zeros(N, dtype=np.int64)
            for n, e in enumerate(ents.tolist()):
                slots[n] = seen[e]; seen[e] += 1
            noise = d.noise[t, ents, slots].copy()
            rnoise = {i: replacement_noise(salt, seed, t, int(d.fresh_seed[t, entity_of[i]]), generation[i], cfg.kmax, cfg.sigma)
                      for i in set(ids.tolist()) if i >= N}          # one stream per replacement identity per round
            for n, i in enumerate(ids.tolist()):      # replacement identities deliver with salted noise, never the entity's public stream
                if i >= N:
                    noise[n] = rnoise[i][slots[n]]
            y = effort_e[ents] + noise
            value_total += float((values_t[jobs] * y).sum())
            counts_e = np.bincount(ents, minlength=N)
            counts_id = np.bincount(ids, minlength=M)
            ledger.cost[t] += counts_id * (a_arr[ent_arr] + b_arr[ent_arr] * effort_e[ent_arr])
            served[t] = counts_e
            delivered = dict(zip(jobs.tolist(), y.tolist()))
        view_a = StateView(t=t, T=T, N=M, audits_left=allowance, audit_u=float(d.audit_u[t]), audit_key=d.audit_key[t],
                           banned_until=banned_until, bond=ledger.bond, capacity=caps_id, escrow=escrow, history=hist, memory=memory)
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
        failed_e = np.zeros(N, dtype=np.int64)
        for r in records:
            if r.failed:
                failed_e[entity_of[r.provider]] += 1
                failed_jobs_of.setdefault(r.provider, []).append(r.job)
        failures[t] = failed_e
        for ident, rounds in cons.bans.items():
            banned_until[ident] = max(int(banned_until[ident]), t + int(rounds) + 1)
        refunded_e = np.zeros(N)
        for j, amt in cons.refunds.items():
            refunded_e[entity_of[owner[j]]] += amt
        ledger.settle(t, escrow, owner, cons, failed_jobs_of)
        ledger.check_conservation(escrow_outstanding=0.0)
        records_all.append(RoundRecord(t=t, offers=MappingProxyType(dict(offers)), assignment=MappingProxyType(dict(assignment)),
                                       payments=MappingProxyType(dict(payments)), audits=records, consequences=_frozen(cons)))
        audited_e = np.zeros(N, dtype=np.int64)
        for r in records:
            audited_e[entity_of[r.provider]] += 1
        funding_e = np.bincount(ent_arr, weights=ledger.funding[t], minlength=N)
        for e in range(N):
            histories[e].append(int(served[t, e]), float(funding_e[e]), int(audited_e[e]), int(failed_e[e]),
                                float(refunded_e[e]), int(banned_until[identity_of[e]]))

    ledger.terminal_settlement()
    ledger.check_conservation(escrow_outstanding=0.0)
    ent_final = np.array(entity_of, dtype=np.int64)
    identity_profit = ledger.profit()
    profit = np.bincount(ent_final, weights=identity_profit, minlength=N)
    cost = float(ledger.cost.sum()); entry = float(ledger.entry.sum())
    audit_cost = min(float(ledger.audit_cost.sum()), float(cfg.budget))
    W = value_total - cost - entry - audit_cost
    buyer_surplus = value_total - float(ledger.funding.sum()) + ledger.buyer_credit()
    return EpisodeResult(sstar=sstar_v, profit=profit, value=value_total, cost=cost, entry=entry, audit_cost=audit_cost,
                         served=served, audits=audits, failures=failures, claims=claims, efforts=efforts,
                         buyer_surplus=buyer_surplus, W=W, history=tuple(records_all), ledger=ledger,
                         n_identities=len(entity_of), entity_of=tuple(entity_of), identity_round=tuple(identity_round),
                         identity_generation=tuple(generation), identity_profit=identity_profit)
