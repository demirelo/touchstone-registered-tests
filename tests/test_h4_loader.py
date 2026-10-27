"""The sealed-family loader (design 5.3): hash check, import, interface check, constant binding, exclusion."""
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tests._v2_profiles import CFG, fingerprint, run_full

GOOD = '''
from sim.policies.v2 import x5v2_family
from dataclasses import replace
BINARY = ("x", "clip")
def make_family(T, L):
    return replace(x5v2_family(T, L), name="H4")
'''


def bundle(tmp: Path, src: str = GOOD) -> tuple[Path, str]:
    d = tmp / "sealed2"; (d / "h4").mkdir(parents=True)
    (d / "h4/family.py").write_text(src); (d / "h4/containment.md").write_text("non-nested"); (d / "h4/check.json").write_text(json.dumps({"ok": True}))
    from sim.h4_loader import bundle_sha
    return d, bundle_sha(d)


def test_bundle_sha_definition(tmp_path):
    d, sha = bundle(tmp_path)
    h = hashlib.sha256()
    for rel in ("h4/family.py", "h4/containment.md", "h4/check.json"):
        h.update(rel.encode()); h.update(b"\0"); h.update(hashlib.sha256((d / rel).read_bytes()).hexdigest().encode()); h.update(b"\n")
    assert sha == h.hexdigest()


def test_h4_loads_valid_bundle(tmp_path):
    from sim.h4_loader import H4Source, load
    d, sha = bundle(tmp_path)
    src = load(d, sha)
    assert isinstance(src, H4Source) and src.family(200, 10).name == "H4"


def test_h4_hash_mismatch_excluded(tmp_path):
    from sim.h4_loader import Excluded, load
    d, sha = bundle(tmp_path)
    out = load(d, "0" * 64)
    assert isinstance(out, Excluded) and "hash" in out.reason


def test_h4_import_error_excluded(tmp_path):
    from sim.h4_loader import Excluded, load
    d, sha = bundle(tmp_path, "import nonexistent_module_xyz\n")
    assert isinstance(load(d, sha), Excluded)


@pytest.mark.parametrize("src", [
    GOOD.replace('name="H4"', 'name="H5"'),
    "from sim.policies.families import Family\nBINARY=('clip',)\ndef make_family(T, L):\n    return Family('H4', ('clip', 'u'), {'u': (0.0, 1.0)}, None)\n",
    "from sim.policies.families import Family\nBINARY=('clip',)\ndef make_family(T, L):\n    return Family('H4', ('u', 'v', 'clip'), {'u': (0.0, 1.0)}, None)\n",
    "BINARY=('clip',)\n"])
def test_h4_interface_violation_excluded(tmp_path, src):
    from sim.h4_loader import Excluded, load
    d, sha = bundle(tmp_path, src)
    assert isinstance(load(d, sha), Excluded)


def test_h4_binds_constants_and_resumes(tmp_path):
    from sim.h4_loader import load
    d, sha = bundle(tmp_path)
    src = load(d, sha)
    made = []
    fam = src.family(100, 20)
    k = {"u": 0.6, "m": 0.5, "s": 0.0, "w": 0.0, "n_age": 3.0, "x": 1, "clip": 0}
    cfg = replace(CFG, T=100)
    from sim.policies.honest import HonestMax
    f = lambda: made.append(fam.make(k)) or made[-1]
    a = run_full(cfg, __import__("sim.rules_v2", fromlist=["x"]).make_rule("F111", L=20), [f] + [HonestMax] * 9, 2000)
    assert made[0].state.T == 100 and made[0].state.W == 20
    fam2 = load(d, sha).family(100, 20)                       # reconstruction from the stored constants
    b = run_full(cfg, __import__("sim.rules_v2", fromlist=["x"]).make_rule("F111", L=20), [lambda: fam2.make(k)] + [HonestMax] * 9, 2000)
    assert fingerprint(a) == fingerprint(b)


@pytest.mark.parametrize("src,needle", [
    ("from sim.policies.families import Family\nBINARY = ('clip',)\n"
     "def make_family(T, L):\n    ks = tuple(f'k{i}' for i in range(16)) + ('clip',)\n"
     "    return Family('H4', ks, {k: (0.0, 1.0) for k in ks[:-1]}, lambda **k: None)\n", "15 knobs"),
    ("from sim.policies.families import Family\nBINARY = ('clip',)\nclass F(Family):\n    project = None\n"
     "def make_family(T, L):\n    return F('H4', ('a', 'clip'), {'a': (0.0, 1.0)}, lambda **k: None)\n", "project"),
    ("from sim.policies.families import Family\nBINARY = ('clip',)\n"
     "def make_family(T, L):\n    return Family('H4', ('a', 'clip'), {'a': (0.0, float('inf'))}, lambda **k: None)\n", "finite"),
])
def test_h4_outside_envelope_is_excluded(tmp_path, src, needle):
    from sim.h4_loader import Excluded, load
    d, sha = bundle(tmp_path, src)
    r = load(d, sha)
    assert isinstance(r, Excluded) and needle in r.reason


def test_h4_controls_are_bounded():
    import scripts.revision_v2 as RV
    from sim.policies.families import Family
    ks = tuple(f"k{i}" for i in range(14)) + ("clip",)
    fam = Family("H4", ks, {k: (0.0, 1.0) for k in ks[:-1]}, lambda **k: None)
    fam_corners = type(fam).corners
    try:
        type(fam).corners = lambda self: (_ for _ in ()).throw(AssertionError("Family.corners must not be called for H4"))

        class Stub:
            def eval_knobs(self, k, source="corner"):
                return 0.0
        vecs = RV.controls(Stub(), fam)
    finally:
        type(fam).corners = fam_corners
    assert 0 < len(vecs) <= 2 * 514


def test_h4_budget_is_x7():
    import scripts.revision_v2 as RV
    mkt = RV.market("dev0", RV.DEV_ROOT, 0.2, dev=True)
    assert RV.job(mkt, "F111", "H4")["budget"][1] == RV.job(mkt, "F111", "X7-SC")["budget"][1] == 2 * RV.job(mkt, "F111", "D2+H3")["budget"][1]
