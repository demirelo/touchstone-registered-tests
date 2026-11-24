"""Post-analysis extract for the paper (not part of the stamped manifest): R3's audit counts and full audit allocation per
winner set, rate and market, from exactly the diagnostics records the committed collector (rep_collect.collect) accepts
for expectation 5, the list of cells whose continued search produced the primary winner, the collector's status fields,
and the sha256 of the run's analysis, draw and manifest, so that replication_paper.py can refuse a stale extract.

Exactness: the collector is run unchanged. Four of its module functions are wrapped for the duration of the call only:
diag_ok and cont_diag_ok remember the diagnostics row they accept, _audit_of returns the same (audited, served) tuple
with that row's allocation and the winner's replacement switch x attached, and select_winner records which
continuation record produced which winner kind. Nothing the collector decides changes. Binding: the analysis is
recomputed from the same collected records exactly as rep_v2's analyse stage does, and the extract is written only if
it is byte-identical to the run's analysis.json.

Usage: replication_extract.py --out <followup3-rep dir> --manifest <manifest> --draw <draw.json> --write <json>"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

CATS = ("honest_replacement", "honest_initial", "focal")
STEM = re.compile(r"^(menu|cthr)-p(0|0\.03|0\.05)__fresh([0-5])@rho0\.2__(F111|Cstar|F000)__D2\+H3__profit(__churn(0\.03|0\.05))?$")
CTHR_POLICY = "Cstar"          # every cthr-directory cell is C-thr, run on the C* policy slot
WINNER_KINDS = ("continued", "unresolved")


def sha_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def allocation(shares: dict) -> dict:
    """The draft-10 audit allocation (docs/revision/posthoc/churn_block.py, audit_allocation) for one winner: per-episode
    [served, audited] counts summed over episodes; young = the first age bin (younger than ten rounds); established =
    the other bins. A zero denominator gives None."""
    per = shares["per_episode"]
    nb = len(per[0]["focal"]) if per else 0
    t = {c: [[sum(e[c][b][j] for e in per) for j in (0, 1)] for b in range(nb)] for c in CATS}
    served = sum(t[c][b][0] for c in CATS for b in range(nb))
    audits = sum(t[c][b][1] for c in CATS for b in range(nb))
    yh = [t["honest_replacement"][0][j] + t["honest_initial"][0][j] for j in (0, 1)]
    eh = [sum(t[c][b][j] for c in ("honest_replacement", "honest_initial") for b in range(1, nb)) for j in (0, 1)]
    fo = [sum(t["focal"][b][j] for b in range(nb)) for j in (0, 1)]
    div = lambda a, b: a / b if b else None
    return {"young_honest_job_share": div(yh[0], served), "young_honest_audit_share": div(yh[1], audits),
            "established_honest_audit_rate": div(eh[1], eh[0]), "focal_job_share": div(fo[0], served),
            "focal_audit_rate": div(fo[1], fo[0])}


class Counts(tuple):
    """(audited, served), as the collector stores it, carrying the allocation of the same shares."""
    alloc: dict


def parse_cell(stem: str) -> dict:
    """'menu-p0.05__fresh3@rho0.2__F111__D2+H3__profit__churn0.05' -> kind, rate, market, policy. Refuses any other
    shape, a churn suffix that disagrees with the rate, a churn suffix at p = 0, or a cthr cell on another policy."""
    m = STEM.match(stem)
    if not m or (m.group(2) == "0") != (m.group(6) is None) or (m.group(6) and m.group(6) != m.group(2)) or \
            (m.group(1) == "cthr" and m.group(4) != CTHR_POLICY):
        raise ValueError(f"unexpected cell identity: {stem}")
    return {"kind": m.group(1), "rate": m.group(2), "market": "rep" + m.group(3), "policy": m.group(4)}


def build(col: dict, winners: dict, safe, hashes: dict) -> dict:
    """The extract from the collector output, the recorded winner kind per continuation key, the collector's file-name
    function and the input hashes. The continued list holds the flagged cells whose primary winner is the continued
    one; its length must equal the collector's continued plus unresolved counts."""
    stems = sorted(safe(k) for k, kw in winners.items() if kw in WINNER_KINDS)
    if len(set(stems)) != len(stems):
        raise ValueError("duplicate continued cell")
    if len(stems) != sum(col["counts"].get(k, 0) for k in WINNER_KINDS):
        raise ValueError("the continued list disagrees with the collector's counts")
    sets = ("frozen", "primary")
    return {"audit": {s: {rk: {m: [v[0], v[1]] for m, v in sorted(ms.items())} for rk, ms in sorted(col["audit"][s].items())} for s in sets},
            "alloc": {s: {rk: {m: v.alloc for m, v in sorted(ms.items())} for rk, ms in sorted(col["audit"][s].items())} for s in sets},
            "counts": col["counts"], "continued": [dict(parse_cell(s), stem=s) for s in stems],
            "status": {k: col[k] for k in ("problems", "unscorable", "round1_mismatch", "gate_ok")}, "binding": hashes}


def recompute(col: dict, confirmatory: bool, analyse) -> str:
    """analysis.json as rep_v2.stage_analyse writes it, from these collected records (default resamples and seed)."""
    res = {k: col[k] for k in ("counts", "round1_mismatch", "gate_ok", "problems", "unscorable")}
    res["confirmatory"] = confirmatory
    for name in ("primary", "frozen"):
        g = col[name]
        res[name] = ("not available (a round-1 mismatch or a continued winner without an identical gate)" if g is None
                     else analyse(g, {rk: {m: tuple(v) for m, v in ms.items()} for rk, ms in col["audit"][name].items()}))
    return json.dumps(res, indent=1, sort_keys=True) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--manifest", required=True); ap.add_argument("--draw", required=True)
    ap.add_argument("--write", required=True)
    a = ap.parse_args(argv)
    import rep_v2 as V
    import rep_collect as C
    import replication_analysis as RA
    import revision_v2 as R
    ns = V.main.__globals__["argparse"].Namespace(out=a.out, manifest=a.manifest, draw=a.draw, smoke=False,
                                                  params=str(V.ROOT / "experiments/v2/params.json"))
    V._require(ns)
    c = V._context(ns); jobs = V._jobs_by_dir(c, False)
    winners, last = {}, {}
    orig = {k: getattr(C, k) for k in ("_audit_of", "select_winner", "diag_ok", "cont_diag_ok")}

    def diag_ok(row, *a, **k):
        ok = orig["diag_ok"](row, *a, **k)
        last["row"] = row if ok else None
        return ok

    def cont_diag_ok(rec, *a, **k):
        ok = orig["cont_diag_ok"](rec, *a, **k)
        last["row"] = rec if ok else None
        return ok

    def audit_of(shares):
        row = last.pop("row", None)
        if row is None or row.get("shares") is not shares:
            raise RuntimeError("an audit count without the accepted diagnostics row")
        out = Counts(orig["_audit_of"](shares)); out.alloc = dict(allocation(shares), x=(row.get("knobs") or {}).get("x")); return out

    def select_winner(frozen, rec):
        g, kw = orig["select_winner"](frozen, rec)
        if rec is not None:
            winners[rec["id"]] = kw
        return g, kw

    C._audit_of, C.select_winner, C.diag_ok, C.cont_diag_ok = audit_of, select_winner, diag_ok, cont_diag_ok
    try:
        col = C.collect(Path(a.out), jobs, gate=V.gate_item(jobs, a.out), smoke=False)
    finally:
        for k, f in orig.items():
            setattr(C, k, f)
    recomputed = recompute(col, c.confirmatory, RA.analyse)
    if recomputed != (Path(a.out) / "analysis.json").read_text():
        raise SystemExit("the analysis recomputed from the collected records differs from analysis.json")
    hashes = {"analysis": sha_file(Path(a.out) / "analysis.json"), "draw": sha_file(a.draw), "manifest": sha_file(a.manifest),
              "recomputed": True}
    res = build(col, winners, R._safe, hashes)
    Path(a.write).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
