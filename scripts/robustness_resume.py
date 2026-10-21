"""Resume of robustness v1 after the bank-order verification bug (pod 1, 2026-10-21).

`verify_bank_group` in scripts/explore_attackers.py rebuilt a bank from `list(doc["sources"])`, but records are written with
sorted keys, so for the X6 group (profiles ...c2_staggered sort before ...c2_synchronised) the rebuilt member order, and its
hash, differed from the bank as built, although no source had changed. This script supplies a check that rebuilds in the
job's canonical source order (the manifest's `bank_sources`), and runs the remaining stages with it. The runner and the
policy module are unchanged, so every existing record stays valid: the script refuses to run unless their hashes equal those
in the records, and it pins the records' commit for the provenance comparison (TOUCHSTONE_GIT_COMMIT)."""
from __future__ import annotations

import argparse, hashlib, json, multiprocessing as mp, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RECORDS_COMMIT = "25bc661025064e41eb6b5d94fbeeaf3b9f106794"
ROOT = Path(__file__).resolve().parents[1]


def check_runner_matches(rec: dict) -> None:
    run = hashlib.sha256((ROOT / "scripts/explore_attackers.py").read_bytes()).hexdigest()
    pol = hashlib.sha256((ROOT / "sim/policies/exploratory.py").read_bytes()).hexdigest()
    p = rec["provenance"]
    if p.get("runner_sha256") != run or p.get("policy_sha256") != pol:
        raise SystemExit("the runner or the policy module differs from the records' versions; this resume would mix code versions")


def verify_bank_group_ordered(out, job: dict) -> dict:
    import scripts.explore_attackers as X
    g = job.get("bank_group", job["family"]); doc = X.read_record(Path(out) / f"bank_{g}.json")
    if doc is None:
        raise SystemExit(f"{job['name']}: no bank document for group {g}")
    stored = set(doc["sources"])
    names = [n for n in (job.get("bank_sources") or []) if n in stored]
    if set(names) != stored:
        raise SystemExit(f"bank {g}: the job's source list does not cover the stored sources")
    emb = list(doc.get("embed_sources") or {})
    recs = {n: X.read_record(Path(out) / "search" / f"{n}.json") for n in names + emb}
    if any(v is None for v in recs.values()):
        raise SystemExit(f"bank {g}: a source search record is missing")
    again = X.build_bank_doc(job["family"], {n: recs[n] for n in names}, list(X.RULES), None, names=names, embed={n: recs[n] for n in emb},
                             group=doc.get("group"))
    if again["bank_hash"] != doc["bank_hash"]:
        raise SystemExit(f"bank {g}: the bank no longer matches its current sources; rebuild the bank and its downstream records")
    return doc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="reference,evaluate"); ap.add_argument("--variants", default="headline")
    ap.add_argument("--rules", default="all"); ap.add_argument("--families", default="all"); ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", default="results/robustness"); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--pilot", action="store_true")
    a = ap.parse_args()
    os.environ["TOUCHSTONE_GIT_COMMIT"] = RECORDS_COMMIT
    try:
        mp.set_start_method("fork", force=True)            # workers inherit the corrected check
    except RuntimeError:
        pass
    import scripts.explore_attackers as X
    import scripts.robustness_v1 as R
    probe = next(Path(a.out).glob("search/*.json"), None)
    if probe is None:
        raise SystemExit("no search records to resume from")
    check_runner_matches(json.loads(probe.read_text()))
    X.verify_bank_group = verify_bank_group_ordered
    print(json.dumps(R.run(vars(a))))


if __name__ == "__main__":
    main()
