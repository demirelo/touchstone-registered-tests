from __future__ import annotations

import json
from dataclasses import dataclass, field

from .cell import Cell, SeedCache, run_focal
from .policies.families import FAMILIES, Family, embed_d1_in_d2, embed_d2_in_h3, embed_d2_in_h3_exit, exact_key


def bank_families() -> dict:
    """Amendment 2: the families a bank may target, from the registry (D1, D2, D2+H3, and H2 once the bundle is present)."""
    from .registry import available_families
    return available_families()


@dataclass
class BankPass:
    ranked: list            # (knobs, f, origin) descending
    best_knobs: dict | None
    best_f: float
    best_origin: str | None
    improved: bool


@dataclass
class Bank:
    entries: list = field(default_factory=list)   # (family_name, knobs, origin)

    def add(self, family_name: str, knobs: dict, origin: str) -> None:
        if family_name not in bank_families():
            raise ValueError(f"unknown family {family_name}")
        if not any(f == family_name and exact_key(k) == exact_key(knobs) for f, k, _ in self.entries):
            self.entries.append((family_name, dict(knobs), origin))

    def _compatible(self, target: str) -> list[tuple[dict, str]]:
        """The typed compatibility filter: a member enters its own family as is, D1 enters D2 through the embedding, and
        (amendment 2) the complete D2-compatible set enters D2+H3 through both embeddings, x = 0 before x = 1, in entry
        order with the origin suffixed; the target's exact corners follow, de-duplicated by exact key."""
        out, seen = [], set()

        def take(m: dict, origin: str) -> None:
            key = exact_key(m)
            if key not in seen:
                seen.add(key); out.append((m, origin))

        for f, k, origin in self.entries:
            if f == target:
                take(dict(k), origin)
            elif f == "D1" and target == "D2":
                take(embed_d1_in_d2(k), origin)
            elif target == "D2+H3" and f in ("D1", "D2"):
                d2 = embed_d1_in_d2(k) if f == "D1" else dict(k)
                take(embed_d2_in_h3(d2), origin + "|x=0"); take(embed_d2_in_h3_exit(d2), origin + "|x=1")
        for c in bank_families()[target].corners():      # the target family's exact-corner controls are members too (spec 8)
            take(c, "corner")
        return out

    def members_for(self, family_name: str) -> list[dict]:
        return [m for m, _ in self._compatible(family_name)]

    def projected_members_for(self, family_name: str) -> list[dict]:
        fam = bank_families()[family_name]
        out, seen = [], set()
        for m, _ in self._compatible(family_name):
            p = fam.project(m); key = exact_key(p)
            if key not in seen:
                seen.add(key); out.append(p)
        return out

    def evaluate(self, cell: Cell, family: Family, cache: SeedCache, known: dict | None = None) -> list[tuple[dict, float, str]]:
        """Members as attacks on the cell's seeds; a member whose exact key is in `known` takes that value without a run."""
        known = known or {}
        scored = []
        for m, origin in self._compatible(family.name):
            key = exact_key(m)
            f = known[key] if key in known else float(run_focal(cell, lambda m=m: family.make(m), cache).normalized.mean())
            scored.append((m, f, origin))
        scored.sort(key=lambda t: -t[1])
        return scored

    def bank_pass(self, cell: Cell, family: Family, cache: SeedCache, incumbent_f: float, known: dict | None = None) -> BankPass:
        ranked = self.evaluate(cell, family, cache, known)
        if not ranked:
            return BankPass(ranked=[], best_knobs=None, best_f=float(incumbent_f), best_origin=None, improved=False)
        m, f, origin = ranked[0]
        improved = f > incumbent_f
        return BankPass(ranked=ranked, best_knobs=m if improved else None, best_f=f if improved else float(incumbent_f),
                        best_origin=origin if improved else None, improved=improved)

    @staticmethod
    def transfer_rows(cell_name: str, incumbent_f: float, bp: BankPass) -> dict:
        return {"cell": cell_name, "incumbent": float(incumbent_f), "best_bank": float(bp.ranked[0][1]) if bp.ranked else None,
                "best_origin": bp.ranked[0][2] if bp.ranked else None, "improved": bool(bp.improved)}

    def to_json(self) -> str:
        return json.dumps([{"family": f, "knobs": k, "origin": o} for f, k, o in self.entries], indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Bank":
        b = cls()
        for e in json.loads(text):
            b.add(e["family"], e["knobs"], e["origin"])
        return b
