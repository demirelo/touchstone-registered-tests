"""The release artifact (design 10; operations plan Task 10). results/ is not tracked by git, so the evaluation records,
the draw (record with headers, instances, H4 decision), the report, the released H4 bundle, the promoted inputs, the
protocol and its upgraded proof, the paper sources, and uv.lock are packed into release/touchstone-v2.tar.gz with a
MANIFEST.json of SHA-256s. --check verifies every listed hash, the required files, the freeze records' hashes against the
packed records, the draw record against the packed protocol and proof, the packed instances against the ones the draw
gives (all but calibrated_cfg, the slow step), the signed tag protocol-v2 in the repository, and that every packed
registration input (experiments/) equals the file at that tag."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.draw_v2 import Refused, instances  # noqa: E402
from scripts.revision_v2 import path_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TOP = "touchstone-v2"
TAG = "protocol-v2"
REQUIRED = ("experiments/protocol-v2.yaml", "experiments/protocol-v2.yaml.ots", "experiments/v2/params.json", "draw/draw.json", "draw/instances.json",
            "draw/h4.json", "report/report.json", "report/report.md", "paper/main.tex", "uv.lock")


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _files(src: Path, prefix: str) -> list[tuple[Path, str]]:
    src = Path(src)
    return [(p, f"{prefix}/{p.relative_to(src).as_posix()}") for p in sorted(src.rglob("*")) if p.is_file()] if src.exists() else []


def assemble(eval_dir, draw_dir, report_dir, h4_dir, out, repo=ROOT) -> Path:
    repo = Path(repo)
    files = (_files(eval_dir, "eval") + _files(draw_dir, "draw") + _files(report_dir, "report") + (_files(h4_dir, "h4") if h4_dir else [])
             + _files(repo / "experiments" / "v2", "experiments/v2") + _files(repo / "paper", "paper")
             + [(repo / rel, rel) for rel in ("experiments/protocol-v2.yaml", "experiments/protocol-v2.yaml.ots", "uv.lock") if (repo / rel).exists()])
    manifest = {arc: _sha(p.read_bytes()) for p, arc in files}
    out = Path(out); out.mkdir(parents=True, exist_ok=True); tar = out / f"{TOP}.tar.gz"
    with tarfile.open(tar, "w:gz") as tf:
        for p, arc in files:
            tf.add(p, arcname=f"{TOP}/{arc}")
        b = json.dumps(manifest, indent=1, sort_keys=True).encode(); ti = tarfile.TarInfo(f"{TOP}/MANIFEST.json"); ti.size = len(b)
        tf.addfile(ti, io.BytesIO(b))
    return tar


def _members(tar: Path) -> dict:
    with tarfile.open(tar) as tf:
        return {m.name[len(TOP) + 1:]: tf.extractfile(m).read() for m in tf.getmembers() if m.isfile() and m.name.startswith(TOP + "/")}


def _draw_problems(files: dict, offset: int) -> list[str]:
    need = ("draw/draw.json", "draw/instances.json", "experiments/protocol-v2.yaml", "experiments/protocol-v2.yaml.ots")
    if any(n not in files for n in need):
        return []                                                  # reported as required files
    try:
        draw, packed = json.loads(files["draw/draw.json"]), json.loads(files["draw/instances.json"])
        got = instances(draw, files["experiments/protocol-v2.yaml"], files["experiments/protocol-v2.yaml.ots"], packed.get("published_height"),
                        offset, calibrate=False)
    except Refused as e:
        return [f"draw/draw.json: does not verify against the packed protocol and proof: {e}"]
    except (ValueError, KeyError, TypeError) as e:
        return [f"draw/draw.json or draw/instances.json: unreadable: {e!r}"]
    strip = {**packed, "markets": {k: {f: v for f, v in m.items() if f != "calibrated_cfg"} for k, m in packed.get("markets", {}).items()}}
    if json.loads(json.dumps(got, default=float)) != strip:
        return ["draw/instances.json: differs from the instances the packed draw gives"]
    if any("calibrated_cfg" not in m for m in packed["markets"].values()):
        return ["draw/instances.json: a market has no calibrated_cfg"]
    return []


def check(tar, repo=ROOT, offset: int = 144) -> list[str]:
    files = _members(Path(tar)); problems = []
    if "MANIFEST.json" not in files:
        return ["MANIFEST.json is missing"]
    manifest = json.loads(files.pop("MANIFEST.json"))
    for arc, h in manifest.items():
        if arc not in files:
            problems.append(f"{arc}: listed but missing")
        elif _sha(files[arc]) != h:
            problems.append(f"{arc}: hash differs from the manifest")
    problems += [f"{arc}: not in the manifest" for arc in files if arc not in manifest]
    problems += [f"{rel}: required file missing" for rel in REQUIRED if rel not in files]
    for arc, b in files.items():
        if arc.startswith("eval/freeze/") and arc.endswith(".json"):
            for rid, h in json.loads(b).get("records", {}).items():
                rel = path_of(Path("eval"), rid).as_posix()
                if rel not in files or _sha(files[rel]) != h:
                    problems.append(f"{arc}: frozen record {rid} is missing or its hash differs")
    problems += _draw_problems(files, offset)
    if subprocess.run(["git", "tag", "-v", TAG], cwd=Path(repo), capture_output=True, text=True).returncode != 0:
        problems.append(f"tag {TAG} is missing, unsigned, or does not verify")
        return problems
    for arc, b in files.items():                                   # the packed registration inputs are the tagged files
        if arc.startswith("experiments/"):
            tagged = subprocess.run(["git", "show", f"{TAG}:{arc}"], cwd=Path(repo), capture_output=True)
            if tagged.returncode != 0 or tagged.stdout != b:
                problems.append(f"{arc}: differs from the file at tag {TAG}")
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--assemble", action="store_true"); g.add_argument("--check", default=None, metavar="TARBALL")
    ap.add_argument("--eval"); ap.add_argument("--draw"); ap.add_argument("--report"); ap.add_argument("--h4", default=None)
    ap.add_argument("--out", default="release"); ap.add_argument("--repo", default=str(ROOT)); ap.add_argument("--offset", type=int, default=144)
    a = ap.parse_args(argv)
    if a.assemble:
        print(assemble(a.eval, a.draw, a.report, a.h4, a.out, a.repo))
        return 0
    problems = check(a.check, a.repo, a.offset)
    print("\n".join(problems) or "ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
