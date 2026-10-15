"""Where frozen code finds the two things that arrive after the lock: the proposed rule (allow-listed module and
parameter file) and the sealed H2 family (spec 6). Environment variables point tests at synthetic copies."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import yaml

from .policies.families import FAMILIES, Family
from .policies.identity import h3_family

ROOT = Path(__file__).resolve().parents[1]


def _path(env: str, default: str) -> Path:
    return Path(os.environ.get(env) or (ROOT / default))


PROPOSED_MODULE = _path("TOUCHSTONE_PROPOSED_MODULE", "sim/mechanisms/proposed.py")
PROPOSED_PARAMS = _path("TOUCHSTONE_PROPOSED_PARAMS", "experiments/proposed.yaml")
SEALED_DIR = _path("TOUCHSTONE_SEALED_DIR", "sealed")


def _import(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def proposed_available() -> bool:
    return PROPOSED_MODULE.exists()


def load_proposed_module():
    if not proposed_available():
        raise ValueError(f"no proposed rule module at {PROPOSED_MODULE}")
    mod = _import(PROPOSED_MODULE, "touchstone_proposed")
    if not callable(getattr(mod, "make", None)):
        raise ValueError("the proposed rule module must define make(params) -> Mechanism")
    return mod


def proposed_params() -> dict:
    return yaml.safe_load(PROPOSED_PARAMS.read_text())


def make_rule(rule_name: str, params: dict):
    from .tuning import rule_from_params
    if rule_name == "proposed":
        return load_proposed_module().make(dict(params))
    return rule_from_params(rule_name, params)


def available_families(locked: dict | None = None) -> dict:
    fams: dict = dict(FAMILIES); fams["D2+H3"] = h3_family(FAMILIES["D2"])
    h2 = SEALED_DIR / "h2" / "family.py"
    if h2.exists():
        from .sealed import effective_path, verify_bundle
        if locked is not None:
            verify_bundle(SEALED_DIR, locked)
        mod = _import(effective_path(SEALED_DIR, "h2/family.py"), "sealed_h2_family")     # a logged, verified repair replaces the file
        fam = getattr(mod, "H2", None)
        if not isinstance(fam, Family):
            raise ValueError("sealed/h2/family.py must define H2, a Family")
        fams["H2"] = fam
    return fams


def available_rules() -> list:
    return ["B1", "B2", "B3"] + (["proposed"] if proposed_available() else [])
