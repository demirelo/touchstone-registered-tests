"""One-command reproduction of the protocol-v2 report under the recorded 1-ulp deviation (author's decision, 2026-11-04).
`scripts/reproduce.py` is frozen at the lock and runs the report with the registered `draw/instances.json`, whose
fresh-market configurations differ from the evaluation platform's in the last binary digit, so its strict verification
refuses the records. This wrapper does what reproduce.py does (unpack, clone, verify and check out tag protocol-v2,
artifact check, environment check) and then:
  1. checks, from the packed files alone, that `deviation/instances_container_configs.json` differs from the registered
     instance file only in fresh-market `calibrated_cfg` floats, each by at most one unit in the last place;
  2. runs the tagged report's --check with that file.
Exit 0 means every table is reproduced under the disclosed substitution.

Usage: reproduce_deviation.py --artifact release/touchstone-v2.tar.gz [--repo PATH_OR_URL]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cfg_ulp import diffs  # noqa: E402

TOP = "touchstone-v2"
SUB = "report/deviation/instances_container_configs.json"


def substitution_problems(registered: dict, substituted: dict) -> list[str]:
    out = []
    for k in sorted(set(registered) | set(substituted)):
        if k != "markets" and registered.get(k) != substituted.get(k):
            out.append(f"{k}: differs outside the market configurations")
    rm, sm = registered.get("markets", {}), substituted.get("markets", {})
    if set(rm) != set(sm):
        out.append("the market sets differ")
    for m in sorted(set(rm) & set(sm)):
        a, b = rm[m], sm[m]
        for k in sorted(set(a) | set(b)):
            if k == "calibrated_cfg" and m.startswith("fresh"):
                for path, x, y, u in diffs(a[k], b[k]):
                    if u is None or u > 1:
                        out.append(f"{m}{path}: {x!r} -> {y!r} is not within one ulp")
            elif a.get(k) != b.get(k):
                out.append(f"{m}.{k}: differs (only fresh-market calibrated_cfg may)")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True); ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[3]))
    a = ap.parse_args(argv)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        with tarfile.open(a.artifact) as tf:
            tf.extractall(tmp / "u", filter="data")
        u = tmp / "u" / TOP; clone = tmp / "clone"
        subprocess.run(["git", "clone", "-q", str(a.repo), str(clone)], check=True)
        if subprocess.run(["git", "-C", str(clone), "tag", "-v", "protocol-v2"], capture_output=True).returncode != 0:
            print("refused: tag protocol-v2 is missing, unsigned, or does not verify"); return 1
        subprocess.run(["git", "-C", str(clone), "checkout", "-q", "protocol-v2"], check=True)
        sys.path.insert(0, str(clone))
        from scripts.artifact_v2 import check
        from scripts.reproduce import environment_problems
        problems = check(a.artifact, repo=clone) + environment_problems(clone / "uv.lock")
        if not (u / SUB).exists():
            problems.append(f"{SUB}: not in the artifact")
        else:
            problems += substitution_problems(json.loads((u / "draw" / "instances.json").read_text()), json.loads((u / SUB).read_text()))
        if problems:
            print("refused:\n" + "\n".join(problems)); return 1
        r = subprocess.run([sys.executable, "scripts/report_v2.py", "--out", str(u / "eval"), "--protocol", str(u / "experiments" / "protocol-v2.yaml"),
                            "--instances", str(u / SUB), "--h4", str(u / "draw" / "h4.json"), "--report", str(u / "report"),
                            "--params", str(u / "experiments" / "v2" / "params.json"), "--check"], cwd=clone, capture_output=True, text=True)
        print(r.stdout, end=""); print(r.stderr, end="", file=sys.stderr)
        return r.returncode


if __name__ == "__main__":
    sys.exit(main())
