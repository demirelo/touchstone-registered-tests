"""Figures 1 and 2 (spec 8) from the sweep's per-seed evaluate records."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sim.coverage import load_report  # noqa: E402
from sim.intervals import bound  # noqa: E402
from sim.locked import load_locked  # noqa: E402


def _upper(g: np.ndarray, iv: dict, coverage: dict | None, family: str) -> tuple[float, str]:
    """The upper 95% bound by the admitted method at this sample size; without a coverage report the nominal method of
    spec 8 (the t bound for H1, the percentile bootstrap for parametrized families), labeled 'nominal'."""
    n = int(len(g))
    if coverage is None:
        method = "t" if family == "H1" else "percentile"; label = f"{method} (nominal)"
    else:
        method = coverage.get("method_at_n", {}).get(str(n)); label = method
    if method is None or n < 2:
        return float("nan"), "none"
    return float(bound(method, g, "upper", 0.95, iv).value), label


def figure_frames(sweep_out: Path, locked: dict, coverage: dict | None = None, h1_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    sweep_out = Path(sweep_out); iv = locked["intervals"]; sigma = float(locked["market"]["sigma"]); bh = float(locked["beta_headline"])
    headline = json.loads((sweep_out / "headline.json").read_text()) if (sweep_out / "headline.json").exists() else {}
    f1, f2 = [], []
    for p in sorted((sweep_out / "evaluate").glob("*.json")):
        rec = json.loads(p.read_text()); spec = rec["spec"]
        if spec["section"] not in ("development", "heldout"):
            continue
        want = headline.get(f"{spec['rule']}/{spec['family']}", {}).get("headline", "median") if float(spec["beta"]) == bh else "median"
        if spec["position"] != want:
            continue
        df = pd.DataFrame(rec["rows"]); tol = rec.get("params", {}).get("tol"); g = df["gain"].to_numpy(dtype=float)
        upper, method = _upper(g, iv, coverage, spec["family"])
        base = {"rule": spec["rule"], "family": spec["family"], "beta": float(spec["beta"]), "position": spec["position"], "audit_spend": float(df["audit_spend_attack"].mean())}
        f1.append({**base, "gain_mean": float(g.mean()), "gain_upper": upper, "bound_method": method, "n_seeds": int(len(g)),
                   "honest_failure_rate": float(stats.norm.cdf(-float(tol) / sigma)) if tol is not None else 0.0})
        f2.append({**base, **{k: float(df[k].mean()) for k in ("eff_honest", "eff_ref", "eff_clip", "eff_attack")}})
    if h1_dir is not None and (Path(h1_dir) / "h1_rows.csv").exists():
        h1 = pd.read_csv(Path(h1_dir) / "h1_rows.csv")
        for (rule, beta), df in h1.groupby(["rule", "beta"]):
            g = df["gain"].to_numpy(dtype=float); upper, method = _upper(g, iv, coverage, "H1")
            base = {"rule": rule, "family": "H1", "beta": float(beta), "position": "median", "audit_spend": float((df["audit_cost_attack"] / df["sstar"]).mean())}
            f1.append({**base, "gain_mean": float(g.mean()), "gain_upper": upper, "bound_method": method, "n_seeds": int(len(g)), "honest_failure_rate": float("nan")})
            f2.append({**base, "eff_honest": float("nan"), "eff_ref": float(df["eff_ref"].mean()), "eff_clip": float(df["eff_clip"].mean()), "eff_attack": float(df["eff_attack"].mean())})
    return pd.DataFrame(f1), pd.DataFrame(f2)


def draw(fig1: pd.DataFrame, fig2: pd.DataFrame, out_dir: Path) -> list[Path]:
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True); paths = []
    fams = sorted(fig1.family.unique()); fig, axes = plt.subplots(1, max(len(fams), 1), figsize=(5 * max(len(fams), 1), 4), squeeze=False)
    for ax, fam in zip(axes[0], fams):
        d = fig1[fig1.family == fam]
        for rule, g in d.groupby("rule"):
            g = g.sort_values("audit_spend")
            label = f"{rule} (honest failure rate {g.honest_failure_rate.iloc[0]:.3f})" if np.isfinite(g.honest_failure_rate.iloc[0]) else rule
            line, = ax.plot(g.audit_spend, g.gain_mean, marker="o", label=label)
            ax.plot(g.audit_spend, g.gain_upper, linestyle="--", alpha=0.5, color=line.get_color())
        ax.set_title(f"family {fam}"); ax.set_xlabel("audit spend / S*"); ax.set_ylabel("gain (S* / N units): mean, upper 95% bound dashed"); ax.legend(fontsize=7)
    p1 = out_dir / "figure1_gain_vs_audit.png"; fig.tight_layout(); fig.savefig(p1, dpi=150); plt.close(fig); paths.append(p1)
    rules = sorted(fig2.rule.unique()); fig, axes = plt.subplots(1, max(len(rules), 1), figsize=(5 * max(len(rules), 1), 4), squeeze=False)
    for ax, rule in zip(axes[0], rules):
        d = fig2[fig2.rule == rule]
        for fam, g in d.groupby("family"):
            g = g.sort_values("audit_spend")
            for k, ls in (("eff_honest", "-"), ("eff_ref", "--"), ("eff_clip", "-."), ("eff_attack", ":")):
                ax.plot(g.audit_spend, g[k], linestyle=ls, marker=".", label=f"{fam} {k[4:]}")
        ax.set_title(f"rule {rule}"); ax.set_xlabel("audit spend / S*"); ax.set_ylabel("gross efficiency"); ax.legend(fontsize=6, ncol=2)
    p2 = out_dir / "figure2_efficiency_quadruple.png"; fig.tight_layout(); fig.savefig(p2, dpi=150); plt.close(fig); paths.append(p2)
    return paths


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--sweep-out", dest="sweep_out", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--coverage-report", dest="coverage_report", default=None); ap.add_argument("--h1-dir", dest="h1_dir", default=None)
    a = ap.parse_args(); lk = load_locked()
    f1, f2 = figure_frames(Path(a.sweep_out), lk, coverage=load_report(a.coverage_report) if a.coverage_report else None, h1_dir=Path(a.h1_dir) if a.h1_dir else None)
    paths = draw(f1, f2, Path(a.out))
    f1.merge(f2, on=["rule", "family", "beta", "position", "audit_spend"]).to_csv(Path(a.out) / "figure_data.csv", index=False)
    print("wrote " + ", ".join(str(p) for p in paths))


if __name__ == "__main__":
    main()
