"""Phase 7: cross-validated evaluation with safety-oriented metrics.

For every split:
  1. fit the pipeline on the training fold only;
  2. predict probabilities for the test fold;
  3. choose a decision threshold with an INNER grouped CV on the training fold
     (largest threshold whose inner out-of-fold recall on sustained >= target),
     then apply it unchanged to the test fold.

Metrics are reported two ways: per-fold mean +/- sd over all splits, and pooled
out-of-fold (each test predicted once per repeat), averaged over repeats.
"""

from __future__ import annotations

import json
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss, confusion_matrix,
                             f1_score, log_loss, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import Pipeline

from flameguard.dataset import ModelingData
from flameguard.validation import Split

TARGET_RECALL = 0.90
INNER_SPLITS = 4


# --- metrics -----------------------------------------------------------------

def threshold_metrics(y: np.ndarray, p: np.ndarray, threshold: float) -> dict:
    pred = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": accuracy_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred, zero_division=0),
        # missed fires: sustained tests predicted to self-extinguish
        "false_negative_rate": fn / (fn + tp) if (fn + tp) else np.nan,
        "false_positive_rate": fp / (fp + tn) if (fp + tn) else np.nan,
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def probability_metrics(y: np.ndarray, p: np.ndarray) -> dict:
    return {
        "roc_auc": roc_auc_score(y, p),
        "pr_auc": average_precision_score(y, p),
        "brier": brier_score_loss(y, p),
        "log_loss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1]),
    }


def choose_threshold(y: np.ndarray, p: np.ndarray, target_recall: float = TARGET_RECALL) -> float:
    """Largest threshold that still gives recall >= target on (y, p)."""
    for t in np.sort(np.unique(p))[::-1]:
        if recall_score(y, (p >= t).astype(int), zero_division=0) >= target_recall:
            return float(t)
    return float(np.min(p))


def fit_model(model, X: pd.DataFrame, y: pd.Series, groups: pd.Series):
    """Fit; grid searches also receive the training groups so their inner folds stay grouped."""
    if isinstance(model, GridSearchCV):
        return model.fit(X, y, groups=groups)
    return model.fit(X, y)


def inner_oof_probabilities(model: Pipeline, X: pd.DataFrame, y: pd.Series, groups: pd.Series,
                            seed: int) -> np.ndarray:
    """Out-of-fold probabilities on the training fold via grouped inner CV."""
    oof = np.full(len(y), np.nan)
    cv = StratifiedGroupKFold(n_splits=INNER_SPLITS, shuffle=True, random_state=seed)
    for tr, te in cv.split(X, y, groups):
        m = clone(model).fit(X.iloc[tr], y.iloc[tr])
        oof[te] = m.predict_proba(X.iloc[te])[:, 1]
    return oof


# --- cross-validation ----------------------------------------------------------

def cross_validate(model_factory: Callable[[], Pipeline], data: ModelingData, splits: list[Split],
                   model_name: str, target_recall: float = TARGET_RECALL,
                   select_threshold: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (per-split metrics, out-of-fold predictions)."""
    X, y, groups = data.X, data.y, data.groups
    fold_rows, pred_rows = [], []
    for i, s in enumerate(splits):
        model = model_factory()
        Xtr, ytr, gtr = X.iloc[s.train], y.iloc[s.train], groups.iloc[s.train]
        fitted = fit_model(clone(model), Xtr, ytr, gtr)
        p = fitted.predict_proba(X.iloc[s.test])[:, 1]
        yte = y.iloc[s.test].to_numpy()

        # For a grid search, the threshold is picked with the chosen hyperparameters held
        # fixed (re-running the whole search inside every inner fold would be costlier and
        # changes little); the outer test fold is still never used.
        best_params = None
        threshold_model = model
        if isinstance(fitted, GridSearchCV):
            best_params = fitted.best_params_
            threshold_model = clone(fitted.best_estimator_)

        threshold = np.nan
        if select_threshold:
            inner = inner_oof_probabilities(threshold_model, Xtr, ytr, gtr, seed=1000 + i)
            threshold = choose_threshold(ytr.to_numpy(), inner, target_recall)

        row = {"model": model_name, "split": s.name, "repeat": s.repeat, "fold": s.fold,
               "n_test": len(yte), "n_sustained": int(yte.sum()),
               "best_params": json.dumps(best_params, default=str) if best_params else ""}
        row |= probability_metrics(yte, p)
        row |= {f"{k}@0.5": v for k, v in threshold_metrics(yte, p, 0.5).items()}
        if select_threshold:
            row["threshold"] = threshold
            row |= {f"{k}@safe": v for k, v in threshold_metrics(yte, p, threshold).items()}
        fold_rows.append(row)

        pred_rows.append(pd.DataFrame({
            "model": model_name, "split": s.name, "repeat": s.repeat, "fold": s.fold,
            "row": s.test, "test_id": data.meta["test_id"].iloc[s.test].to_numpy(),
            "y_true": yte, "p_sustained": p, "threshold": threshold,
        }))
    return pd.DataFrame(fold_rows), pd.concat(pred_rows, ignore_index=True)


def pooled_metrics(preds: pd.DataFrame) -> pd.DataFrame:
    """Metrics on pooled out-of-fold predictions, one row per (model, repeat)."""
    rows = []
    for (model, repeat), g in preds.groupby(["model", "repeat"]):
        y, p = g["y_true"].to_numpy(), g["p_sustained"].to_numpy()
        row = {"model": model, "repeat": repeat} | probability_metrics(y, p)
        row |= {f"{k}@0.5": v for k, v in threshold_metrics(y, p, 0.5).items()}
        if g["threshold"].notna().all():
            pred = (p >= g["threshold"].to_numpy()).astype(int)
            row |= {f"{k}@safe": v for k, v in threshold_metrics(y, pred, 0.5).items()}
        rows.append(row)
    return pd.DataFrame(rows)


SUMMARY_METRICS = ["roc_auc", "pr_auc", "brier", "log_loss", "accuracy@0.5", "recall@0.5",
                   "precision@0.5", "f1@0.5", "false_negative_rate@0.5", "recall@safe", "precision@safe",
                   "f1@safe", "false_negative_rate@safe", "false_positive_rate@safe"]


def summarize(fold_metrics: pd.DataFrame, metrics: list[str] = SUMMARY_METRICS) -> pd.DataFrame:
    """Mean and sd of per-fold metrics per model, formatted 'mean ± sd'."""
    metrics = [m for m in metrics if m in fold_metrics.columns]
    agg = fold_metrics.groupby("model", sort=False)[metrics].agg(["mean", "std"])
    out = pd.DataFrame(index=agg.index)
    for m in metrics:
        out[m] = [f"{a:.3f} ± {b:.3f}" for a, b in zip(agg[(m, "mean")], agg[(m, "std")])]
    return out
