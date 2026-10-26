"""One-command reproduction of the protocol-v2 report (design 10; operations plan Task 10; final review K12): unpack the
release artifact, clone the repository, verify the signed tag protocol-v2 and check it out, run the artifact check
(manifest, required files, frozen records, the draw and instances, packed registration inputs equal to the tagged
files), check that this Python satisfies the clone's uv.lock and that every locked runtime dependency of the project is
installed at its locked version, and run the real report's --check (report.json and report.md) on the packed
records. Exit 0 means every table is reproduced; otherwise the problems or differences are printed."""
from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP = "touchstone-v2"


def _installed(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


_real_installed = _installed


def _python() -> str:
    return platform.python_version()


def environment_problems(lock: Path) -> list[str]:
    """This Python satisfies requires-python, and every package the project needs at run time (its dependencies, followed
    transitively, whose markers hold here; dev dependencies are not followed) is installed at a locked version."""
    from packaging.markers import Marker
    from packaging.specifiers import SpecifierSet
    data = tomllib.loads(Path(lock).read_text()); out = []
    req = data.get("requires-python")
    if req and _python() not in SpecifierSet(req):
        out.append(f"Python {_python()} does not satisfy the locked requires-python {req}")
    pkgs = {}
    for pkg in data.get("package", []):
        pkgs.setdefault(pkg["name"], []).append(pkg)
    roots = [pkg for pkg in data.get("package", []) if "editable" in (pkg.get("source") or {})]
    if not roots:
        return out + ["uv.lock names no editable project package"]

    def holds(dep):
        return "marker" not in dep or Marker(dep["marker"]).evaluate({"extra": ""})
    seen, todo = set(), [d for r in roots for d in r.get("dependencies", []) if holds(d)]
    while todo:
        dep = todo.pop(); name = dep["name"]
        if name in seen:
            continue
        seen.add(name)
        if name not in pkgs:
            out.append(f"{name}: needed but not in uv.lock"); continue
        locked = {p.get("version") for p in pkgs[name]}; got = _installed(name)
        if got is None:
            out.append(f"{name}: not installed (locked {', '.join(sorted(map(str, locked)))})")
        elif got not in locked:
            out.append(f"{name}: installed {got}, locked {', '.join(sorted(map(str, locked)))}")
        todo += [d for p in pkgs[name] if dep.get("version") in (None, p.get("version")) for d in p.get("dependencies", []) if holds(d)]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True); ap.add_argument("--repo", default=str(ROOT), help="a clone source: path or URL")
    ap.add_argument("--smoke", action="store_true", help="the report's smoke seeds (tests only)")
    ap.add_argument("--offset", type=int, default=144, help="the registered offset H = A + offset")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(ROOT))
    from scripts.artifact_v2 import check
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        with tarfile.open(a.artifact) as tf:
            tf.extractall(tmp / "u", filter="data")
        u = tmp / "u" / TOP; clone = tmp / "clone"
        subprocess.run(["git", "clone", "-q", str(a.repo), str(clone)], check=True)
        if subprocess.run(["git", "-C", str(clone), "tag", "-v", "protocol-v2"], capture_output=True).returncode != 0:
            print("refused: tag protocol-v2 is missing, unsigned, or does not verify"); return 1
        subprocess.run(["git", "-C", str(clone), "checkout", "-q", "protocol-v2"], check=True)
        problems = check(a.artifact, repo=clone, offset=a.offset) + environment_problems(clone / "uv.lock")
        if problems:
            print("refused:\n" + "\n".join(problems)); return 1
        r = subprocess.run([sys.executable, "scripts/report_v2.py", "--out", str(u / "eval"), "--protocol", str(u / "experiments" / "protocol-v2.yaml"),
                            "--instances", str(u / "draw" / "instances.json"), "--h4", str(u / "draw" / "h4.json"), "--report", str(u / "report"),
                            "--params", str(u / "experiments" / "v2" / "params.json"), "--check"] + (["--smoke"] if a.smoke else []),
                           cwd=clone, capture_output=True, text=True)
        print(r.stdout, end=""); print(r.stderr, end="", file=sys.stderr)
        return r.returncode


if __name__ == "__main__":
    sys.exit(main())
