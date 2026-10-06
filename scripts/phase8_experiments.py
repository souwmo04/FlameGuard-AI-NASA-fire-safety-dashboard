"""Phase 8: tuning, feature ablation, sensitivity variants and stress tests.

All sections use the Phase 7 primary dataset and the same 25 grouped splits
(5 x repeated StratifiedGroupKFold, seed 0) unless stated otherwise.

Writes to reports/phase8/:
  tuning_fold_metrics.csv, tuning_oof_predictions.csv  nested-CV tuned models
  model_selection.csv                                  pre-registered selection rule applied
  ablation.csv, ablation_paired.csv                    logistic regression feature ablations
  sensitivity_metrics.csv, sensitivity_coefficients.csv dataset variants
  stress_metrics.csv                                   held-out-condition splits
  stress_no_pressure.csv                               same, logistic with vs without pressure
  final_fold_metrics.csv, final_oof_predictions.csv    final candidates without pressure (D-001)
  final_selection.csv                                  selection rule applied to final candidates

Usage (from the project root):
    .venv/Scripts/python scripts/phase8_experiments.py                 # everything
    .venv/Scripts/python scripts/phase8_experiments.py --only ablation
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from flameguard.dataset import build_modeling_data  # noqa: E402
from flameguard.evaluation import (cross_validate, probability_metrics,  # noqa: E402
                                   threshold_metrics)
from flameguard.model import (FINAL_CANDIDATES, TUNED_MODELS, logreg, o2_only_logreg,  # noqa: E402
                              random_forest, xgboost)
from flameguard.validation import repeated_group_kfold, stress_splits  # noqa: E402

OUT = ROOT / "reports" / "phase8"
PHASE7 = ROOT / "reports" / "phase7"
SEED, N_SPLITS, N_REPEATS = 0, 5, 5

# Pre-registered (stated before Phase 8 was run): lowest mean log loss over the 25 outer
# folds; any simpler model within one standard error of the best is preferred.
COMPLEXITY = ["o2_only_logreg", "logreg", "logreg_tuned", "xgboost", "xgboost_tuned",
              "random_forest", "random_forest_tuned"]
COMPLEXITY_FINAL = ["logreg_np", "logreg_np_tuned", "xgboost_np", "xgboost_np_tuned",
                    "random_forest_np", "random_forest_np_tuned"]


def load_primary():
    master = pd.read_csv(ROOT / "data" / "processed" / "combustion_master.csv")
    data = build_modeling_data(master, "primary")
    splits = repeated_group_kfold(data.y, data.groups, N_SPLITS, N_REPEATS, SEED)
    return master, data, splits


def timed(label, fn):
    t0 = time.time()
    out = fn()
    print(f"  {label:42s} {time.time() - t0:6.0f}s")
    return out


# --- 1. tuning ------------------------------------------------------------------

def run_tuning():
    _, data, splits = load_primary()
    folds, preds = [], []
    for name, factory in TUNED_MODELS.items():
        f, p = timed(name, lambda: cross_validate(factory, data, splits, model_name=name))
        folds.append(f)
        preds.append(p)
    tuned = pd.concat(folds, ignore_index=True)
    tuned.to_csv(OUT / "tuning_fold_metrics.csv", index=False)
    pd.concat(preds, ignore_index=True).to_csv(OUT / "tuning_oof_predictions.csv", index=False)

    # chosen hyperparameters per outer fold
    print(tuned.groupby("model")["best_params"].value_counts().to_string())
    select_model(tuned)


def select_model(tuned: pd.DataFrame, include_phase7: bool = True, complexity: list[str] = COMPLEXITY,
                 out_name: str = "model_selection.csv") -> pd.DataFrame:
    if include_phase7:
        base = pd.read_csv(PHASE7 / "fold_metrics.csv")
        allf = pd.concat([base[base["model"] != "majority_baseline"], tuned], ignore_index=True)
    else:
        allf = tuned
    rows = []
    for m, g in allf.groupby("model"):
        n = len(g)
        rows.append({"model": m, "log_loss_mean": g["log_loss"].mean(),
                     "log_loss_se": g["log_loss"].std() / np.sqrt(n),
                     "brier_mean": g["brier"].mean(), "roc_auc_mean": g["roc_auc"].mean(),
                     "pr_auc_mean": g["pr_auc"].mean(), "recall@safe": g["recall@safe"].mean(),
                     "precision@safe": g["precision@safe"].mean(), "folds": n})
    sel = pd.DataFrame(rows).sort_values("log_loss_mean").reset_index(drop=True)
    best = sel.iloc[0]
    limit = best["log_loss_mean"] + best["log_loss_se"]
    sel["within_1se_of_best"] = sel["log_loss_mean"] <= limit
    sel["complexity_rank"] = sel["model"].map({m: i for i, m in enumerate(complexity)})
    eligible = sel[sel["within_1se_of_best"]].sort_values("complexity_rank")
    chosen = eligible.iloc[0]["model"]
    sel["selected"] = sel["model"] == chosen
    sel.to_csv(OUT / out_name, index=False)
    print(sel.round(4).to_string())
    print(f"Selected: {chosen} (best by log loss: {best['model']}, 1-SE limit {limit:.4f})")
    return sel


# --- 2. feature ablation ----------------------------------------------------------

ABLATIONS = {
    "full (base + fuel x d0)": lambda: logreg(),
    "no fuel x d0 interaction": lambda: logreg(interaction=False),
    "+ p_o2_atm": lambda: logreg(feature_set="with_po2"),
    "- pressure": lambda: logreg(feature_set="no_pressure"),
    "- droplet size (and interaction)": lambda: logreg(feature_set="no_d0", interaction=False),
    "- suppressant (CO2, He)": lambda: logreg(feature_set="no_suppressant"),
    "- fuel (and interaction)": lambda: logreg(feature_set="no_fuel", interaction=False),
    "O2 + fuel only": lambda: logreg(feature_set="o2_fuel", interaction=False),
}


def run_ablation():
    _, data, splits = load_primary()
    folds = []
    for name, factory in ABLATIONS.items():
        f, _ = timed(name, lambda: cross_validate(factory, data, splits, model_name=name, select_threshold=False))
        folds.append(f)
    f = pd.concat(folds, ignore_index=True)
    summary = f.groupby("model", sort=False)[["roc_auc", "pr_auc", "brier", "log_loss"]].agg(["mean", "std"])
    summary.columns = [f"{a}_{b}" for a, b in summary.columns]
    summary.to_csv(OUT / "ablation.csv")

    ref = "full (base + fuel x d0)"
    rows = []
    for metric, better in [("roc_auc", 1), ("log_loss", -1)]:
        w = f.pivot(index="split", columns="model", values=metric)
        for m in ABLATIONS:
            if m == ref:
                continue
            d = w[m] - w[ref]
            rows.append({"variant": m, "metric": metric, "mean_delta_vs_full": d.mean(), "sd": d.std(),
                         "variant_better_folds": int((better * d > 0).sum()), "folds": len(d)})
    paired = pd.DataFrame(rows)
    paired.to_csv(OUT / "ablation_paired.csv", index=False)
    print(summary.round(3).to_string())
    print(paired.round(4).to_string())


# --- 3. sensitivity variants -------------------------------------------------------

def run_sensitivity():
    master = pd.read_csv(ROOT / "data" / "processed" / "combustion_master.csv")
    rows, coefs = [], []
    for variant in ["primary", "exclude_disruption", "impute_d0", "exclude_anomalies"]:
        data = build_modeling_data(master, variant)
        splits = repeated_group_kfold(data.y, data.groups, N_SPLITS, N_REPEATS, SEED)
        impute = variant == "impute_d0"
        for name, factory in [("logreg", lambda: logreg(impute=impute)),
                              ("xgboost", lambda: xgboost(impute=impute)),
                              ("o2_only_logreg", o2_only_logreg)]:
            f, _ = timed(f"{variant} / {name}", lambda: cross_validate(factory, data, splits, model_name=name))
            row = {"variant": variant, "model": name, "tests": len(data.y), "sustained": int(data.y.sum())}
            for m in ["roc_auc", "pr_auc", "brier", "log_loss", "recall@safe", "precision@safe"]:
                row[f"{m}_mean"] = f[m].mean()
                row[f"{m}_sd"] = f[m].std()
            rows.append(row)
        # standardised logistic coefficients on all tests of the variant (direction / size stability)
        fitted = logreg(impute=impute).fit(data.X, data.y)
        names = fitted.named_steps["pre"].get_feature_names_out()
        for n, c in zip(names, fitted.named_steps["model"].coef_[0]):
            coefs.append({"variant": variant, "feature": n, "std_coef": c})
    pd.DataFrame(rows).to_csv(OUT / "sensitivity_metrics.csv", index=False)
    coef = pd.DataFrame(coefs).pivot(index="feature", columns="variant", values="std_coef")
    coef.to_csv(OUT / "sensitivity_coefficients.csv")
    print(pd.DataFrame(rows).round(3).to_string())
    print(coef.round(3).to_string())


# --- 4. stress tests -----------------------------------------------------------------

def run_stress():
    _, data, _ = load_primary()
    rows = []
    for split in stress_splits(data.meta):
        for name, factory in [("o2_only_logreg", o2_only_logreg), ("logreg", logreg),
                              ("random_forest", random_forest), ("xgboost", xgboost)]:
            f, p = cross_validate(factory, data, [split], model_name=name)
            r = f.iloc[0]
            rows.append({"split": split.name, "model": name, "train_tests": len(split.train),
                         "test_tests": len(split.test), "test_sustained": int(r["n_sustained"]),
                         "roc_auc": r["roc_auc"], "pr_auc": r["pr_auc"], "brier": r["brier"],
                         "log_loss": r["log_loss"], "threshold": r["threshold"],
                         "recall@safe": r["recall@safe"], "precision@safe": r["precision@safe"],
                         "false_negative_rate@safe": r["false_negative_rate@safe"],
                         "mean_predicted": p["p_sustained"].mean(), "observed_rate": p["y_true"].mean()})
        print(f"  {split.name} done")
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "stress_metrics.csv", index=False)
    print(out.round(3).to_string())

    # Post-hoc diagnosis (led to D-001): the same splits for logistic regression without pressure.
    rows = []
    for split in stress_splits(data.meta):
        tr = data.X.iloc[split.train]
        for name, factory in [("logreg", logreg), ("logreg_no_pressure", lambda: logreg(feature_set="no_pressure"))]:
            f, p = cross_validate(factory, data, [split], model_name=name)
            r = f.iloc[0]
            rows.append({"split": split.name, "model": name, "train_pressure_sd": tr["pressure_atm"].std(),
                         "roc_auc": r["roc_auc"], "brier": r["brier"], "log_loss": r["log_loss"],
                         "recall@safe": r["recall@safe"], "precision@safe": r["precision@safe"],
                         "mean_predicted": p["p_sustained"].mean(), "observed_rate": p["y_true"].mean()})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "stress_no_pressure.csv", index=False)
    print(out.round(3).to_string())


def run_final():
    """Final candidates without pressure (D-001), then the pre-registered selection rule."""
    _, data, splits = load_primary()
    folds, preds = [], []
    for name, factory in FINAL_CANDIDATES.items():
        f, p = timed(name, lambda: cross_validate(factory, data, splits, model_name=name))
        folds.append(f)
        preds.append(p)
    final = pd.concat(folds, ignore_index=True)
    final.to_csv(OUT / "final_fold_metrics.csv", index=False)
    pd.concat(preds, ignore_index=True).to_csv(OUT / "final_oof_predictions.csv", index=False)
    print(final.groupby("model")["best_params"].value_counts().to_string())
    select_model(final, include_phase7=False, complexity=COMPLEXITY_FINAL, out_name="final_selection.csv")


SECTIONS = {"ablation": run_ablation, "sensitivity": run_sensitivity, "stress": run_stress, "tuning": run_tuning,
            "final": run_final}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=list(SECTIONS), help="run a single section")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in SECTIONS.items():
        if args.only and name != args.only:
            continue
        print(f"== {name}")
        fn()
    return 0


if __name__ == "__main__":
    sys.exit(main())
