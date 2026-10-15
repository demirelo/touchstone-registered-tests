"""Run the H1 five-episode procedure (spec 5.4) against registered rules with a model backend: the comprehension check
first, every uncached request counted and capped by the budgeted backend, replay from the prompt cache, and the
token pilot that sets the cost cap. Ruling D9: the T = 200 calibration verifies the tuned files; the T = 100
calibration builds the market."""
from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sweep import load_params  # noqa: E402
from sim.calibrate import cell_config, load_calibration  # noqa: E402
from sim.config import MarketConfig  # noqa: E402
from sim.describe import comprehension_questions, describe_record, load_vocabulary, render  # noqa: E402
from sim.llm_actor import (ACTOR_INSTRUCTIONS, BudgetedBackend, CapExceeded, FakeBackend, H1_ROW_FIELDS, PilotTargetReached, PromptCache,  # noqa: E402
                           comprehension_check, h1_rows, make_backend, run_h1_cell)
from sim.locked import load_locked, market_config_from_locked, seeds as locked_seeds, settings_hash  # noqa: E402
from sim.positions import positions  # noqa: E402
from sim.registry import available_rules, make_rule  # noqa: E402

META = ["backend", "model", "rule", "beta", "eval_namespace", "T", "budget"]
FIELDS = META + H1_ROW_FIELDS


def smoke_config() -> MarketConfig:
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=6, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=0.0, budget=0.0)


def h1_config(locked: dict, cal, beta: float, base: MarketConfig) -> MarketConfig:
    return cell_config(base, cal, rho=float(locked["rho"]["default"]), beta=float(beta))


def make_fake_cheat(instructions: str):
    def fn(kind, payload):
        if kind == "comprehension":
            return {"answers": {q["id"]: q["options"][0]["label"] for q in payload["questions"]}}
        p = payload["state"]["provider"]
        return {"effort": 0.0, "offer": {"claim": 1.0, "bid": p["a"]}}
    return FakeBackend(fn, instructions=instructions)


def run_h1(o: dict) -> tuple[dict, int]:
    lk = load_locked(); h = dict(lk["h1"]); smoke = bool(o["smoke"])
    reps = 2 if smoke else int(h["repetitions"]); betas = [0.05] if smoke else [float(b) for b in h["betas"]]
    lk_run = dict(lk, h1=dict(h, repetitions=reps))
    out = Path(o["out"]); out.mkdir(parents=True, exist_ok=True)
    cache_dir = o["cache"] or (out / "cache" if smoke else (Path("experiments/cache/h1") if o["eval_namespace"] == "final_eval" else Path("experiments/cache")) / o["backend"])
    cache = PromptCache(cache_dir)                                   # D3: development runs under experiments/cache/<backend>/, the final-eval H1 runs under experiments/cache/h1/<backend>/
    if o.get("prompt"):
        from sim.registry import SEALED_DIR
        from sim.sealed import effective_path
        pp = Path(o["prompt"]).resolve()
        instructions = (effective_path(SEALED_DIR, str(pp.relative_to(SEALED_DIR.resolve()))) if pp.is_relative_to(SEALED_DIR.resolve()) else pp).read_text()   # a sealed path goes through the repair overlay
    else:
        instructions = ACTOR_INSTRUCTIONS
    raw = make_fake_cheat(instructions) if o["backend"] == "fake-cheat" else make_backend(o["backend"], lk, instructions)
    calls_cap = int(o["max_calls"] if o["max_calls"] is not None else h["calls_cap"])
    cost_cap = o["max_cost_usd"] if o["max_cost_usd"] is not None else h.get("cost_cap_usd")
    backend = BudgetedBackend(raw, max_calls=calls_cap, max_cost_usd=cost_cap, prices=h.get("prices", {}), stop_at=int(o["pilot_calls"]) if o["pilot"] else None,
                              ledger=None if (smoke or o["pilot"]) else cache.directory / "ledger.json")      # the caps are cumulative across restarts of a real run
    from sim.calibrate import calibrate
    from sim.cell import market_key
    if not smoke and not (o["calibration"] and o["calibration_t100"]):
        raise SystemExit("a real run needs --calibration and --calibration-t100")
    if o["tuned_dir"] and not o["calibration"]:
        raise SystemExit("--tuned-dir needs --calibration (the T = 200 calibration that verifies the tuned files)")
    if smoke:
        base = smoke_config(); cal100 = calibrate(base, [4000, 4001])                     # the smoke market calibrates itself: no file can mismatch it
        cal200 = load_calibration(o["calibration"]) if o["calibration"] else cal100
    else:
        cal200 = load_calibration(o["calibration"]); cal100 = load_calibration(o["calibration_t100"])
        base = dataclasses.replace(market_config_from_locked(lk), T=int(h["T"]))
        if int(cal100.T) != int(h["T"]):
            raise SystemExit(f"--calibration-t100 has T = {cal100.T}, locked h1.T is {h['T']}")
        if cal100.market_key != market_key(base):
            raise SystemExit("--calibration-t100 belongs to a different market than the H1 market built from locked.yaml")
    try:
        eval_seeds = tuple(locked_seeds(lk, o["eval_namespace"]))
    except ValueError as e:
        raise SystemExit(f"evaluation namespace {o['eval_namespace']} is not available: {e}")
    train = tuple(locked_seeds(lk, "dev_train")[:4]); selection = tuple(locked_seeds(lk, "dev_train")[:5])
    voc = load_vocabulary(); qs = comprehension_questions()
    rules = [r.strip() for r in o["rules"].split(",") if r.strip()]
    unknown = [r for r in rules if r not in available_rules()]
    if unknown:
        raise SystemExit(f"unknown rules {unknown}; available: {available_rules()}")
    tuned = Path(o["tuned_dir"]) if o["tuned_dir"] else None
    params = {r: load_params(r, tuned, smoke, cal200.market_key, settings_hash(lk), cal200.seeds) for r in rules}
    summary = {"backend": backend.name, "model": backend.model, "instructions_sha256": hashlib.sha256(instructions.encode()).hexdigest(), "T": int(base.T),
               "calls_cumulative": backend.calls,
               "eval_namespace": o["eval_namespace"], "calibration_t100_sha256": hashlib.sha256(Path(o["calibration_t100"]).read_bytes()).hexdigest() if o["calibration_t100"] else None,
               "tuned_sha256": {r: hashlib.sha256((tuned / f"tuned_{r}.json").read_bytes()).hexdigest() for r in rules if tuned and (tuned / f"tuned_{r}.json").exists()},
               "calls_cap": calls_cap, "cost_cap_usd": cost_cap, "calls": 0, "cache_hits": 0, "usage": backend.usage, "cost_usd": 0.0,
               "comprehension": {}, "cells": {}, "partial": [], "stopped_by": None, "smoke": smoke}
    rows: list = []; status = 0

    def flush():
        summary["calls"] = backend.calls_this_run; summary["calls_cumulative"] = backend.calls; summary["cost_usd"] = backend.cost_usd
        (out / "h1_summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=float))
        with (out / "h1_rows.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)

    try:
        summary["comprehension"] = comprehension_check(backend, cache, {r: make_rule(r, params[r]) for r in rules}, qs)
        for rule in rules:
            for beta in betas:
                key = f"{rule}|{beta}"; summary["partial"].append(key)
                cfg = h1_config(lk, cal100, beta, base)
                rule_factory = (lambda r=rule: make_rule(r, params[r]))
                rendered = render(describe_record(rule_factory()), voc)
                res = run_h1_cell(cfg, rule_factory, positions(cfg)["median"], backend, cache, rendered, train, eval_seeds[:reps], lk_run, selection)
                meta = {"backend": backend.name, "model": backend.model, "rule": rule, "beta": beta, "eval_namespace": o["eval_namespace"], "T": int(cfg.T), "budget": float(cfg.budget)}
                rows += h1_rows(res, meta)
                summary["cache_hits"] += sum(r.cache_hits for r in res.attack + res.twin + res.clipped + res.reference.twin_results)
                summary["cells"][key] = {"calls": res.calls, "new_calls_clipped": res.new_calls_clipped, "invalid_count": res.invalid_count,
                                         "inconclusive": res.inconclusive, "reference": res.reference.name, "reference_scores": res.reference.scores, "usage": res.usage}
                summary["partial"].remove(key)
                flush()
    except CapExceeded as e:
        summary["stopped_by"] = e.reason; status = 3
    except PilotTargetReached:
        summary["stopped_by"] = "pilot target"
    finally:
        flush()
    if o["pilot"]:
        n = max(backend.calls_this_run, 1); target = int(o["pilot_calls"])
        pilot = {"backend": backend.name, "model": backend.model, "calls": backend.calls_this_run, "target": target, "complete": backend.calls_this_run >= target,
                 "fallback_rounds": backend.malformed, "fallback_rate": backend.malformed / n, "stop_reasons": backend.stop_reasons,
                 "mean_input_tokens": backend.usage["input_tokens"] / n, "mean_output_tokens": backend.usage["output_tokens"] / n,
                 "mean_cache_creation_input_tokens": backend.usage.get("cache_creation_input_tokens", 0) / n, "mean_cache_read_input_tokens": backend.usage.get("cache_read_input_tokens", 0) / n,
                 "mean_latency_s": (sum(backend.latencies) / len(backend.latencies)) if backend.latencies else 0.0,
                 "cost_per_call_usd": backend.cost_usd / n, "projected_cost_usd": backend.cost_usd / n * int(h["calls_cap"])}
        (out / f"pilot_{backend.name}.json").write_text(json.dumps(pilot, indent=1)); print(json.dumps(pilot))
        status = 0 if pilot["complete"] else 4
    if status == 3:
        print(f"stopped: {summary['stopped_by']}; partial cells {summary['partial']} are not in h1_rows.csv; results so far are in {out}", file=sys.stderr)
    return summary, status


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True, choices=["fake-honest", "fake-cheat", "anthropic", "jev"])
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--calibration", default=None, help="the T = 200 calibration (verifies the tuned files, ruling D9); required with --tuned-dir or without --smoke")
    ap.add_argument("--calibration-t100", dest="calibration_t100", default=None, help="the T = 100 calibration the H1 market is built from; required without --smoke")
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None); ap.add_argument("--cache", default=None); ap.add_argument("--out", required=True)
    ap.add_argument("--eval-namespace", dest="eval_namespace", default="dev_val", choices=["dev_val", "final_eval"])
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--pilot-calls", dest="pilot_calls", type=int, default=200)
    ap.add_argument("--max-calls", dest="max_calls", type=int, default=None); ap.add_argument("--max-cost-usd", dest="max_cost_usd", type=float, default=None)
    ap.add_argument("--prompt", default=None, help="path of the sealed H1 prompt (sealed/h1_prompt.txt); replaces the development instructions")
    s, status = run_h1(vars(ap.parse_args()))
    print(json.dumps({"calls": s["calls"], "cost_usd": s["cost_usd"], "cells": {k: v["inconclusive"] for k, v in s["cells"].items()}, "partial": s["partial"]}))
    sys.exit(status)


if __name__ == "__main__":
    main()
