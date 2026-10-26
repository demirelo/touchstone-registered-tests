"""The protocol-v2 writer and checker (operations plan Task 6): hashes re-derived from their files, the frozen cost
decision, kappa from admission, and the commit and signed-tag checks in a temporary repository with its own test key."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
H4 = {"commit": "a" * 40, "bundle_sha256": "b" * 64}


def _repo(tmp_path, total=30.0, kappa_q1=0.5, kappa_q4=None) -> Path:
    r = tmp_path / "repo"; (r / "experiments" / "v2" / "benchmark").mkdir(parents=True); (r / "docs" / "revision").mkdir(parents=True)
    shutil.copy(ROOT / "experiments" / "revision-v2-manifest.yaml", r / "experiments" / "revision-v2-manifest.yaml")
    v2 = r / "experiments" / "v2"
    cred = {"variant": "thr", "K": 6, "M": None}; (v2 / "comparator.json").write_text(json.dumps({"cred": cred}))
    tuned = {s: {"tol": 0.16, "L": 10} for s in ("B3-t", "R3-t", "R4-t", "C*-t")}
    for s, bp in tuned.items():
        (v2 / f"tuned_{s}.json").write_text(json.dumps({"rule": s, "best_params": bp}))
    (v2 / "params.json").write_text(json.dumps({"cred": cred, "tuned": tuned}))
    (v2 / "coverage.json").write_text(json.dumps({"Q1": {"kappa": 0.5, "kappa_effective": kappa_q1}, "Q4": {"kappa": 0.25, "kappa_effective": kappa_q4}}))
    dec = {"branch": "two20k", "markets": ["headline", "dev0"], "cuts": 1, "development_usd": 9.0, "evaluation_usd": total - 9.0, "total_usd": total,
           "approval_required": total > 40, "spent_usd": 1.0, "stop": None}
    (v2 / "benchmark" / "decision.json").write_text(json.dumps({"decision": dec, "ledger": {"spent": [{"op": "development", "tag": "bench", "usd": 1.0}]}, "timings_sha256": "d" * 64}))
    entries = {p.relative_to(v2).as_posix(): _sha(p) for p in v2.rglob("*.json") if p.name not in ("params.json", "promotion.json")}
    (v2 / "promotion.json").write_text(json.dumps({"entries": entries, "kinds": {}}))
    (r / "docs" / "revision" / "predictions-v2.md").write_text("# Predictions\n")
    (r / "docs" / "revision" / "budget-ledger.json").write_text(json.dumps({"caps": {}, "reservations": [], "spent": [{"op": "development", "tag": "bench", "usd": 1.0},
                                                                                                                       {"op": "development", "tag": "tune", "usd": 4.5}]}))
    return r


def _sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _build(r, **kw):
    from scripts.lock_v2 import build
    args = dict(code_commit="e" * 40, cuts=1, h4=H4, approval=None, branch="two20k", markets=["headline", "dev0"]); args.update(kw)
    return build(r, **args)


def test_build_and_check_round_trip(tmp_path):
    from scripts.lock_v2 import check
    r = _repo(tmp_path); p = _build(r)
    assert check(r, p) == []
    expected = {"manifest_sha256": _sha(r / "experiments/revision-v2-manifest.yaml"), "params_sha256": _sha(r / "experiments/v2/params.json"),
                "promotion_sha256": _sha(r / "experiments/v2/promotion.json"), "decision_sha256": _sha(r / "experiments/v2/benchmark/decision.json"),
                "coverage_sha256": _sha(r / "experiments/v2/coverage.json"), "predictions_sha256": _sha(r / "docs/revision/predictions-v2.md")}
    assert {k: p[k] for k in expected} == expected
    assert p["version"] == 2 and p["h4"] == H4 and p["cuts"] == 1 and p["branch"] == "two20k" and p["development_markets"] == ["headline", "dev0"]
    assert p["block"] == {"rule": "H = A + 144", "depth": 6, "explorers": ["blockstream.info", "mempool.space"]}
    assert p["seeds"] == {"eval_range": [30_000_000, 40_000_000], "per_market": 200} and p["markets"] == ["headline"] + [f"fresh{i}" for i in range(6)]
    assert p["caps"] == {"development": 12, "evaluation": 40} and p["cost"]["spent_usd"] == pytest.approx(5.5)


@pytest.mark.parametrize("rel", ["experiments/v2/params.json", "experiments/v2/coverage.json", "experiments/revision-v2-manifest.yaml",
                                 "docs/revision/predictions-v2.md", "experiments/v2/promotion.json", "experiments/v2/benchmark/decision.json"])
def test_check_reports_each_changed_input(tmp_path, rel):
    from scripts.lock_v2 import check
    r = _repo(tmp_path); p = _build(r)
    with open(r / rel, "a") as f:
        f.write("\n")
    problems = check(r, p)
    assert problems and any(Path(rel).name.split(".")[0].split("-")[0] in x for x in problems)


def test_total_above_40_needs_approval(tmp_path):
    from scripts.lock_v2 import check
    r = _repo(tmp_path, total=44.0)
    with pytest.raises(SystemExit):
        _build(r)
    p = _build(r, approval="Approved up to 45 USD. (author, 2026-10-30)")
    assert check(r, p) == [] and p["approval"].startswith("Approved")
    assert any("approval" in x for x in check(r, dict(p, approval=None)))


def test_kappa_comes_from_kappa_effective(tmp_path):
    r = _repo(tmp_path, kappa_q1=None, kappa_q4=0.25)
    assert _build(r)["kappa"] == {"Q1": None, "Q4": 0.25}


def test_decision_and_choices_must_agree(tmp_path):
    from scripts.lock_v2 import check
    r = _repo(tmp_path)
    with pytest.raises(SystemExit):
        _build(r, cuts=0)
    with pytest.raises(SystemExit):
        _build(r, branch="three20k", markets=["headline", "dev0", "dev1"])


def test_decision_survives_later_spend(tmp_path):
    from scripts.lock_v2 import check
    r = _repo(tmp_path)
    led = r / "docs/revision/budget-ledger.json"; d = json.loads(led.read_text())
    d["spent"].append({"op": "development", "tag": "coverage", "usd": 3.0}); led.write_text(json.dumps(d))     # spend after the decision
    p = _build(r)
    assert check(r, p) == [] and p["cost"]["spent_usd"] == pytest.approx(8.5) and p["cuts"] == 1
    dec = r / "experiments/v2/benchmark/decision.json"; dd = json.loads(dec.read_text()); dd["decision"]["cuts"] = 0; dec.write_text(json.dumps(dd))
    assert any("decision" in x for x in check(r, p))


# ---- commit and tag checks in a temporary repository with its own signing key -----------------------------------------------

def _git(r, *args, env):
    return subprocess.run(["git", *args], cwd=r, env=env, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def signed(tmp_path, monkeypatch):
    key = tmp_path / "key"
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "test", "-f", str(key)], check=True)
    allowed = tmp_path / "allowed"; allowed.write_text(f"test@example.com {(tmp_path / 'key.pub').read_text().strip()}\n")
    cfg = tmp_path / "gitconfig"
    cfg.write_text(f"[user]\n\tname = T\n\temail = test@example.com\n\tsigningkey = {key}\n[gpg]\n\tformat = ssh\n[gpg \"ssh\"]\n\tallowedSignersFile = {allowed}\n"
                   "[commit]\n\tgpgsign = false\n[tag]\n\tgpgsign = false\n[init]\n\tdefaultBranch = main\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(cfg)); monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    env = dict(os.environ)
    r = tmp_path / "g"; (r / "sim").mkdir(parents=True); (r / "sim" / "a.py").write_text("x = 1\n")
    _git(r, "init", "-q", env=env); _git(r, "add", "-A", env=env); _git(r, "commit", "-qm", "code", env=env)
    code = _git(r, "rev-parse", "HEAD", env=env)
    (r / "experiments" / "v2").mkdir(parents=True); (r / "experiments" / "v2" / "x.json").write_text("{}")
    (r / "experiments" / "protocol-v2.yaml").write_text(yaml.safe_dump({"version": 2, "code_commit": code}))
    _git(r, "add", "-A", env=env); _git(r, "commit", "-qm", "protocol", env=env)
    return r, code, env


def _ok(monkeypatch):
    import scripts.lock_v2 as L
    monkeypatch.setattr(L, "check", lambda repo, protocol: [])


def test_check_commit_passes_a_signed_tag_on_a_data_only_commit(signed, monkeypatch):
    from scripts.lock_v2 import check_commit
    r, code, env = signed; _ok(monkeypatch)
    _git(r, "tag", "-s", "protocol-v2", "-m", "protocol v2", env=env)
    check_commit(r)


@pytest.mark.parametrize("case", ["untagged head", "lightweight tag", "code change", "dirty tree"])
def test_check_commit_refuses_other_head_or_unsigned_tag(signed, monkeypatch, case):
    from scripts.lock_v2 import check_commit
    r, code, env = signed; _ok(monkeypatch)
    if case == "lightweight tag":
        _git(r, "tag", "protocol-v2", env=env)
    else:
        _git(r, "tag", "-s", "protocol-v2", "-m", "protocol v2", env=env)
    if case == "untagged head":
        (r / "docs").mkdir(); (r / "docs" / "n.md").write_text("n"); _git(r, "add", "-A", env=env); _git(r, "commit", "-qm", "later", env=env)
    if case == "code change":
        (r / "sim" / "a.py").write_text("x = 2\n"); _git(r, "add", "-A", env=env); _git(r, "commit", "-qm", "code edit", env=env)
        _git(r, "tag", "-d", "protocol-v2", env=env); _git(r, "tag", "-s", "protocol-v2", "-m", "protocol v2", env=env)
    if case == "dirty tree":
        (r / "experiments" / "v2" / "x.json").write_text('{"dirty": 1}')
    with pytest.raises(SystemExit):
        check_commit(r)



# ---- final review K3: a failed git comparison never passes ------------------------------------------------------------------

@pytest.mark.parametrize("case", ["missing commit object", "not an ancestor"])
def test_k3_unresolvable_or_foreign_code_commit_is_refused(signed, monkeypatch, case):
    import yaml
    from scripts.lock_v2 import check_commit
    r, code, env = signed; _ok(monkeypatch)
    if case == "missing commit object":
        bogus = "1" * 40
    else:
        _git(r, "checkout", "-q", "--orphan", "other", env=env); (r / "o.txt").write_text("o"); _git(r, "add", "-A", env=env)
        _git(r, "commit", "-qm", "unrelated", env=env); bogus = _git(r, "rev-parse", "HEAD", env=env); _git(r, "checkout", "-q", "main", env=env)
    p = r / "experiments" / "protocol-v2.yaml"; p.write_text(yaml.safe_dump({"version": 2, "code_commit": bogus}))
    _git(r, "add", "-A", env=env); _git(r, "commit", "-qm", "protocol points elsewhere", env=env)
    _git(r, "tag", "-s", "protocol-v2", "-m", "protocol v2", env=env)
    with pytest.raises(SystemExit):
        check_commit(r)



# ---- final review K5: the lock checks every promoted file and the parameters derived from them ----------------------------

@pytest.mark.parametrize("rel,edit", [("experiments/v2/tuned_R3-t.json", lambda d: d.update(best_params={"tol": 0.08, "L": 3})),
                                      ("experiments/v2/comparator.json", lambda d: d.update(cred={"variant": "mem", "K": 6, "M": 50}))])
def test_k5_lock_detects_promoted_files_changed_after_promotion(tmp_path, rel, edit):
    from scripts.lock_v2 import check
    r = _repo(tmp_path); p = _build(r)
    f = r / rel; d = json.loads(f.read_text()); edit(d); f.write_text(json.dumps(d))
    assert any("promot" in x for x in check(r, p))


def test_k5_params_must_follow_from_the_promoted_files(tmp_path):
    from scripts.lock_v2 import check
    r = _repo(tmp_path)
    f = r / "experiments/v2/params.json"; d = json.loads(f.read_text()); d["tuned"]["B3-t"]["L"] = 50; f.write_text(json.dumps(d))
    with pytest.raises(SystemExit):
        _build(r)


@pytest.mark.parametrize("fail", [("status",), ("rev-parse", "HEAD"), ("rev-parse", "protocol-v2^{commit}")])
def test_l5_every_git_command_must_succeed(signed, monkeypatch, fail):
    import scripts.lock_v2 as L
    r, code, env = signed; _ok(monkeypatch); _git(r, "tag", "-s", "protocol-v2", "-m", "protocol v2", env=env)
    real = L._git

    def broken(repo, *args):
        out = real(repo, *args)
        if tuple(args[:len(fail)]) == fail:                       # only this command fails, and its output still looks valid
            return type(out)(out.args, 128, out.stdout, "fatal: broken")
        return out
    monkeypatch.setattr(L, "_git", broken)
    with pytest.raises(SystemExit):
        L.check_commit(r)
