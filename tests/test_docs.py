import re
from pathlib import Path

from sim.sealed import BUNDLE_FILES

ROOT = Path(__file__).resolve().parents[1]


def test_custodian_bundle_paths_match_the_loader_and_runbook_scripts_exist():
    text = (ROOT / "docs" / "custodian.md").read_text()
    paths = set(re.findall(r"`sealed/([A-Za-z0-9_./-]+)`", text))
    from sim.sealed import ACCESS_LOG
    assert {p for p in paths if not p.startswith("patches/") and not p.endswith("/") and p != ACCESS_LOG} == set(BUNDLE_FILES)   # the access log is named too and is outside the hash
    rb = (ROOT / "docs" / "lock-runbook.md").read_text()
    for script in set(re.findall(r"scripts/([a-z_]+\.py)", rb)):
        assert (ROOT / "scripts" / script).exists(), script
