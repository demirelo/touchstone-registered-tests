from __future__ import annotations

import math

import numpy as np

from .mechanisms.base import AuditRecord, Consequences, L_MAX, Offers, StateView


def _finite(x) -> bool:
    return isinstance(x, (int, float, np.floating, np.integer)) and math.isfinite(float(x))


def validate_assignment(assignment: dict[int, int], values_t: np.ndarray, offers: Offers, view: StateView) -> None:
    J = len(values_t)
    counts = np.zeros(view.N, dtype=np.int64)
    for j, i in assignment.items():
        if not (0 <= int(j) < J):
            raise ValueError(f"assignment names job {j} out of range")
        if i not in offers:
            raise ValueError(f"assignment to provider {i} with no offer")
        if not view.is_active(i):
            raise ValueError(f"assignment to banned provider {i}")
        counts[i] += 1
    over = np.flatnonzero(counts > view.capacity)
    if over.size:
        raise ValueError(f"capacity exceeded for providers {over.tolist()}")


def validate_payments(payments: dict[int, float], assignment: dict[int, int], values_t: np.ndarray, offers: Offers) -> None:
    if set(payments.keys()) != set(assignment.keys()):
        raise ValueError("payments must cover exactly the assigned jobs")
    for j, p in payments.items():
        if not _finite(p) or p < 0:
            raise ValueError(f"payment for job {j} must be finite and non-negative")
        if p > values_t[j] * offers[assignment[j]].claim + 1e-12:
            raise ValueError(f"payment for job {j} exceeds what the buyer accepts")


def validate_audits(audit_list: list[int], assignment: dict[int, int], view: StateView) -> None:
    if len(set(audit_list)) != len(audit_list):
        raise ValueError("audit list must be unique")
    for j in audit_list:
        if j not in assignment:
            raise ValueError(f"audit of unserved job {j}")
    if len(audit_list) > view.audits_left:
        raise ValueError("audit list exceeds the remaining allowance")


def validate_consequences(cons: Consequences, records: tuple[AuditRecord, ...], escrow: dict, owner: dict,
                          bond: np.ndarray, recent_receipts: np.ndarray, active: set[int]) -> None:
    failed_jobs = {r.job for r in records if r.failed}
    failed_idents = {r.provider for r in records if r.failed}
    for job, amt in cons.refunds.items():
        if not _finite(amt) or amt < 0:
            raise ValueError(f"refund for job {job} must be finite and non-negative")
        if job not in failed_jobs:
            raise ValueError(f"refund for job {job} without a failed audit")
        if amt > escrow.get(job, 0.0) + 1e-12:
            raise ValueError(f"refund for job {job} exceeds its escrow")
    for ident, rounds in cons.bans.items():
        if isinstance(rounds, bool) or not isinstance(rounds, (int, np.integer)):
            raise ValueError(f"ban for identity {ident} must be an integer number of rounds")
        if ident not in failed_idents:
            raise ValueError(f"ban for identity {ident} without a failed audit")
        if not (0 < rounds <= L_MAX):
            raise ValueError(f"ban for identity {ident} must be in 1..{L_MAX}")
    bond_after = np.array(bond, dtype=float)
    for ident, amt in cons.forfeits.items():
        if not _finite(amt) or amt < 0:
            raise ValueError(f"forfeit for identity {ident} must be finite and non-negative")
        if ident not in failed_idents:
            raise ValueError(f"forfeit for identity {ident} without a failed audit")
        cap_escrow = sum(escrow.get(j, 0.0) for j in failed_jobs if owner.get(j) == ident)
        if amt > min(bond_after[ident], cap_escrow) + 1e-12:
            raise ValueError(f"forfeit for identity {ident} exceeds its bond or its failed escrow")
        bond_after[ident] -= amt
    for ident, amt in cons.releases.items():
        if not _finite(amt) or amt < 0:
            raise ValueError(f"release for identity {ident} must be finite and non-negative")
        if amt > bond_after[ident] + 1e-12:
            raise ValueError(f"release for identity {ident} exceeds its bond")
        bond_after[ident] -= amt
    for ident, amt in cons.holdbacks.items():
        if not _finite(amt) or amt < 0:
            raise ValueError(f"hold-back for identity {ident} must be finite and non-negative")
        if ident not in active:
            raise ValueError(f"hold-back for identity {ident} without an offer this round")
        if bond_after[ident] + amt > recent_receipts[ident] + 1e-12:
            raise ValueError(f"hold-back for identity {ident} exceeds the H_MAX-round receipts cap")
