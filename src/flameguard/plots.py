"""Figures for model results (Phase 7+). Reuses the EDA style.

Colour = model identity in fixed order (logistic regression, random forest, XGBoost:
CVD-validated slots 1-3). Baselines are drawn in neutral grey as reference marks,
not as competing series.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, roc_curve

from flameguard.eda import AXIS, INK_2, MUTED, SURFACE

MODEL_ORDER = ["majority_baseline", "o2_only_logreg", "logreg", "random_forest", "xgboost"]
MODEL_LABELS = {
    "majority_baseline": "Majority baseline",
    "o2_only_logreg": "O₂-only logistic",
    "logreg": "Logistic regression",
    "random_forest": "Random forest",
    "xgboost": "XGBoost",
}
MODEL_COLORS = {
    "majority_baseline": "#c3c2b7",
    "o2_only_logreg": "#898781",
    "logreg": "#2a78d6",
    "random_forest": "#eb6834",
    "xgboost": "#1baf7a",
}


def plot_fold_metric(fold_metrics: pd.DataFrame, metric: str, label: str) -> plt.Figure:
    """One dot per CV split (jittered) and the mean bar, per model."""
    models = [m for m in MODEL_ORDER if m in set(fold_metrics["model"])]
    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    for i, m in enumerate(models):
        vals = fold_metrics.loc[fold_metrics["model"] == m, metric].to_numpy()
        ax.scatter(rng.uniform(-0.18, 0.18, len(vals)) + i, vals, s=26, color=MODEL_COLORS[m],
                   edgecolors=SURFACE, linewidths=0.8, alpha=0.85, zorder=2)
        mean = vals.mean()
        ax.plot([i - 0.3, i + 0.3], [mean, mean], color=INK_2, linewidth=2, zorder=3)
        ax.text(i + 0.33, mean, f"{mean:.3f}", va="center", fontsize=9, color=INK_2)
    ax.set_xticks(range(len(models)), [MODEL_LABELS[m] for m in models])
    ax.set_ylabel(label)
    ax.grid(axis="x", visible=False)
    ax.set_title(f"{label} on each of {fold_metrics['split'].nunique()} grouped CV test folds (bar = mean)")
    fig.tight_layout()
    return fig


def plot_curves(oof: pd.DataFrame, repeat: int = 0) -> plt.Figure:
    """Pooled out-of-fold ROC and precision-recall curves for one CV repeat."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    sub = oof[oof["repeat"] == repeat]
    base_rate = sub.groupby("model")["y_true"].mean().iloc[0]
    for m in [x for x in MODEL_ORDER if x != "majority_baseline" and x in set(sub["model"])]:
        g = sub[sub["model"] == m]
        y, p = g["y_true"].to_numpy(), g["p_sustained"].to_numpy()
        style = {"color": MODEL_COLORS[m], "linewidth": 2, "label": MODEL_LABELS[m]}
        if m == "o2_only_logreg":
            style |= {"linestyle": (0, (4, 2)), "linewidth": 1.6}
        fpr, tpr, _ = roc_curve(y, p)
        axes[0].plot(fpr, tpr, **style)
        prec, rec, _ = precision_recall_curve(y, p)
        axes[1].plot(rec, prec, **style)
    axes[0].plot([0, 1], [0, 1], color=AXIS, linewidth=1, linestyle=":")
    axes[0].set(xlabel="False positive rate (extinguished tests flagged)", ylabel="Recall on sustained",
                title="ROC curve")
    axes[1].axhline(base_rate, color=AXIS, linewidth=1, linestyle=":")
    axes[1].text(0.01, base_rate + 0.02, f"no-skill = {base_rate:.2f}", fontsize=8.5, color=MUTED)
    axes[1].set(xlabel="Recall on sustained", ylabel="Precision", title="Precision–recall curve",
                ylim=(0, 1.02))
    axes[1].axvline(0.9, color=MUTED, linewidth=1, linestyle=(0, (2, 2)))
    axes[1].text(0.895, 0.04, "recall target 0.90", rotation=90, ha="right", fontsize=8.5, color=MUTED)
    axes[0].legend(loc="lower right", fontsize=9)
    fig.suptitle(f"Pooled out-of-fold predictions (CV repeat {repeat}, grouped by atmosphere)",
                 x=0.01, ha="left", fontsize=12, fontweight="semibold")
    fig.tight_layout()
    return fig


def plot_leakage(leak: pd.DataFrame, metric: str = "roc_auc", label: str = "ROC-AUC") -> plt.Figure:
    """Dumbbell: grouped (honest) vs row-level (leaky) CV for the same models."""
    d = leak[leak["metric"] == metric].set_index("model")
    models = [m for m in MODEL_ORDER if m in d.index]
    fig, ax = plt.subplots(figsize=(9, 3.4))
    for i, m in enumerate(models):
        g, u = d.loc[m, "grouped_mean"], d.loc[m, "ungrouped_mean"]
        ax.plot([g, u], [i, i], color=AXIS, linewidth=2, zorder=1)
        ax.scatter([g], [i], s=70, color=MODEL_COLORS[m], edgecolors=SURFACE, linewidths=1.2, zorder=3)
        ax.scatter([u], [i], s=70, facecolors=SURFACE, edgecolors=MODEL_COLORS[m], linewidths=1.8, zorder=3)
        ax.text(max(g, u) + 0.004, i, f"+{u - g:.3f}", va="center", fontsize=9, color=INK_2)
    ax.set_yticks(range(len(models)), [MODEL_LABELS[m] for m in models])
    ax.invert_yaxis()
    ax.set_xlabel(f"Mean {label} over 25 test folds")
    ax.grid(axis="y", visible=False)
    ax.set_title(f"{label}: grouped CV (filled) vs row-level CV ignoring atmospheres (hollow)")
    fig.tight_layout()
    return fig


def plot_ablation(paired: pd.DataFrame, metric: str = "roc_auc", label: str = "ROC-AUC") -> plt.Figure:
    """Paired change vs the full logistic model per ablation: mean ± sd over 25 folds."""
    d = paired[paired["metric"] == metric].copy()
    sign = -1 if metric == "log_loss" else 1
    d["gain"] = sign * d["mean_delta_vs_full"]
    d = d.sort_values("gain")
    fig, ax = plt.subplots(figsize=(11, 3.9))
    y = np.arange(len(d))
    hurts = d["gain"] < 0
    colors = np.where(hurts, MODEL_COLORS["logreg"], MUTED)
    ax.errorbar(d["gain"], y, xerr=d["sd"], fmt="none", ecolor=AXIS, elinewidth=1.4, zorder=1)
    ax.scatter(d["gain"], y, s=64, c=colors, edgecolors=SURFACE, linewidths=1.2, zorder=2)
    for yi, (_, r) in zip(y, d.iterrows()):
        ax.text(1.01, yi, f"better in {r['variant_better_folds']}/{r['folds']} folds", transform=ax.get_yaxis_transform(),
                ha="left", va="center", fontsize=8.5, color=INK_2)
    ax.axvline(0, color=INK_2, linewidth=1)
    ax.set_yticks(y, d["variant"])
    ax.set_xlabel(f"Change in {label} vs full model ({'lower log loss' if sign < 0 else 'higher'} = better), mean ± sd")
    ax.grid(axis="y", visible=False)
    ax.set_title(f"Feature ablation, logistic regression (25 grouped folds): what each input contributes")
    fig.tight_layout()
    return fig


def plot_stress(stress: pd.DataFrame, reference: dict[str, float], metric: str = "roc_auc",
                label: str = "ROC-AUC") -> plt.Figure:
    """Stress-split metric per model, with the in-distribution grouped-CV mean as a reference tick."""
    models = [m for m in MODEL_ORDER if m in set(stress["model"])]
    splits = list(dict.fromkeys(stress["split"]))
    fig, ax = plt.subplots(figsize=(11, 3.9))
    width = 0.8 / len(models)
    for k, m in enumerate(models):
        vals = [stress[(stress["split"] == s) & (stress["model"] == m)][metric].iloc[0] for s in splits]
        x = np.arange(len(splits)) + (k - (len(models) - 1) / 2) * width
        ax.scatter(x, vals, s=70, color=MODEL_COLORS[m], edgecolors=SURFACE, linewidths=1.2, label=MODEL_LABELS[m],
                   zorder=3)
        for xi, v in zip(x, vals):
            ax.text(xi, v + 0.015, f"{v:.2f}", ha="center", fontsize=7.5, color=INK_2)
    ax.set_xticks(range(len(splits)), [s.replace("_", " ") for s in splits])
    ax.set_ylim(0.5, 1.0)  # dots, not bars, so a non-zero baseline does not distort
    ax.set_ylabel(label)
    ref_txt = ", ".join(f"{MODEL_LABELS[m]} {v:.2f}" for m, v in reference.items())
    ax.set_title(f"{label} on held-out conditions (in-distribution grouped CV: {ref_txt})", fontsize=10)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1), fontsize=9)
    fig.tight_layout()
    return fig
