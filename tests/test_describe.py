import pytest
from sim.describe import (DESCRIBE_FIELDS, NOT_EXPRESSIBLE, load_vocabulary, validate_record, render, uses_not_expressible,
                          describe_record, comprehension_questions, score_comprehension, correct_value)
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.mechanisms.second_score import SecondScore
from sim.mechanisms.ablation import EnforcementAblation


def rules():
    return [PostedPrices(0.25, 0.40, 0.55), PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), SecondScore(tol=0.12, L=10),
            EnforcementAblation(SecondScore(tol=0.12, L=10), PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=20))]


def test_every_rule_record_uses_only_vocabulary_values():
    voc = load_vocabulary()
    for r in rules():
        rec = describe_record(r)
        assert set(rec) >= set(DESCRIBE_FIELDS)
        validate_record(rec, voc)
        assert not uses_not_expressible(rec)


def test_vocabulary_refuses_unknown_values():
    voc = load_vocabulary()
    rec = describe_record(PostedPrices(0.25, 0.40, 0.55))
    bad = dict(rec, failed_audit="we think about it")
    with pytest.raises(ValueError, match="failed_audit"):
        validate_record(bad, voc)
    missing = {k: v for k, v in rec.items() if k != "holdback"}
    with pytest.raises(ValueError, match="holdback"):
        validate_record(missing, voc)
    ne = dict(rec, holdback=NOT_EXPRESSIBLE)
    validate_record(ne, voc)
    assert uses_not_expressible(ne)


def test_renderer_receives_only_the_record_and_is_noninterfering(monkeypatch):
    voc = load_vocabulary()
    rec = describe_record(PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10))
    text = render(rec, voc)
    assert "0.12" in text and "banned for 10 rounds" in text and "uniform random" in text and "PostedRandomAudit" not in text
    assert "claim times the job value reaches the tier price" in text and "0.5 to below 0.8" in text and "tier the job was allocated in" in text   # the acceptance condition, the tiers, the payment
    b3 = render(describe_record(SecondScore(tol=0.12, L=10)), voc)
    assert "score = job value times claim minus bid" in b3 and "negative score are not eligible" in b3 and "zero when there is none" in b3
    for bad in ("twelve", float("nan"), float("inf"), True):
        with pytest.raises(ValueError, match="numeric"):
            validate_record(dict(rec, parameters=dict(rec["parameters"], audit_tolerance=bad)), voc)
    assert len(voc["numeric"]["holdback"]) == 2 and all("," in v for v in voc["numeric"]["holdback"])             # YAML kept the two values whole
    hb = dict(rec, holdback=voc["numeric"]["holdback"][0])
    with pytest.raises(ValueError, match="holdback"):
        validate_record(hb, voc)                                                                                   # a hold-back value needs its figure
    hb["parameters"] = dict(rec["parameters"], holdback=7)
    assert "last 7 rounds are held back" in render(hb, voc)
    # the renderer sees the record only: a spy record with a changed numeric parameter changes the bytes; nothing else can
    spy = dict(rec, parameters=dict(rec["parameters"], audit_tolerance=0.16))
    assert render(spy, voc) != text
    # noninterference: renaming the class and changing its source comments does not change the rendered bytes
    class RenamedRuleWithDifferentComments(PostedRandomAudit):
        """A docstring that mentions tolerance 0.99 and bans forever."""
    assert render(describe_record(RenamedRuleWithDifferentComments(0.25, 0.40, 0.55, tol=0.12, L=10)), voc) == text
    assert render(rec, voc) == text                                              # deterministic


def test_comprehension_fixture_scores_answers_from_the_record():
    qs = comprehension_questions()
    assert len(qs) >= 6 and all({"id", "question", "answer_from", "options"} <= set(q) for q in qs)
    rec = describe_record(PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10))
    perfect = {q["id"]: next(o for o in q["options"] if o["value"] == correct_value(rec, q["answer_from"]))["label"] for q in qs}
    assert score_comprehension(perfect, rec, qs) == len(qs)
    assert correct_value(rec, "parameters.audit_tolerance") == "0.12" and correct_value(rec, "parameters.ban_length") == "10"
    assert correct_value(describe_record(PostedPrices(0.25, 0.40, 0.55)), "parameters.ban_length") == "none"
    assert len([q for q in qs if q["answer_from"].startswith("parameters.")]) == 2
    wrong = dict(perfect); first = qs[0]; wrong[first["id"]] = next(o["label"] for o in first["options"] if o["label"] != perfect[first["id"]])
    assert score_comprehension(wrong, rec, qs) == len(qs) - 1
    assert score_comprehension({}, rec, qs) == 0


def test_record_keys_outside_the_fields_are_refused():
    """Final review F10: a record with a key outside the describe() fields is refused, and so is a parameters entry for a
    non-numeric field."""
    voc = load_vocabulary(); rec = describe_record(PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10))
    with pytest.raises(ValueError, match="note"):
        validate_record(dict(rec, note="x"), voc)
    with pytest.raises(ValueError, match="parameters"):
        validate_record(dict(rec, parameters=dict(rec["parameters"], payment=3)), voc)


NOT_EXPRESSIBLE_MODULE = '''
from sim.mechanisms.base import Mechanism, Consequences

class Proposed(Mechanism):
    name = "proposed"
    def __init__(self, tol, L): self.tol, self.L = float(tol), int(L)
    def allocate(self, values_t, offers, view): return {}
    def price(self, assignment, values_t, offers, view): return {}
    def audit(self, assignment, view): return []
    def enforce(self, records, view): return Consequences()
    def describe(self):
        return {"allocation_order": "jobs in descending value; each job goes to the offer with capacity and the highest score, score = job value times claim minus bid, offers with a negative score are not eligible, at random among equal scores",
                "eligibility": "active offers with capacity", "payment": "second score: job value times claim minus the highest score among the other eligible offers for that job, zero when there is none",
                "audit_selection": "not expressible", "audit_tolerance": "number", "failed_audit": "full refund of the audited job", "ban_length": "number", "holdback": "none",
                "parameters": {"audit_tolerance": self.tol, "ban_length": self.L}}

def make(params):
    return Proposed(params["tol"], params["L"])
'''


def test_describe_proposed_writer_accepts_only_the_registered_not_expressible_record(tmp_path, monkeypatch):
    import subprocess, sys, yaml
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    params = tmp_path / "proposed.yaml"; params.write_text(yaml.safe_dump({"rule": "proposed", "best_params": {"allocation": "A", "targeting": "T1", "tol": 0.12, "L": 10}}))
    out = tmp_path / "describe.yaml"
    cmd = [sys.executable, str(root / "scripts" / "describe_proposed.py"), "--params", str(params), "--out", str(out)]
    expressible = tmp_path / "expressible.py"
    expressible.write_text((root / "tests" / "test_tune_proposed_script.py").read_text().split("SYNTH = '''")[1].split("'''")[0])
    env = {**__import__("os").environ, "TOUCHSTONE_PROPOSED_MODULE": str(expressible)}
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=root, env=env)
    assert r.returncode != 0 and "not expressible" in (r.stderr + r.stdout) and not out.exists()
    ne = tmp_path / "ne.py"; ne.write_text(NOT_EXPRESSIBLE_MODULE)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=root, env={**env, "TOUCHSTONE_PROPOSED_MODULE": str(ne)})
    assert r.returncode == 0, r.stderr[-1500:]
    rec = yaml.safe_load(out.read_text())
    assert rec["audit_selection"] == NOT_EXPRESSIBLE and rec["parameters"] == {"audit_tolerance": 0.12, "ban_length": 10}
    assert r.stdout.startswith("Market rule.") and "audit selection of this rule is not expressible" in r.stdout
