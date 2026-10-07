"""Exploratory-analysis helpers: summary tables and figures for the FLEX master table.

All figures describe OBSERVED NASA results only; nothing here is a model output.

Colour encodes the diluent everywhere (N2 / CO2 / He, fixed order, CVD-validated
for all-pairs use). Outcome is encoded by marker fill and shape, never by colour,
so the same colour always means the same atmosphere across figures.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from sklearn.metrics import roc_auc_score

from flameguard.data_loader import PROJECT_ROOT

from flameguard.stats import wilson_interval  # noqa: F401  (re-exported for notebooks)

MASTER_PATH = PROJECT_ROOT / "data" / "processed" / "combustion_master.csv"
FIGURE_DIR = PROJECT_ROOT / "docs" / "figures"

DILUENTS = ["N2", "CO2", "He"]
DILUENT_COLORS = {"N2": "#2a78d6", "CO2": "#eb6834", "He": "#1baf7a"}
DILUENT_LABELS = {"N2": "N₂ only (no added suppressant)", "CO2": "CO₂ added", "He": "He added"}
FUELS = ["Methanol", "Heptane"]

INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"


def use_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": ["Segoe UI", "DejaVu Sans", "sans-serif"],
        "font.size": 10,
        "text.color": INK,
        "axes.labelcolor": INK_2,
        "axes.titlesize": 11,
        "axes.titleweight": "semibold",
        "axes.titlecolor": INK,
        "axes.titlelocation": "left",
        "axes.edgecolor": AXIS,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2,
        "legend.frameon": False,
        "figure.dpi": 110,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
    })


def load_master(path: Path | str = MASTER_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["qc_flags"] = df["qc_flags"].fillna("")  # empty string = no flags, not missing data
    df["test_date"] = pd.to_datetime(df["test_datetime_gmt"].str[:10])
    return df


def save(fig: plt.Figure, name: str) -> Path:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURE_DIR / f"{name}.png"
    fig.savefig(path)
    return path


# --- tables ------------------------------------------------------------------

def rate_table(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Observed sustained-combustion rate with n and 95% Wilson interval per group."""
    g = df.groupby(by, observed=True)["y_sustained"].agg(n="size", sustained="sum").reset_index()
    ci = [wilson_interval(s, n) for s, n in zip(g["sustained"], g["n"])]
    g["rate"] = g["sustained"] / g["n"]
    g["ci_low"] = [c[0] for c in ci]
    g["ci_high"] = [c[1] for c in ci]
    return g


def size_quartiles(df: pd.DataFrame, by: str = "fuel") -> pd.Series:
    """Initial-droplet-diameter quartile within each `by` group, labelled with its mm range."""
    def label(s: pd.Series) -> pd.Series:
        q = pd.qcut(s, 4)
        names = [f"Q{i + 1}: {iv.left:.1f}–{iv.right:.1f} mm" for i, iv in enumerate(q.cat.categories)]
        return q.cat.rename_categories(names).astype(object)
    return df.groupby(by, group_keys=False)["d0_mm"].apply(label)


def missingness_table(df: pd.DataFrame) -> pd.DataFrame:
    miss = df.isna().sum()
    miss = miss[miss > 0]
    return pd.DataFrame({"missing": miss, "share": (miss / len(df)).round(3)}).sort_values("missing", ascending=False)


def univariate_auc(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Direction-free ROC-AUC of each single variable for y_sustained (0.5 = no signal).

    Descriptive only: computed on all rows, no validation split. It ranks how much
    each variable separates the outcomes on its own, not model performance.
    """
    rows = []
    for col in columns:
        ok = df[col].notna()
        auc = roc_auc_score(df.loc[ok, "y_sustained"], df.loc[ok, col])
        rows.append({"variable": col, "auc": round(max(auc, 1 - auc), 3),
                     "direction": "higher -> more sustained" if auc >= 0.5 else "higher -> more extinction",
                     "n": int(ok.sum())})
    return pd.DataFrame(rows).sort_values("auc", ascending=False).reset_index(drop=True)


def group_purity_table(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    for col in group_cols:
        s = df.groupby(col)["y_sustained"].agg(["mean", "size"])
        pure = (s["mean"] == 0) | (s["mean"] == 1)
        rows.append({"grouping": col, "groups": len(s), "median_size": int(s["size"].median()),
                     "largest": int(s["size"].max()), "largest_share": round(s["size"].max() / len(df), 3),
                     "single_outcome_groups": f"{pure.mean():.0%}"})
    return pd.DataFrame(rows)


# --- figures -----------------------------------------------------------------

def _outcome_legend(ax, **kwargs) -> None:
    handles = [
        Line2D([], [], marker="^", linestyle="", markersize=8, color=INK_2, label="Sustained (completion / disruption)"),
        Line2D([], [], marker="o", linestyle="", markersize=7, markerfacecolor="none",
               markeredgecolor=INK_2, markeredgewidth=1.4, label="Extinguished"),
    ]
    ax.legend(handles=handles, **kwargs)


def plot_flammability_map(df: pd.DataFrame) -> plt.Figure:
    """O2 vs initial droplet size, faceted fuel x diluent; filled triangles = sustained."""
    fig, axes = plt.subplots(2, 3, figsize=(12, 7), sharex=True, sharey=True)
    for i, fuel in enumerate(FUELS):
        for j, dil in enumerate(DILUENTS):
            ax = axes[i, j]
            sub = df[(df["fuel"] == fuel) & (df["diluent"] == dil)]
            color = DILUENT_COLORS[dil]
            ext = sub[sub["y_sustained"] == 0]
            sus = sub[sub["y_sustained"] == 1]
            ax.scatter(ext["d0_mm"], ext["x_o2"], s=42, marker="o", facecolors="none",
                       edgecolors=color, linewidths=1.4, zorder=2)
            ax.scatter(sus["d0_mm"], sus["x_o2"], s=60, marker="^", color=color,
                       edgecolors=SURFACE, linewidths=1.0, zorder=3)
            n_missing = sub["d0_mm"].isna().sum()
            note = f"n = {len(sub)}  ({int(sus.shape[0])} sustained)"
            if n_missing:
                note += f", {n_missing} without d₀"
            ax.set_title(f"{fuel} · {DILUENT_LABELS[dil]}\n", fontsize=10)
            ax.text(0, 1.02, note, transform=ax.transAxes, va="bottom", fontsize=8.5, color=INK_2)
            if i == 1:
                ax.set_xlabel("Initial droplet diameter d₀ (mm)")
            if j == 0:
                ax.set_ylabel("O₂ mole fraction")
    fig.suptitle("Observed FLEX outcomes by oxygen level and droplet size", x=0.01, ha="left",
                 fontsize=13, fontweight="semibold", y=1.0)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    _outcome_legend(fig, loc="upper left", bbox_to_anchor=(0.005, 0.965), ncol=2, fontsize=9)
    return fig


def plot_rate_vs_o2(df: pd.DataFrame, bins: list[float]) -> tuple[plt.Figure, pd.DataFrame]:
    """Observed sustained rate per O2 bin, one line per diluent, faceted by fuel, 95% Wilson bars."""
    d = df.assign(o2_bin=pd.cut(df["x_o2"], bins))
    table = rate_table(d, ["fuel", "diluent", "o2_bin"])
    table["o2_mid"] = table["o2_bin"].apply(lambda b: b.mid).astype(float)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    offsets = {"N2": -0.0025, "CO2": 0.0, "He": 0.0025}
    for ax, fuel in zip(axes, FUELS):
        for dil in DILUENTS:
            t = table[(table["fuel"] == fuel) & (table["diluent"] == dil)].sort_values("o2_mid")
            if t.empty:
                continue
            x = t["o2_mid"] + offsets[dil]
            ax.errorbar(x, t["rate"], yerr=[t["rate"] - t["ci_low"], t["ci_high"] - t["rate"]],
                        color=DILUENT_COLORS[dil], linewidth=2, marker="o", markersize=7,
                        markeredgecolor=SURFACE, markeredgewidth=1.2, elinewidth=1, capsize=0,
                        label=DILUENT_LABELS[dil], alpha=0.95)
        ax.set_title(fuel)
        ax.set_xlabel("O₂ mole fraction (bin midpoint)")
        ax.set_ylim(-0.03, 1.03)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    axes[0].set_ylabel("Observed share of tests sustained")
    for ax in axes:
        ax.legend(loc="upper left", fontsize=9)
    fig.suptitle("Observed share of sustained tests by oxygen level (bars: 95% Wilson interval)",
                 x=0.01, ha="left", fontsize=13, fontweight="semibold", y=1.02)
    fig.tight_layout()
    return fig, table


def plot_design_space(df: pd.DataFrame) -> plt.Figure:
    """Which O2 / suppressant / pressure combinations were actually tested."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4))
    ax = axes[0]
    for dil in DILUENTS:
        sub = df[df["diluent"] == dil].assign(added=lambda d: d["x_co2"] + d["x_he"])
        pts = sub.groupby(["x_o2", "added"]).size().reset_index(name="n")
        ax.scatter(pts["x_o2"], pts["added"], s=18 + 14 * pts["n"], color=DILUENT_COLORS[dil],
                   edgecolors=SURFACE, linewidths=1.2, label=DILUENT_LABELS[dil], alpha=0.9)
    ax.set_xlabel("O₂ mole fraction")
    ax.set_ylabel("Added suppressant mole fraction (CO₂ or He)")
    ax.set_title("Tested atmospheres (dot area = number of tests)")
    ax.legend(handles=[Line2D([], [], marker="o", linestyle="", markersize=8, color=DILUENT_COLORS[d],
                              label=DILUENT_LABELS[d]) for d in DILUENTS], loc="upper right", fontsize=9)

    ax = axes[1]
    levels = ["0.7atm", "1atm", "2-3atm"]
    counts = df.groupby(["pressure_level", "diluent"]).size().unstack(fill_value=0).reindex(levels).fillna(0)
    x = np.arange(len(levels))
    width = 0.26
    for k, dil in enumerate(DILUENTS):
        vals = counts.get(dil, pd.Series(0, index=levels)).to_numpy()
        bars = ax.bar(x + (k - 1) * width, vals, width - 0.02, color=DILUENT_COLORS[dil],
                      label=DILUENT_LABELS[dil])
        for b, v in zip(bars, vals):
            if v:
                ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{int(v)}", ha="center", fontsize=8.5, color=INK_2)
    ax.set_xticks(x, ["~0.7 atm", "~1 atm", "2–3 atm"])
    ax.set_ylabel("Tests")
    ax.set_title("Tests per pressure level")
    ax.grid(axis="x", visible=False)
    fig.suptitle("The test matrix: where the data does (and does not) cover",
                 x=0.01, ha="left", fontsize=13, fontweight="semibold", y=1.03)
    fig.tight_layout()
    return fig


def plot_campaign_timeline(df: pd.DataFrame) -> plt.Figure:
    """Test sequence: O2 per test over time, coloured by diluent, outcome by marker."""
    fig, ax = plt.subplots(figsize=(12, 4.2))
    for dil in DILUENTS:
        sub = df[df["diluent"] == dil]
        ext, sus = sub[sub["y_sustained"] == 0], sub[sub["y_sustained"] == 1]
        ax.scatter(ext["test_date"], ext["x_o2"], s=34, marker="o", facecolors="none",
                   edgecolors=DILUENT_COLORS[dil], linewidths=1.2)
        ax.scatter(sus["test_date"], sus["x_o2"], s=50, marker="^", color=DILUENT_COLORS[dil],
                   edgecolors=SURFACE, linewidths=0.8)
    ax.set_ylabel("O₂ mole fraction")
    ax.set_title("FLEX test campaign, March 2009 – December 2011", loc="left")
    dil_handles = [Line2D([], [], marker="s", linestyle="", markersize=9, color=DILUENT_COLORS[d],
                          label=DILUENT_LABELS[d]) for d in DILUENTS]
    leg = ax.legend(handles=dil_handles, loc="upper left", bbox_to_anchor=(0, -0.12), ncol=3, fontsize=9)
    ax.add_artist(leg)
    _outcome_legend(ax, loc="upper right", bbox_to_anchor=(1, -0.12), ncol=2, fontsize=9)
    fig.tight_layout()
    return fig


def plot_group_sizes(df: pd.DataFrame, group_col: str) -> plt.Figure:
    """Tests per validation group, split by outcome (stacked, largest groups first)."""
    s = df.groupby(group_col)["y_sustained"].agg(sustained="sum", n="size")
    s["extinguished"] = s["n"] - s["sustained"]
    s = s.sort_values("n", ascending=False)
    fig, ax = plt.subplots(figsize=(12, 3.8))
    x = np.arange(len(s))
    ax.bar(x, s["extinguished"], 0.8, color="#86b6ef", edgecolor=SURFACE, linewidth=1, label="Extinguished")
    ax.bar(x, s["sustained"], 0.8, bottom=s["extinguished"], color="#184f95", edgecolor=SURFACE,
           linewidth=1, label="Sustained")
    ax.set_xticks([])
    ax.set_xlabel(f"{len(s)} groups ({group_col}), largest first")
    ax.set_ylabel("Tests")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title(f"Validation groups: size and outcome mix ({group_col})")
    fig.tight_layout()
    return fig
