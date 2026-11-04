"""The check behind the 2026-11-04 deviation (1-ulp fresh-market configs). The run mode recalibrates each fresh market on
the pod (Linux x86); instances.json holds the configs computed on the Mac (arm64). For each market this checks that
(1) every evaluation record carries one config hash, equal to the hash of the config a Linux amd64 container recomputes,
(2) that config differs from the recorded one only in float values, each by at most one unit in the last place, and
(3) the runner's own verify passes on the records when given the container's configs. Writes nothing in the record
directories; the verify input with the container's configs goes to --work and is never the recorded instances.json."""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path


def _ord(x: float) -> int:
    i = struct.unpack("<q", struct.pack("<d", float(x)))[0]
    return i if i >= 0 else -(1 << 63) - i


def diffs(rec, lin, path: str = "") -> list[tuple[str, object, object, int | None]]:
    """(path, recorded, recomputed, ulps); ulps is None for any difference that is not between two floats."""
    if isinstance(rec, dict) and isinstance(lin, dict):
        return [d for k in sorted(set(rec) | set(lin)) for d in diffs(rec.get(k, KeyError), lin.get(k, KeyError), f"{path}.{k}")]
    if isinstance(rec, list) and isinstance(lin, list):
        if len(rec) != len(lin):
            return [(path, len(rec), len(lin), None)]
        return [d for i, (a, b) in enumerate(zip(rec, lin)) for d in diffs(a, b, f"{path}[{i}]")]
    if rec == lin and type(rec) is type(lin):
        return []
    if type(rec) is float and type(lin) is float:
        return [(path, rec, lin, abs(_ord(rec) - _ord(lin)))]
    return [(path, rec, lin, None)]


def within(ds, max_ulps: int) -> bool:
    return all(u is not None and u <= max_ulps for *_, u in ds)


def pod_hash_ok(pod_hashes: set, container_hash: str) -> bool:
    return pod_hashes == {container_hash}


def sha_json(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=float).encode()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", required=True); ap.add_argument("--linux", required=True); ap.add_argument("--eval", required=True)
    ap.add_argument("--markets", required=True); ap.add_argument("--verify", required=True, help="results/pods/verify_market.sh")
    ap.add_argument("--work", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    inst = json.loads(Path(a.instances).read_text()); lin = json.loads(Path(a.linux).read_text()); work = Path(a.work); work.mkdir(parents=True, exist_ok=True)
    alt = json.loads(json.dumps(inst)); markets = a.markets.split(",")
    for m in markets:
        alt["markets"][m]["calibrated_cfg"] = lin[m]
    alt_path = work / "instances_container_configs.json"; alt_path.write_text(json.dumps(alt))
    rep = {"instances_sha256": hashlib.sha256(Path(a.instances).read_bytes()).hexdigest(), "linux_sha256": hashlib.sha256(Path(a.linux).read_bytes()).hexdigest(), "markets": {}}
    for m in markets:
        ds = diffs(inst["markets"][m]["calibrated_cfg"], lin[m])
        pods = {json.loads(Path(f).read_text())["provenance"]["cfg_sha256"] for f in glob.glob(f"{a.eval}/{m}/evaluate/*.json")}
        v = subprocess.run(["bash", a.verify, m, m], env={"PATH": "/usr/bin:/bin:/usr/local/bin:" + str(Path.home() / ".local/bin"), "HOME": str(Path.home()),
                           "INSTANCES": str(alt_path)}, capture_output=True, text=True)
        r = {"container_hash": sha_json(lin[m]), "pod_hashes": sorted(pods), "pod_hash_ok": pod_hash_ok(pods, sha_json(lin[m])),
             "recorded_hash": sha_json(inst["markets"][m]["calibrated_cfg"]), "differences": [[p, x, y, u] for p, x, y, u in ds],
             "within_one_ulp": within(ds, 1), "verify_exit": v.returncode, "verify": v.stdout.strip()[-300:]}
        r["ok"] = r["pod_hash_ok"] and r["within_one_ulp"] and v.returncode == 0
        rep["markets"][m] = r
        print(m, "ok" if r["ok"] else "NOT OK", f"pod_hash_ok={r['pod_hash_ok']} diffs={len(ds)} max_ulps={max([u or 0 for *_, u in ds], default=0)} verify_exit={v.returncode}")
    rep["ok"] = all(r["ok"] for r in rep["markets"].values())
    Path(a.out).write_text(json.dumps(rep, indent=1)); return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
