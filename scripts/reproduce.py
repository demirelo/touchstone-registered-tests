"""One-command reproduction of the protocol-v2 report (design 10; operations plan Task 10): unpack the release artifact,
clone the repository at the signed tag protocol-v2, and run the report's --check on the packed records and inputs. Exit 0
means every table is reproduced; otherwise the differences are printed."""
from __future__ import annotations

import argparse
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP = "touchstone-v2"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True); ap.add_argument("--repo", default=str(ROOT), help="a clone source: path or URL")
    a = ap.parse_args(argv)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        with tarfile.open(a.artifact) as tf:
            tf.extractall(tmp / "u", filter="data")
        u = tmp / "u" / TOP; clone = tmp / "clone"
        subprocess.run(["git", "clone", "-q", str(a.repo), str(clone)], check=True)
        subprocess.run(["git", "-C", str(clone), "checkout", "-q", "protocol-v2"], check=True)
        r = subprocess.run([sys.executable, "scripts/report_v2.py", "--out", str(u / "eval"), "--protocol", str(u / "experiments" / "protocol-v2.yaml"),
                            "--instances", str(u / "draw" / "instances.json"), "--h4", str(u / "draw" / "h4.json"), "--report", str(u / "report"),
                            "--params", str(u / "experiments" / "v2" / "params.json"), "--check"], cwd=clone, capture_output=True, text=True)
        print(r.stdout, end=""); print(r.stderr, end="", file=sys.stderr)
        return r.returncode


if __name__ == "__main__":
    sys.exit(main())
