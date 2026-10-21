"""The resume of the headline robustness pod after the bank-order verification bug (plan Task 5 ruling)."""
from __future__ import annotations

import json

import pytest

import scripts.explore_attackers as X
import scripts.robustness_v1 as R


@pytest.fixture(scope="module")
def x6_group(tmp_path_factory):
    out = tmp_path_factory.mktemp("rr")
    specs = [s for s in R.manifest_specs() if s["variant"] == "headline" and s["family"] == "X6-SE" and s["rule"] == "B3" and s["c"] == 2]
    jobs = R.jobs_for(specs, True)
    R.assign_banks(jobs, R.manifest_specs(), True, selected=jobs)
    for j in jobs:
        X.write_record(out / "search" / f"{j['name']}.json", X.x_search(j))
    recs = {n: X.read_record(out / "search" / f"{n}.json") for n in jobs[0]["bank_sources"] if (out / "search" / f"{n}.json").exists()}
    names = [n for n in jobs[0]["bank_sources"] if n in recs]
    doc = X.build_bank_doc("X6-SE", recs, ["B3"], None, names=names, group=jobs[0]["bank_group"])
    X.write_record(out / f"bank_{jobs[0]['bank_group']}.json", doc)          # written with sorted keys, as on the pods
    for j in jobs:
        j["bank_sources"] = names
    return out, jobs


def test_sorted_keys_break_the_frozen_check_for_x6(x6_group):
    out, jobs = x6_group
    assert list(json.loads((out / f"bank_{jobs[0]['bank_group']}.json").read_text())["sources"]) != jobs[0]["bank_sources"]
    with pytest.raises(SystemExit):
        X.verify_bank_group(out, jobs[0])


def test_ordered_check_accepts_the_unchanged_bank_and_still_detects_a_change(x6_group):
    from scripts.robustness_resume import verify_bank_group_ordered
    out, jobs = x6_group
    verify_bank_group_ordered(out, jobs[0])
    p = out / "search" / f"{jobs[1]['name']}.json"; d = json.loads(p.read_text()); keep = p.read_text()
    d["attack"]["best_knobs"]["P"] = 7.0; p.write_text(json.dumps(d))
    with pytest.raises(SystemExit):
        verify_bank_group_ordered(out, jobs[0])
    p.write_text(keep)


def test_resume_refuses_a_runner_that_differs_from_the_records(tmp_path):
    from scripts.robustness_resume import check_runner_matches
    rec = {"provenance": {"runner_sha256": "0" * 64, "policy_sha256": "0" * 64}}
    with pytest.raises(SystemExit):
        check_runner_matches(rec)
