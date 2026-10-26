"""Artifact assembly, check, and reproduction (operations plan Task 10). A temporary repository with its own SSH test key
carries the signed tag protocol-v2; reproduction clones it at the tag and runs its report check. The repository's
report script is a small stand-in with the same command line, so the test exercises the unpack, clone, invoke, and
exit-code path; the real report's check is tested in tests/test_report_v2.py."""
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

STUB = '''import argparse, json, sys
from pathlib import Path
ap = argparse.ArgumentParser()
for k in ("--out", "--protocol", "--instances", "--h4", "--report", "--params"):
    ap.add_argument(k)
ap.add_argument("--check", action="store_true")
a = ap.parse_args()
got = {p.name: sum(json.loads(p.read_text())["gain"]) for p in sorted(Path(a.out, "evaluate").glob("*.json"))}
want = json.loads(Path(a.report, "report.json").read_text())
diff = [k for k in sorted(set(got) | set(want)) if got.get(k) != want.get(k)]
print("\\n".join(diff) or "ok")
sys.exit(1 if diff else 0)
'''


def _git(r, *args):
    return subprocess.run(["git", *args], cwd=r, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def world(tmp_path, monkeypatch):
    key = tmp_path / "key"
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "test", "-f", str(key)], check=True)
    allowed = tmp_path / "allowed"; allowed.write_text(f"test@example.com {(tmp_path / 'key.pub').read_text().strip()}\n")
    cfg = tmp_path / "gitconfig"
    cfg.write_text(f"[user]\n\tname = T\n\temail = test@example.com\n\tsigningkey = {key}\n[gpg]\n\tformat = ssh\n[gpg \"ssh\"]\n\tallowedSignersFile = {allowed}\n"
                   "[commit]\n\tgpgsign = false\n[tag]\n\tgpgsign = false\n[init]\n\tdefaultBranch = main\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(cfg)); monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    repo = tmp_path / "repo"
    for rel, text in {"scripts/report_v2.py": STUB, "experiments/v2/params.json": "{}", "experiments/protocol-v2.yaml": "version: 2\n",
                      "experiments/protocol-v2.yaml.ots": "proof", "paper/main.tex": "\\\\documentclass{article}", "uv.lock": "lock"}.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True); (repo / rel).write_text(text)
    _git(repo, "init", "-q"); _git(repo, "add", "-A"); _git(repo, "commit", "-qm", "protocol"); _git(repo, "tag", "-s", "protocol-v2", "-m", "protocol v2")
    ev = tmp_path / "eval"; (ev / "evaluate").mkdir(parents=True); (ev / "freeze").mkdir()
    from scripts.revision_v2 import path_of
    from sim.records_v2 import sha_file
    rec = ev / "evaluate" / "a.json"; rec.write_text(json.dumps({"gain": [0.1, 0.2]}))
    ref = path_of(ev, "reference/fresh0@rho0.2/F111"); ref.parent.mkdir(parents=True); ref.write_text("{}")
    (ev / "freeze" / "fresh0@rho0.2.json").write_text(json.dumps({"stage": "freeze", "records": {"reference/fresh0@rho0.2/F111": sha_file(ref)}}))
    draw = tmp_path / "draw"; draw.mkdir()
    for n in ("draw.json", "instances.json", "h4.json"):
        (draw / n).write_text("{}")
    rep = tmp_path / "report"; rep.mkdir(); (rep / "report.json").write_text(json.dumps({"a.json": 0.30000000000000004})); (rep / "report.md").write_text("# r")
    h4 = tmp_path / "sealed2"; (h4 / "h4").mkdir(parents=True); (h4 / "h4" / "family.py").write_text("x = 1")
    return {"repo": repo, "eval": ev, "draw": draw, "report": rep, "h4": h4, "out": tmp_path / "release"}


def _assemble(w):
    from scripts.artifact_v2 import assemble
    return assemble(w["eval"], w["draw"], w["report"], w["h4"], w["out"], repo=w["repo"])


def _rewrite(tar: Path, name: str, data: bytes | None):
    with tarfile.open(tar) as tf:
        members = [(m, tf.extractfile(m).read() if m.isfile() else None) for m in tf.getmembers()]
    with tarfile.open(tar, "w:gz") as tf:
        for m, b in members:
            if m.name.endswith(name):
                if data is None:
                    continue
                b = data; m.size = len(b)
            tf.addfile(m, io.BytesIO(b) if b is not None else None)


def test_assemble_and_check_a_synthetic_release(world):
    from scripts.artifact_v2 import check
    tar = _assemble(world)
    assert tar.name == "touchstone-v2.tar.gz" and check(tar, repo=world["repo"]) == []
    with tarfile.open(tar) as tf:
        names = tf.getnames()
    assert any(n.endswith("MANIFEST.json") for n in names) and any(n.endswith("paper/main.tex") for n in names) and any("h4/family.py" in n for n in names)


@pytest.mark.parametrize("case", ["changed file", "missing file", "freeze hash", "unsigned tag"])
def test_check_reports_missing_and_changed_files(world, case):
    from scripts.artifact_v2 import check
    tar = _assemble(world)
    if case == "changed file":
        _rewrite(tar, "evaluate/a.json", b'{"gain": [9.9]}')
    if case == "missing file":
        _rewrite(tar, "draw/instances.json", None)
    if case == "freeze hash":
        _rewrite(tar, "freeze/fresh0@rho0.2.json", json.dumps({"stage": "freeze", "records": {"reference/fresh0@rho0.2/F111": "0" * 64}}).encode())
    if case == "unsigned tag":
        _git(world["repo"], "tag", "-d", "protocol-v2"); _git(world["repo"], "tag", "protocol-v2")
    assert check(tar, repo=world["repo"])


# ---- final review K12: the archive is bound to the signed registration; reproduction runs the real report ----------------------

def test_k12_packed_registration_must_equal_the_tagged_files(world):
    from scripts.artifact_v2 import check
    tar = _assemble(world)
    _rewrite(tar, "experiments/v2/params.json", b'{"cred": "changed"}')
    with tarfile.open(tar) as tf:                                   # recompute the manifest so only the tag binding can catch it
        files = {m.name: tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}
    import hashlib
    man = {k.split("/", 1)[1]: hashlib.sha256(v).hexdigest() for k, v in files.items() if not k.endswith("MANIFEST.json")}
    _rewrite(tar, "MANIFEST.json", json.dumps(man).encode())
    assert any("tag" in p for p in check(tar, repo=world["repo"]))


@pytest.fixture(scope="module")
def real(tmp_path_factory):
    """A clone of this repository with a test-signed protocol-v2 tag, recorded draw inputs, and a report made by the real
    report_v2.py (no context has a freeze, so every question is unanswered; the reproduction path is what is tested)."""
    import hashlib
    import yaml
    import sim.instances as INST
    from sim.records import cfg_to_dict
    base = tmp_path_factory.mktemp("real"); root = Path(__file__).resolve().parents[1]
    with pytest.MonkeyPatch.context() as mp:
        key = base / "key"; subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "test", "-f", str(key)], check=True)
        allowed = base / "allowed"; allowed.write_text(f"test@example.com {(base / 'key.pub').read_text().strip()}\n")
        cfg = base / "gitconfig"
        cfg.write_text(f"[user]\n\tname = T\n\temail = test@example.com\n\tsigningkey = {key}\n[gpg]\n\tformat = ssh\n[gpg \"ssh\"]\n\tallowedSignersFile = {allowed}\n"
                       "[commit]\n\tgpgsign = false\n[tag]\n\tgpgsign = false\n[init]\n\tdefaultBranch = main\n")
        mp.setenv("GIT_CONFIG_GLOBAL", str(cfg)); mp.setenv("GIT_CONFIG_NOSYSTEM", "1")
        repo = base / "repo"; subprocess.run(["git", "clone", "-q", str(root), str(repo)], check=True)
        params = {"cred": {"variant": "thr", "K": 6, "M": None}, "tuned": {s: {"tol": 0.16, "L": 10} for s in ("B3-t", "R3-t", "R4-t", "C*-t")}}
        (repo / "experiments" / "v2").mkdir(parents=True, exist_ok=True); (repo / "experiments" / "v2" / "params.json").write_text(json.dumps(params))
        (repo / "experiments" / "protocol-v2.yaml").write_text(yaml.safe_dump({"version": 2, "kappa": {"Q1": None, "Q4": None}, "cuts": 0, "h4": None}))
        (repo / "experiments" / "protocol-v2.yaml.ots").write_bytes(b"proof")
        _git(repo, "add", "-A"); _git(repo, "commit", "-qm", "protocol"); _git(repo, "tag", "-s", "protocol-v2", "-m", "protocol v2")
        rh = "cd" * 32
        draw = base / "draw"; draw.mkdir(); (draw / "draw.json").write_text("{}")
        (draw / "instances.json").write_text(json.dumps({"root": rh, "confirmatory": True, "markets": {m["label"]: {"calibrated_cfg": cfg_to_dict(m["cfg"])} for m in INST.markets(rh, 6)},
                                                        "seeds": {}, "salt_sha256": hashlib.sha256(bytes.fromhex(INST.identity_salt_hex(rh))).hexdigest()}))
        (draw / "h4.json").write_text(json.dumps({"loaded": False, "reason": "no bundle is registered", "bundle_sha256": None, "h4_excluded": True, "registered_sha256": None}))
        ev = base / "eval"; ev.mkdir(); rep = base / "report"
        r = subprocess.run([sys.executable, "scripts/report_v2.py", "--out", str(ev), "--protocol", str(repo / "experiments" / "protocol-v2.yaml"), "--instances", str(draw / "instances.json"),
                            "--h4", str(draw / "h4.json"), "--report", str(rep), "--params", str(repo / "experiments" / "v2" / "params.json"), "--smoke"],
                           cwd=repo, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-2000:]
        from scripts.artifact_v2 import assemble
        tar = assemble(ev, draw, rep, None, base / "release", repo=repo)
        yield {"repo": repo, "tar": tar}


def test_k12_reproduce_passes_an_unchanged_release_with_the_real_report(real, capsys):
    from scripts.reproduce import main
    assert main(["--artifact", str(real["tar"]), "--repo", str(real["repo"]), "--smoke"]) == 0 and "ok" in capsys.readouterr().out


def test_k12_reproduce_detects_a_changed_report(real, tmp_path, capsys):
    import shutil
    from scripts.reproduce import main
    tar = tmp_path / "t.tar.gz"; shutil.copy(real["tar"], tar)
    with tarfile.open(tar) as tf:
        md = next(tf.extractfile(m).read() for m in tf.getmembers() if m.name.endswith("report/report.md"))
    _rewrite(tar, "report/report.md", md.replace(b"unanswered", b"answered", 1))
    assert main(["--artifact", str(tar), "--repo", str(real["repo"]), "--smoke"]) != 0


def test_k12_reproduce_refuses_an_unsigned_tag(real, tmp_path):
    import shutil
    from scripts.reproduce import main
    repo = tmp_path / "unsigned"; shutil.copytree(real["repo"], repo)
    _git(repo, "tag", "-d", "protocol-v2"); _git(repo, "tag", "protocol-v2")
    assert main(["--artifact", str(real["tar"]), "--repo", str(repo), "--smoke"]) != 0


def test_k12_environment_must_match_the_lock(real, monkeypatch):
    import scripts.reproduce as RP
    assert RP.environment_problems(real["repo"] / "uv.lock") == []
    monkeypatch.setattr(RP, "_installed", lambda name: "0.0.0" if name == "numpy" else RP._real_installed(name))
    assert any("numpy" in p for p in RP.environment_problems(real["repo"] / "uv.lock"))
