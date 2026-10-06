"""Phase 9: final evaluation and the deployable model.

Uses the out-of-fold (OOF) predictions of the selected model `logreg_np` from
Phase 8 (5 repeats x 5 grouped folds; each test predicted once per repeat) to
  1. check calibration (reliability bins, calibration slope/intercept per repeat);
  2. set the alert threshold (largest p with OOF recall >= 0.90 pooled over repeats)
     and the Fire Risk bands, with the observed outcome rate in each band;
  3. put 95% group-bootstrap intervals (resampling atmosphere groups) on the metrics;
  4. break performance down by fuel and suppressant, and list consistently missed fires;
then fits the final pipeline on all 252 primary tests and saves models/final_model.*.

Usage:  .venv/Scripts/python scripts/finalize_model.py
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import sklearn  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import (average_precision_score, brier_score_loss, log_loss,  # noqa: E402
                             roc_auc_score)

from flameguard.dataset import build_modeling_data  # noqa: E402
from flameguard.eda import wilson_interval  # noqa: E402
from flameguard.evaluation import choose_threshold, threshold_metrics  # noqa: E402
from flameguard.model import FINAL_FEATURE_SET, logreg  # noqa: E402
from flameguard.prediction import ApplicabilityDomain, FinalModel, RiskBands  # noqa: E402

OUT = ROOT / "reports" / "phase9"
SELECTED = "logreg_np"
TARGET_RECALL = 0.90
N_BOOT = 2000
RNG = np.random.default_rng(2026)


def calibration_per_repeat(oof: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for r, g in oof.groupby("repeat"):
        p = g["p_sustained"].clip(1e-6, 1 - 1e-6)
        logit = np.log(p / (1 - p)).to_frame("logit")
        fit = LogisticRegression(C=1e6, max_iter=1000).fit(logit, g["y_true"])
        rows.append({"repeat": r, "calibration_slope": fit.coef_[0][0], "calibration_intercept": fit.intercept_[0],
                     "mean_predicted": p.mean(), "observed_rate": g["y_true"].mean(),
                     "brier": brier_score_loss(g["y_true"], g["p_sustained"])})
    return pd.DataFrame(rows)


def reliability_table(avg: pd.DataFrame, n_bins: int = 8) -> pd.DataFrame:
    a = avg.assign(bin=pd.qcut(avg["p"], n_bins))
    t = a.groupby("bin", observed=True).agg(n=("y", "size"), sustained=("y", "sum"), mean_predicted=("p", "mean"))
    ci = [wilson_interval(s, n) for s, n in zip(t["sustained"], t["n"])]
    t["observed_rate"] = t["sustained"] / t["n"]
    t["ci_low"], t["ci_high"] = [c[0] for c in ci], [c[1] for c in ci]
    t.index = t.index.astype(str)
    return t.reset_index()


def metrics(y, p, threshold) -> dict:
    out = {"roc_auc": roc_auc_score(y, p), "pr_auc": average_precision_score(y, p),
           "brier": brier_score_loss(y, p), "log_loss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1])}
    tm = threshold_metrics(y, p, threshold)
    out |= {k: tm[k] for k in ["recall", "precision", "false_negative_rate", "false_positive_rate"]}
    return out


def group_bootstrap(avg: pd.DataFrame, threshold: float) -> pd.DataFrame:
    groups = avg["group"].unique()
    by_group = {g: idx for g, idx in avg.groupby("group").indices.items()}
    draws = []
    for _ in range(N_BOOT):
        pick = RNG.choice(groups, size=len(groups), replace=True)
        idx = np.concatenate([by_group[g] for g in pick])
        y, p = avg["y"].to_numpy()[idx], avg["p"].to_numpy()[idx]
        if y.min() == y.max():
            continue
        draws.append(metrics(y, p, threshold))
    d = pd.DataFrame(draws)
    point = metrics(avg["y"].to_numpy(), avg["p"].to_numpy(), threshold)
    return pd.DataFrame({"estimate": pd.Series(point), "ci_low": d.quantile(0.025), "ci_high": d.quantile(0.975),
                         "boot_draws": len(d)})


def band_table(avg: pd.DataFrame, bands: RiskBands) -> pd.DataFrame:
    a = avg.assign(band=avg["p"].map(bands.band))
    t = a.groupby("band").agg(tests=("y", "size"), sustained=("y", "sum"), mean_predicted=("p", "mean"))
    t = t.reindex(["LOW", "ELEVATED", "HIGH"])
    ci = [wilson_interval(int(s), int(n)) for s, n in zip(t["sustained"], t["tests"])]
    t["observed_sustained_rate"] = t["sustained"] / t["tests"]
    t["ci_low"], t["ci_high"] = [c[0] for c in ci], [c[1] for c in ci]
    return t.reset_index()


def subgroup_table(avg: pd.DataFrame, threshold: float) -> pd.DataFrame:
    rows = []
    for col in ["fuel", "diluent"]:
        for val, g in avg.groupby(col):
            y, p = g["y"].to_numpy(), g["p"].to_numpy()
            tm = threshold_metrics(y, p, threshold)
            rows.append({"subgroup": f"{col}={val}", "tests": len(g), "sustained": int(y.sum()),
                         "roc_auc": roc_auc_score(y, p) if 0 < y.sum() < len(y) else np.nan,
                         "brier": brier_score_loss(y, p), "mean_predicted": p.mean(), "observed_rate": y.mean(),
                         "recall": tm["recall"] if y.sum() else np.nan, "missed_fires": tm["fn"],
                         "false_alarms": tm["fp"]})
    return pd.DataFrame(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(ROOT / "data" / "processed" / "combustion_master.csv")
    data = build_modeling_data(master, "primary")

    oof = pd.read_csv(ROOT / "reports" / "phase8" / "final_oof_predictions.csv")
    oof = oof[oof["model"] == SELECTED]
    assert oof.groupby("repeat")["test_id"].nunique().eq(len(data.y)).all()

    meta = data.meta.set_index("test_id")
    avg = (oof.groupby("test_id").agg(y=("y_true", "first"), p=("p_sustained", "mean"),
                                      p_repeat_sd=("p_sustained", "std")).reset_index())
    avg = avg.join(meta[["group_id_atmosphere", "diluent"]], on="test_id").rename(columns={"group_id_atmosphere": "group"})
    avg = avg.join(data.X.assign(test_id=data.meta["test_id"].to_numpy()).set_index("test_id"), on="test_id")

    # 1. calibration
    cal = calibration_per_repeat(oof)
    cal.to_csv(OUT / "calibration_per_repeat.csv", index=False)
    rel = reliability_table(avg)
    rel.to_csv(OUT / "reliability.csv", index=False)

    # 2. threshold and bands (pooled OOF over all repeats)
    alert = choose_threshold(oof["y_true"].to_numpy(), oof["p_sustained"].to_numpy(), TARGET_RECALL)
    bands = RiskBands(alert_threshold=alert)
    bt = band_table(avg, bands)
    bt.to_csv(OUT / "risk_bands.csv", index=False)
    bands.band_stats = {r["band"]: {k: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v)
                                    for k, v in r.items() if k != "band"} for r in bt.to_dict("records")}

    # 3. bootstrap intervals
    boot = group_bootstrap(avg, alert)
    boot.to_csv(OUT / "metrics_bootstrap.csv")

    # 4. subgroups and consistent misses
    sub = subgroup_table(avg, alert)
    sub.to_csv(OUT / "subgroups.csv", index=False)
    missed = (oof.assign(missed=(oof["y_true"] == 1) & (oof["p_sustained"] < alert))
              .groupby("test_id")["missed"].sum().rename("missed_in_repeats"))
    fn = avg.join(missed, on="test_id")
    fn = fn[(fn["y"] == 1) & (fn["missed_in_repeats"] >= 3)]
    fn = fn.join(master.set_index("test_id")[["flex_identifier", "outcome_raw", "qc_flags"]], on="test_id")
    fn = fn[["test_id", "flex_identifier", "fuel", "diluent", "x_o2", "x_co2", "x_he", "d0_mm", "outcome_raw",
             "p", "missed_in_repeats", "qc_flags"]].sort_values("p")
    fn.to_csv(OUT / "consistently_missed_fires.csv", index=False)

    # 5. final fit on all primary tests
    pipeline = logreg(feature_set=FINAL_FEATURE_SET).fit(data.X, data.y)
    names = list(pipeline.named_steps["pre"].get_feature_names_out())
    coefs = dict(zip(names, pipeline.named_steps["model"].coef_[0].round(4).tolist()))
    domain = ApplicabilityDomain.fit(data.X, data.groups)
    nested = pd.read_csv(ROOT / "reports" / "phase8" / "final_fold_metrics.csv")
    nested = nested[nested["model"] == SELECTED]
    metadata = {
        "model": "L2 logistic regression (C=1), fuel x droplet-size interaction, no pressure (decision D-001)",
        "features": names,
        "standardised_coefficients": coefs,
        "intercept": float(pipeline.named_steps["model"].intercept_[0]),
        "training_tests": int(len(data.y)), "training_sustained": int(data.y.sum()),
        "training_data_sha256": hashlib.sha256((ROOT / "data" / "processed" / "combustion_master.csv").read_bytes()).hexdigest(),
        "scope": "Methanol or n-heptane droplets, quiescent microgravity (ISS FLEX), 0.7-1 atm, "
                 "within the tested O2 / CO2 / He / droplet-size ranges",
        "validation": {
            "scheme": "5 x repeated 5-fold StratifiedGroupKFold by chamber atmosphere (25 folds)",
            "nested_threshold_estimates": {m: [float(nested[m].mean()), float(nested[m].std())]
                                           for m in ["roc_auc", "pr_auc", "brier", "log_loss", "recall@safe",
                                                     "precision@safe", "false_negative_rate@safe"]},
            "oof_bootstrap_95ci": {k: [float(v["estimate"]), float(v["ci_low"]), float(v["ci_high"])]
                                   for k, v in boot.iterrows()},
            "calibration_slope_range": [float(cal["calibration_slope"].min()), float(cal["calibration_slope"].max())],
        },
        "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                     "pandas": pd.__version__, "numpy": np.__version__},
        "label": "Research prototype trained on NASA PSI-69 (FLEX), DOI 10.60555/mbq8-0451. Not a certified "
                 "spacecraft fire-safety system.",
    }
    FinalModel(pipeline=pipeline, bands=bands, domain=domain, metadata=metadata).save()

    print(cal.round(3).to_string())
    print(rel.round(3).to_string())
    print(f"alert threshold = {alert:.4f}")
    print(bt.round(3).to_string())
    print(boot.round(3).to_string())
    print(sub.round(3).to_string())
    print(fn.round(3).to_string())
    print(json.dumps(coefs, indent=1))
    print("support radius:", domain.support_radius)
    return 0


if __name__ == "__main__":
    sys.exit(main())
