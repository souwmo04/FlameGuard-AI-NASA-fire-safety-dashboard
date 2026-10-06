"""Phase 7: train and evaluate baseline models with grouped cross-validation.

Writes to reports/phase7/:
  fold_metrics.csv      one row per model x split (25 grouped splits)
  oof_predictions.csv   out-of-fold P(sustained) for every test, model and repeat
  pooled_metrics.csv    metrics on pooled out-of-fold predictions per repeat
  summary.csv           mean ± sd over the 25 splits
  leakage_check.csv     grouped vs ungrouped (row-level) CV, same models
  run_info.json         data size, splits, library versions

Usage (from the project root):
    .venv/Scripts/python scripts/train_baselines.py
"""

from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import sklearn  # noqa: E402
import xgboost  # noqa: E402
from sklearn.model_selection import StratifiedKFold  # noqa: E402

from flameguard.dataset import build_modeling_data  # noqa: E402
from flameguard.evaluation import cross_validate, pooled_metrics, summarize  # noqa: E402
from flameguard.model import MODELS  # noqa: E402
from flameguard.validation import Split, repeated_group_kfold  # noqa: E402

OUT = ROOT / "reports" / "phase7"
N_SPLITS, N_REPEATS, SEED = 5, 5, 0


def ungrouped_splits(y: pd.Series) -> list[Split]:
    """Row-level stratified CV that IGNORES atmosphere groups (for the leakage comparison only)."""
    splits = []
    for r in range(N_REPEATS):
        cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED + r)
        for k, (tr, te) in enumerate(cv.split(np.zeros(len(y)), y)):
            splits.append(Split(name=f"r{r}f{k}", train=tr, test=te, repeat=r, fold=k))
    return splits


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(ROOT / "data" / "processed" / "combustion_master.csv")
    data = build_modeling_data(master, "primary")
    splits = repeated_group_kfold(data.y, data.groups, n_splits=N_SPLITS, n_repeats=N_REPEATS, seed=SEED)
    print(data.summary())

    folds, preds = [], []
    for name, factory in MODELS.items():
        t0 = time.time()
        f, p = cross_validate(factory, data, splits, model_name=name)
        folds.append(f)
        preds.append(p)
        print(f"  {name:18s} ROC-AUC {f['roc_auc'].mean():.3f} ± {f['roc_auc'].std():.3f}  ({time.time() - t0:.0f}s)")
    fold_metrics = pd.concat(folds, ignore_index=True)
    oof = pd.concat(preds, ignore_index=True)

    fold_metrics.to_csv(OUT / "fold_metrics.csv", index=False)
    oof.to_csv(OUT / "oof_predictions.csv", index=False)
    pooled_metrics(oof).to_csv(OUT / "pooled_metrics.csv", index=False)
    summarize(fold_metrics).to_csv(OUT / "summary.csv")

    # Leakage check: identical models, but splits that ignore the atmosphere groups.
    leak_rows = []
    row_splits = ungrouped_splits(data.y)
    for name in ["o2_only_logreg", "logreg", "random_forest", "xgboost"]:
        f_row, _ = cross_validate(MODELS[name], data, row_splits, model_name=name, select_threshold=False)
        f_grp = fold_metrics[fold_metrics["model"] == name]
        for metric in ["roc_auc", "pr_auc", "brier"]:
            leak_rows.append({"model": name, "metric": metric,
                              "grouped_mean": f_grp[metric].mean(), "grouped_sd": f_grp[metric].std(),
                              "ungrouped_mean": f_row[metric].mean(), "ungrouped_sd": f_row[metric].std()})
    leak = pd.DataFrame(leak_rows)
    leak["ungrouped_minus_grouped"] = leak["ungrouped_mean"] - leak["grouped_mean"]
    leak.to_csv(OUT / "leakage_check.csv", index=False)

    info = {
        "data": data.summary(),
        "cv": {"scheme": "StratifiedGroupKFold", "group": data.groups.name, "n_splits": N_SPLITS,
               "n_repeats": N_REPEATS, "seed": SEED},
        "threshold_rule": "largest threshold with inner grouped-CV recall >= 0.90 on the training fold",
        "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                     "xgboost": xgboost.__version__, "pandas": pd.__version__, "numpy": np.__version__},
    }
    (OUT / "run_info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print(summarize(fold_metrics).to_string())
    print(leak.round(3).to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
