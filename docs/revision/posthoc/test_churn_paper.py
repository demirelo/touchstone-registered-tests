import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import churn_paper as P  # noqa: E402

HERE = Path(__file__).parent
FIRST = json.loads((HERE / "churn.json").read_text())
MID = json.loads((HERE / "churn_mid.json").read_text())


def test_curves_cover_five_rates_and_match_the_records():
    d = P.data(FIRST, MID)
    assert d["rates"] == [0.0, 0.01, 0.02, 0.03, 0.05]
    d05 = [p for p in d["curves"]["base"]["d"] if p["p"] == 0.05][0]
    assert d05["estimate"] == FIRST["statistics"]["base"]["0.05"]["d"]["pooled"]["estimate"]
    q03 = [p for p in d["curves"]["doubled"]["q"] if p["p"] == 0.03][0]
    assert q03["estimate"] == MID["statistics"]["doubled"]["0.03"]["q"]["pooled"]["estimate"]


def test_allocation_rows_come_from_review_r4():
    d = P.data(FIRST, MID)
    assert len(d["allocation"]) == 12
    r = [x for x in d["allocation"] if x["p"] == 0.02 and x["rule"] == "R3"][0]
    a = MID["review_r4"]["audit_allocation"]["0.02"]["F111|base"]
    assert r["focal_audit_rate"] == a["focal_audit_rate"] and r["x_off"] == sum(v == 0 for v in a["x_by_market"].values())
    assert r["eff_attack"] == MID["review_r4"]["eff_attack"]["base"]["0.02"]["F111"]


def test_check_refuses_stale_outputs(tmp_path):
    d = P.data(FIRST, MID)
    assert len(P.check(d, tmp_path, tmp_path)) == 2
    P.write(d, tmp_path, tmp_path)
    assert P.check(d, tmp_path, tmp_path) == []
    (tmp_path / "posthoc_churn_audit.tex").write_text("x")
    assert any("audit" in b for b in P.check(d, tmp_path, tmp_path))
