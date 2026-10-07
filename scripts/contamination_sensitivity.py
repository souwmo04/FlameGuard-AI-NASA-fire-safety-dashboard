"""Phase 14 / decision D-002: does fuel-needle contamination change the model's conclusions?

NASA/TP-2015-216046 (§5.2, pp. 16-17) reports that a needle coating contaminated the droplets in all
2009-2011 FLEX tests and that methanol disruptions are "probably due to the presence of the
contaminant" (no conclusion for heptane). FlameGuard labels disruption as sustained burning, so this
script re-runs the final model's validation with those outcomes removed:

    primary                       252 tests (the deployed model's data)
    exclude_methanol_disruption   methanol disruptions removed
    exclude_disruption            all disruptions removed

Same model (L2 logistic regression, no pressure), same 5 x 5 grouped cross-validation as Phase 8/9.
Writes reports/phase14/:
    contamination_metrics.csv       per-variant mean/sd of cross-validated metrics (+ per fuel, pooled OOF)
    contamination_coefficients.csv  standardised coefficients fitted on each variant
    contamination_scenarios.csv     Fire Risk for reference scenarios under each variant
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from flameguard.dataset import build_modeling_data  # noqa: E402
from flameguard.evaluation import cross_validate, probability_metrics  # noqa: E402
from flameguard.model import FINAL_CANDIDATES  # noqa: E402
from flameguard.validation import repeated_group_kfold  # noqa: E402

OUT = ROOT / "reports" / "phase14"
VARIANTS = ["primary", "exclude_methanol_disruption", "exclude_disruption"]
N_SPLITS, N_REPEATS, SEED = 5, 5, 0
FACTORY = FINAL_CANDIDATES["logreg_np"]

# Reference scenarios: inputs as the model uses them (mole fractions, mm).
SCENARIOS = {
    "methanol, air, 3 mm": dict(fuel="Methanol", x_o2=0.21, x_co2=0.0, x_he=0.0, d0_mm=3.0),
    "methanol, 25% O2, 3 mm": dict(fuel="Methanol", x_o2=0.25, x_co2=0.0, x_he=0.0, d0_mm=3.0),
    "heptane, air, 3 mm": dict(fuel="Heptane", x_o2=0.21, x_co2=0.0, x_he=0.0, d0_mm=3.0),
    "heptane, 18% O2 + 15% CO2, 3 mm": dict(fuel="Heptane", x_o2=0.18, x_co2=0.15, x_he=0.0, d0_mm=3.0),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(ROOT / "data" / "processed" / "combustion_master.csv")
    rows, coefs, scen = [], [], []
    for variant in VARIANTS:
        data = build_modeling_data(master, variant)
        splits = repeated_group_kfold(data.y, data.groups, N_SPLITS, N_REPEATS, SEED)
        folds, preds = cross_validate(FACTORY, data, splits, model_name="logreg_np")
        row = {"variant": variant, "tests": len(data.y), "sustained": int(data.y.sum()),
               "methanol_sustained": int(data.y[data.X["fuel"] == "Methanol"].sum()),
               "heptane_sustained": int(data.y[data.X["fuel"] == "Heptane"].sum())}
        for m in ["roc_auc", "pr_auc", "brier", "log_loss", "recall@safe", "precision@safe"]:
            row[f"{m}_mean"] = folds[m].mean()
            row[f"{m}_sd"] = folds[m].std()
        # per-fuel metrics on pooled out-of-fold predictions (mean over repeats)
        fuel_of = dict(zip(data.meta["test_id"], data.X["fuel"]))
        preds["fuel"] = preds["test_id"].map(fuel_of)
        for fuel in ["Methanol", "Heptane"]:
            per = []
            for _, g in preds[preds["fuel"] == fuel].groupby("repeat"):
                if g["y_true"].nunique() == 2:
                    per.append(probability_metrics(g["y_true"].to_numpy(), g["p_sustained"].to_numpy()))
            if per:
                row[f"{fuel.lower()}_roc_auc"] = float(np.mean([m["roc_auc"] for m in per]))
                row[f"{fuel.lower()}_pr_auc"] = float(np.mean([m["pr_auc"] for m in per]))
        rows.append(row)

        fitted = FACTORY().fit(data.X, data.y)
        names = fitted.named_steps["pre"].get_feature_names_out()
        for n, c in zip(names, fitted.named_steps["model"].coef_[0]):
            coefs.append({"variant": variant, "feature": n, "std_coef": c})
        # pressure_atm is present in the input frame but not used by the no-pressure feature set
        X = pd.DataFrame(list(SCENARIOS.values())).assign(pressure_atm=1.0)[data.X.columns]
        for name, p in zip(SCENARIOS, fitted.predict_proba(X)[:, 1]):
            scen.append({"variant": variant, "scenario": name, "fire_risk": 100 * p})
        print(f"{variant}: {len(data.y)} tests, {int(data.y.sum())} sustained, "
              f"ROC-AUC {row['roc_auc_mean']:.3f}, PR-AUC {row['pr_auc_mean']:.3f}")

    pd.DataFrame(rows).to_csv(OUT / "contamination_metrics.csv", index=False)
    pd.DataFrame(coefs).pivot(index="feature", columns="variant", values="std_coef")[VARIANTS].to_csv(
        OUT / "contamination_coefficients.csv")
    pd.DataFrame(scen).pivot(index="scenario", columns="variant", values="fire_risk")[VARIANTS].to_csv(
        OUT / "contamination_scenarios.csv")
    print(pd.DataFrame(rows).round(3).T.to_string())
    print(pd.read_csv(OUT / "contamination_coefficients.csv").round(3).to_string())
    print(pd.read_csv(OUT / "contamination_scenarios.csv").round(1).to_string())


if __name__ == "__main__":
    main()
