"""The development comparator table (internal review r2/r3 of the Fable 5.2 revision): every configuration's stored
inner-budget gains and efficiencies, and the two full-budget rechecks, from experiments/v2/log/Cstar__*.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comparator_table as C  # noqa: E402


def _log(d, variant, K, M, kind, g_hl, g_d0, e_hl=0.999, e_d0=0.995):
    spec = {"L": 10, "cred": {"K": K, "M": M, "variant": variant}, "tol": 0.16}
    det = {m: {f: {"gain": g, "eff": e} for f in ("D2+H3", "X7-SC")} for m, g, e in (("headline", g_hl, e_hl), ("dev0", g_d0, e_d0))}
    (d / f"Cstar__{json.dumps(spec, sort_keys=True, separators=(',', ':'))}__{kind}.json").write_text(json.dumps({"spec": spec, "detail": det}))


def test_rows_list_inner_and_recheck_runs_with_gains(tmp_path):
    _log(tmp_path, "mem", 6, 20, "inner", 0.0, -0.1767); _log(tmp_path, "mem", 6, 20, "recheck", 0.0966, 0.0381)
    _log(tmp_path, "thr", 12, None, "recheck", 0.0761, 0.0178); _log(tmp_path, "boinc", 10, None, "inner", 0.0, 0.0)
    rows = C.rows(tmp_path)
    assert [(r["config"], r["budget"]) for r in rows] == [("C-boinc", "inner"), ("C-mem(6, 20)", "inner"), ("C-mem(6, 20)", "full"), ("C-thr(12)", "full")]
    assert rows[2]["gain"]["headline"]["D2+H3"] == 0.0966
    t = C.table(rows)
    assert "C-mem(6, 20) & full & 0.097 & 0.038" in t and "C-thr(12) & full & 0.076 & 0.018" in t and "\\ensuremath{-0.177}" in t
