"""The H4 session kit (operations plan Task 1): load check, smoke evaluation on development seeds, check.json inside the hash."""
import json
import shutil
from pathlib import Path

import pytest

TOY = Path(__file__).resolve().parent / "fixtures" / "h4_toy"


def _copy(tmp_path) -> Path:
    d = tmp_path / "sealed2"; shutil.copytree(TOY, d)
    return d


def test_toy_bundle_passes_load_and_hash_round_trip(tmp_path, capsys):
    from scripts.h4_check import main
    from sim.h4_loader import H4Source, bundle_sha, load
    d = _copy(tmp_path)
    assert main(["--bundle", str(d), "--smoke"]) == 0
    printed = capsys.readouterr().out.strip().splitlines()[-1]
    chk = json.loads((d / "h4" / "check.json").read_text())
    assert chk["load"]["ok"] is True and chk["load"]["constants"] == [[200, 10], [100, 20]]
    assert set(chk) >= {"load", "smoke", "scipy", "commit"} and printed == bundle_sha(d)
    assert isinstance(load(d, printed), H4Source)


@pytest.mark.parametrize("src,needle", [
    ("from dataclasses import replace\nfrom sim.policies.families import FAMILIES\nfrom sim.policies.identity import h3_family\n"
     "def make_family(T, L):\n    return replace(h3_family(FAMILIES['D2']), name='H4')\n", "BINARY"),
    ("from dataclasses import replace\nfrom sim.policies.families import FAMILIES\nfrom sim.policies.identity import h3_family\nBINARY = ('x', 'clip')\n"
     "def make_family(T, L):\n    return replace(h3_family(FAMILIES['D2']), name='X')\n", "H4"),
])
def test_missing_binary_or_wrong_name_fails_load_check(tmp_path, src, needle):
    from scripts.h4_check import load_check
    d = _copy(tmp_path); (d / "h4" / "family.py").write_text(src)
    r = load_check(d)
    assert r["ok"] is False and needle in r["problem"]


def test_smoke_touches_development_seeds_only(tmp_path, monkeypatch):
    import sim.instances as INST
    from scripts.h4_check import smoke
    monkeypatch.setattr(INST, "eval_seeds", lambda *a, **k: (_ for _ in ()).throw(AssertionError("reserved evaluation seeds")))
    r = smoke(_copy(tmp_path))
    assert set(r) == {f"{rule}|{m}" for rule in ("F000", "F111") for m in ("dev0", "dev1")}
    dev = set(range(1000, 1005)) | set(range(2000, 2020))
    for v in r.values():
        assert set(v["train_seeds"]) | set(v["eval_seeds"]) <= dev and "gain" in v and v["train_seeds"] and v["eval_seeds"]


def test_check_json_is_inside_the_hash(tmp_path):
    from scripts.h4_check import main
    from sim.h4_loader import bundle_sha
    d = _copy(tmp_path); main(["--bundle", str(d), "--smoke"])
    before = bundle_sha(d); p = d / "h4" / "check.json"; p.write_text(p.read_text() + " ")
    assert bundle_sha(d) != before
