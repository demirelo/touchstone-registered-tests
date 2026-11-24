"""Tests for replication_paper.py: the paper summary and tables built from the committed analysis and extract."""
import json
from pathlib import Path

import pytest

import replication_paper as RP

HERE = Path(__file__).resolve().parent
SHA = "a" * 64
XOFF = {"d": 0.0, "q": 0.3, "u": 0.6}            # distinct values per contrast, so that a column swap is visible


CONT = [("menu", "0", "rep2", "F111"), ("menu", "0.03", "rep4", "F111"), ("menu", "0.05", "rep1", "Cstar"), ("cthr", "0.05", "rep3", "Cstar")]
RULE = {("menu", "F111"): "R3", ("menu", "Cstar"): "C*", ("cthr", "Cstar"): "C-thr"}


def _stem(k, p, m, pol):
    return f"{k}-p{p}__fresh{m[3]}@rho0.2__{pol}__D2+H3__profit" + ("" if p == "0" else f"__churn{p}")


def _analysis():
    mk = lambda v: {f"rep{i}": v + 0.01 * i for i in range(6)}
    pc = lambda mean: {"complete": True, "lower": 5, "markets": mk(mean), "mean": mean, "t95": [mean - 0.1, mean + 0.1]}
    ab = lambda mean: {"complete": True, "markets": {f"rep{i}": {"estimate": mean, "ci95": [mean - 0.002, mean + 0.002]} for i in range(6)},
                       "mean": mean, "pooled_ci95": [mean - 0.01, mean + 0.01], "t95": [mean - 0.2, mean + 0.2]}
    bs = lambda mean: {"markets": {f"rep{i}": {"ci95": [mean - 0.003, mean + 0.003]} for i in range(6)}, "pooled": {"ci95": [mean - 0.004, mean + 0.004]}}
    terms = {p: {f"rep{i}": {r: {"attack": 0.3, "eff_attack": e, "gain": 0.1, "reference": 0.2}
                             for r, e in (("R3", 0.95 - float(p)), ("C*", 0.99), ("C-thr", 0.98), ("B3", 0.97))}
                 for i in range(6)} for p in ("0", "0.03", "0.05")}
    s = {"paired_changes": {p: {x: pc((-0.1 if p == "0.05" else -0.05) - XOFF[x]) for x in "dqu"} for p in ("0.03", "0.05")},
         "bootstrap": {p: {x: bs(-0.1 - XOFF[x]) for x in "dqu"} for p in ("0.03", "0.05")},
         "absolute": {p: {x: ab(0.02 - float(p) * 4 - XOFF[x]) for x in "dqu"} for p in ("0", "0.03", "0.05")},
         "criteria": {p: {x: {"material": True, "support": True} for x in "dqu"} for p in ("0.03", "0.05")},
         "expectations": {str(k): {"text": "t", "verdict": "met"} for k in range(1, 6)}, "terms": terms}
    an = {"primary": s, "frozen": json.loads(json.dumps(s)), "counts": {"continued": 4, "frozen": 68, "unresolved": 0},
          "gate_ok": True, "problems": [], "unscorable": [], "round1_mismatch": False, "confirmatory": True}
    for k, p, m, pol in CONT:                             # a continued cell's primary terms differ from its frozen terms
        an["primary"]["terms"][p][m][RULE[(k, pol)]]["gain"] = 0.05
    return an


def _al(c, x=1):
    return {"young_honest_job_share": 0.1, "young_honest_audit_share": 0.3, "established_honest_audit_rate": 0.2,
            "focal_job_share": 0.08, "focal_audit_rate": c[0] / c[1] if c[1] else None, "x": x}


def _extract():
    fr = {"0": {f"rep{i}": [80, 100] for i in range(6)}, "0.05": {f"rep{i}": [2 + i, 100] for i in range(6)},
          "0.03": {f"rep{i}": [5, 100] for i in range(6)}}
    pr = json.loads(json.dumps(fr)); del pr["0.03"]["rep4"]      # continued R3 cell at 0.03: no continued diagnostics
    al = lambda au: {p: {m: _al(c, x=int(m != "rep0")) for m, c in ms.items()} for p, ms in au.items()}
    sha = {k: RP.sha_file(v) for k, v in RP.COMMITTED.items()}
    return {"audit": {"primary": pr, "frozen": fr}, "alloc": {"primary": al(pr), "frozen": al(fr)},
            "counts": {"continued": 4, "frozen": 68, "unresolved": 0},
            "status": {"problems": [], "unscorable": [], "round1_mismatch": False, "gate_ok": True},
            "binding": dict(sha, analysis=SHA, recomputed=True),
            "continued": [{"kind": k, "rate": p, "market": m, "policy": pol, "stem": _stem(k, p, m, pol)} for k, p, m, pol in CONT]}


def _sum(an=None, ex=None, sha=SHA):
    return RP.summary(an or _analysis(), ex or _extract(), sha)


def test_audit_shares_min_max_and_count_below():
    a = _sum()["primary"]["audit"]
    assert a["0"]["focal_audit_min"] == pytest.approx(0.8) and a["0"]["focal_audit_max"] == pytest.approx(0.8)
    assert a["0.05"]["focal_audit_min"] == pytest.approx(0.02) and a["0.05"]["focal_audit_max"] == pytest.approx(0.07)
    assert a["0.05"]["markets"] == 6 and a["below"]["markets"] == 6
    assert a["0.03"]["markets"] == 5                      # missing counts are not imputed


def test_zero_denominator_counts_as_not_below():
    ex = _extract(); ex["audit"]["primary"]["0.05"]["rep0"] = [0, 0]; ex["alloc"]["primary"]["0.05"]["rep0"]["focal_audit_rate"] = None
    assert _sum(ex=ex)["primary"]["audit"]["below"]["markets"] == 5


def test_allocation_means_and_market_count():
    a = _sum()["primary"]["alloc"]
    assert a["0.05"]["young_honest_job_share"] == pytest.approx(0.1) and a["0.05"]["markets"] == 6
    assert a["0.03"]["markets"] == 5 and a["0.05"]["replacing_markets"] == 5
    assert a["0.05"]["focal_audit_rate"] == pytest.approx(sum(2 + i for i in range(6)) / 600)


def test_efficiency_means_per_rule():
    e = _sum()["primary"]["eff"]
    assert e["0.05"]["R3"]["eff"] == pytest.approx(0.90) and e["0"]["C*"]["eff"] == pytest.approx(0.99)
    assert e["0.05"]["R3"]["eff_min"] == pytest.approx(0.90)


def test_spread_two_most_negative_and_rest():
    sp = _sum()["primary"]["spread"]["0.05"]["q"]
    assert sp["top"] == {"0": pytest.approx(-0.4), "1": pytest.approx(-0.39)} and sp["top_markets"] == ["rep0", "rep1"]
    assert sp["rest"] == {"min": pytest.approx(-0.38), "max": pytest.approx(-0.35)}


def test_setdiff_and_criteria_counts():
    an = _analysis(); an["frozen"]["absolute"]["0.05"]["d"]["mean"] -= 0.04; an["frozen"]["criteria"]["0.03"]["d"]["support"] = False
    s = _sum(an=an)
    assert s["setdiff"]["0.05"]["d"]["difference"] == pytest.approx(0.04) and s["setdiff"]["0"]["q"]["difference"] == 0
    assert s["frozen"]["criteria"] == {"support": {"cells": 5}, "material": {"cells": 6}}


def test_continued_split_by_rate_and_rule():
    c = _sum()["continued"]
    assert c["all"]["cells"] == 4 and c["0"]["cells"] == 1 and c["0.05"]["cells"] == 2 and c["0.03"]["cells"] == 1
    assert c["rules"]["R3"]["cells"] == 2 and c["rules"]["C-thr"]["cells"] == 1 and c["rules"]["C*"]["cells"] == 1


@pytest.mark.parametrize("mutate", [
    lambda an, ex: ex.update(counts={"continued": 5, "frozen": 67, "unresolved": 0}),
    lambda an, ex: an.update(problems=["x"]),
    lambda an, ex: an.update(confirmatory=False),
    lambda an, ex: ex.update(binding={"analysis": "b" * 64}),                        # stale extract, equal counts
    lambda an, ex: ex["status"].update(problems=["y"]),
    lambda an, ex: ex["continued"].append(dict(ex["continued"][0])),                 # duplicate identity
    lambda an, ex: ex["continued"][2].update(rate="0.03"),                           # fields disagree with the stem
    lambda an, ex: ex["audit"]["primary"].update({"0.02": {"rep0": [1, 2]}}),        # unplanned rate
    lambda an, ex: ex["alloc"]["primary"]["0.05"].pop("rep5"),                       # allocation misses a cell
    lambda an, ex: an["primary"]["expectations"]["5"].update(verdict="not met"),     # audit counts say met
    lambda an, ex: ex["binding"].update(draw="c" * 64),                              # not the committed draw
    lambda an, ex: ex["binding"].update(manifest="c" * 64),                          # not the committed manifest
    lambda an, ex: ex["binding"].pop("recomputed"),                                  # analysis not recomputed
    lambda an, ex: ex["continued"][2].update(market="rep2", stem=_stem("menu", "0.05", "rep2", "Cstar")),  # swapped cell
    lambda an, ex: ex["audit"]["primary"]["0.05"].update(rep2=[120, 100]),           # audited above served
    lambda an, ex: ex["audit"]["primary"]["0.05"].update(rep2=[-1, 100]),            # negative count
    lambda an, ex: ex["alloc"]["primary"]["0.05"]["rep2"].update(young_honest_job_share=1.2),   # share above one
    lambda an, ex: ex["alloc"]["primary"]["0.05"]["rep2"].update(focal_audit_rate=0.5),         # rate disagrees with counts
    lambda an, ex: ex["alloc"]["primary"]["0.05"]["rep2"].update(x=2),                          # impossible switch
    lambda an, ex: [ex[k]["frozen"]["0.03"].pop("rep1") for k in ("audit", "alloc")],           # frozen coverage gap
    lambda an, ex: [ex[k]["primary"]["0.05"].pop("rep5") for k in ("audit", "alloc")],          # primary gap not allowed
    lambda an, ex: ex["continued"].append({"kind": "cthr", "rate": "0", "market": "rep1", "policy": "F111",
                                           "stem": "cthr-p0__fresh1@rho0.2__F111__D2+H3__profit"}),   # impossible identity
])
def test_refusals(mutate):
    an, ex = _analysis(), _extract()
    mutate(an, ex)
    with pytest.raises(ValueError):
        RP.summary(an, ex, SHA)


def test_table_columns_follow_the_contrasts():
    t = RP.table(_analysis())
    row = next(l for l in t.splitlines() if l.startswith("Primary & 0.05"))
    assert row.index("$-$0.100") < row.index("$-$0.400") < row.index("$-$0.700")       # d, q, u in that order
    assert "All-frozen" in t and "nan" not in t.lower() and "5/6" in t


def test_appendix_tables_have_every_row():
    an = _analysis()
    assert RP.table_markets(an).count("\\\\") == 1 + 2 * 2 * 3 * 2 and "rep5" in RP.table_markets(an)
    assert RP.table_absolute(an).count("\\\\") == 1 + 2 * 3 * 3 * 2
    assert RP.table_terms(an).count("\\\\") == 1 + 2 * 3 * 4 and "C-thr" in RP.table_terms(an)
    assert RP.table_alloc(_sum()).count("\\\\") == 1 + 2 * 3 and "5/6" in RP.table_alloc(_sum()) and "4/5" in RP.table_alloc(_sum())


def test_check_reports_stale_files(tmp_path):
    an, ex = _analysis(), _extract()
    RP.write(an, ex, SHA, tmp_path / "s.json", tmp_path / "t.tex")
    assert RP.check(an, ex, SHA, tmp_path / "s.json", tmp_path / "t.tex") == []
    (tmp_path / "replication_terms.tex").write_text("stale")
    assert RP.check(an, ex, SHA, tmp_path / "s.json", tmp_path / "t.tex")


def test_committed_files_are_current():
    p = HERE / "replication-analysis.json"
    an, ex = json.loads(p.read_text()), json.loads((HERE / "replication-extract.json").read_text())
    tex = HERE.parent / "paper-v2" / "tables" / "replication.tex"
    assert RP.check(an, ex, RP.sha_file(p), HERE / "replication_paper.json", tex) == []


def test_expectation_tally():
    an = _analysis(); an["frozen"]["expectations"]["3"]["verdict"] = "not met"
    s = _sum(an=an)
    assert s["primary"]["exp"] == {"fulfilled": 5, "failed": 0} and s["frozen"]["exp"] == {"fulfilled": 4, "failed": 1}
