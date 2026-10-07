"""Phase 10: SHAP explanations of the final model in Fire Risk points.

Explanations are computed on the RAW inputs a user sets (fuel, O2, CO2, He, droplet
diameter), not on the engineered features, so the fuel x diameter term is shared
fairly between fuel and diameter instead of appearing as an abstract extra feature.

Values are exact interventional Shapley values: with at most five players all
2^5 coalitions are enumerated, so there is no sampling error. For a test x,
    phi_j = contribution of input j, in Fire Risk points (0-100 scale)
    base  = mean Fire Risk over the background (the 252 training tests)
    base + sum(phi) = Fire Risk of x   (exact additivity)

Fuel first (asymmetric Shapley values, Frye, Rowat & Feige, NeurIPS 2020)
-------------------------------------------------------------------------
The model's droplet-size effect has opposite signs for the two fuels. Standard
(symmetric) SHAP splits that interaction evenly, so for a METHANOL test the
droplet-size contribution is partly evaluated with HEPTANE as the fuel and
inherits heptane's downward slope - the opposite of what the model does for
methanol. Treating fuel as the context that is set first fixes this: fuel gets
v({fuel}) - v({}), and the remaining players are Shapley values of the game in
which the test's own fuel is always present.

Groupings
---------
grouped            (primary) fuel first, then atmosphere = {O2, CO2, He} and droplet size.
                   O2 and suppressant were varied together in FLEX; one atmosphere player
                   keeps every evaluated atmosphere a tested one.
detailed           fuel first, then O2, CO2, He, droplet size separately. The O2 vs
                   suppressant split is not individually reliable.
detailed_symmetric standard SHAP over all five inputs (validation against the shap
                   library and comparison; not shown to users).

These values explain the MODEL. They are associations learned from FLEX data, not
measured causal effects of changing a condition.
"""

from __future__ import annotations

import math

from itertools import combinations
from math import factorial

import numpy as np
import pandas as pd

from flameguard.prediction import FinalModel

RAW_COLUMNS = ["is_heptane", "x_o2", "x_co2", "x_he", "d0_mm"]
FUEL_FIRST = "fuel"
GROUPINGS = {
    "grouped": {"fuel": ["is_heptane"],
                "atmosphere (O₂ + CO₂ + He)": ["x_o2", "x_co2", "x_he"],
                "droplet size": ["d0_mm"]},
    "detailed": {"fuel": ["is_heptane"], "O₂": ["x_o2"], "CO₂": ["x_co2"], "He": ["x_he"],
                 "droplet size": ["d0_mm"]},
    "detailed_symmetric": {"fuel": ["is_heptane"], "O₂": ["x_o2"], "CO₂": ["x_co2"], "He": ["x_he"],
                           "droplet size": ["d0_mm"]},
}
ASYMMETRIC = {"grouped": True, "detailed": True, "detailed_symmetric": False}


def to_raw(inputs: pd.DataFrame) -> pd.DataFrame:
    """Model inputs (fuel as text) -> numeric raw frame in RAW_COLUMNS order."""
    raw = pd.DataFrame({"is_heptane": (inputs["fuel"] == "Heptane").astype(float)}, index=inputs.index)
    for c in RAW_COLUMNS[1:]:
        raw[c] = inputs[c].astype(float)
    return raw


def risk_function(model: FinalModel):
    """f(Z) -> Fire Risk (0-100) for a numeric array with RAW_COLUMNS."""
    def f(Z: np.ndarray) -> np.ndarray:
        Z = np.asarray(Z, dtype=float)
        frame = pd.DataFrame(Z, columns=RAW_COLUMNS)
        frame.insert(0, "fuel", np.where(frame.pop("is_heptane") >= 0.5, "Heptane", "Methanol"))
        frame["pressure_atm"] = np.nan  # not a model input (D-001)
        return 100.0 * model.pipeline.predict_proba(frame)[:, 1]
    return f


def exact_shapley(f, x: np.ndarray, background: np.ndarray, players: list[list[int]],
                  first: int | None = None) -> tuple[np.ndarray, float]:
    """Exact interventional Shapley values of f at x for groups of columns ("players").

    v(S) = mean_b f(z) where z takes x's values for players in S and b's values otherwise.
    If `first` is a player index, that player is ordered first (asymmetric Shapley):
    phi_first = v({first}) - v({}), and the others are Shapley values of S -> v(S + {first}).
    Returns (phi per player, base value v(empty set)).
    """
    k = len(players)
    n_bg = len(background)
    subsets = [s for r in range(k + 1) for s in combinations(range(k), r)]
    # Evaluate every coalition in one batched model call.
    batch = np.repeat(background[None, :, :], len(subsets), axis=0).copy()
    for i, s in enumerate(subsets):
        for p in s:
            batch[i, :, players[p]] = x[players[p]][:, None]
    values = f(batch.reshape(-1, background.shape[1])).reshape(len(subsets), n_bg).mean(axis=1)
    v = dict(zip(subsets, values))
    phi = np.zeros(k)
    if first is None:
        for j in range(k):
            for s in subsets:
                if j in s:
                    continue
                weight = factorial(len(s)) * factorial(k - len(s) - 1) / factorial(k)
                phi[j] += weight * (v[tuple(sorted(s + (j,)))] - v[s])
        return phi, float(v[()])

    phi[first] = v[(first,)] - v[()]
    rest = [j for j in range(k) if j != first]
    m = len(rest)
    for j in rest:
        others = [r for r in rest if r != j]
        for size in range(m):
            for s in combinations(others, size):
                weight = factorial(size) * factorial(m - size - 1) / factorial(m)
                with_j = tuple(sorted(s + (j, first)))
                without = tuple(sorted(s + (first,)))
                phi[j] += weight * (v[with_j] - v[without])
    return phi, float(v[()])


def explain(model: FinalModel, inputs: pd.DataFrame, background: pd.DataFrame,
            grouping: str = "grouped") -> pd.DataFrame:
    """One row per input row: base, fire_risk, and one column per player (Fire Risk points)."""
    groups = GROUPINGS[grouping]
    players = [[RAW_COLUMNS.index(c) for c in cols] for cols in groups.values()]
    first = list(groups).index(FUEL_FIRST) if ASYMMETRIC[grouping] else None
    f = risk_function(model)
    bg = to_raw(background).to_numpy()
    rows = []
    for x in to_raw(inputs).to_numpy():
        phi, base = exact_shapley(f, x, bg, players, first=first)
        rows.append({"base": base, "fire_risk": float(f(x[None, :])[0]), **dict(zip(groups, phi))})
    return pd.DataFrame(rows, index=inputs.index)


def global_importance(contrib: pd.DataFrame) -> pd.DataFrame:
    """Mean |contribution| per player over many explained tests (Fire Risk points)."""
    players = [c for c in contrib.columns if c not in {"base", "fire_risk"}]
    imp = contrib[players].abs().mean().sort_values(ascending=False)
    return pd.DataFrame({"mean_abs_points": imp, "share": imp / imp.sum()})


def format_risk(risk: float) -> str:
    """Whole-number Fire Risk without implying certainty at the extremes."""
    if risk > 99.5:
        return "> 99"
    if risk < 0.5:
        return "< 1"
    return str(math.floor(risk + 0.5))  # round halves up, like the frontend's Math.round (not banker's rounding)


def describe(row: pd.Series, band: str, inputs: pd.Series | None = None) -> str:
    """Deterministic plain-language summary of one grouped explanation (no LLM involved)."""
    players = [c for c in row.index if c not in {"base", "fire_risk"}]
    ordered = sorted(players, key=lambda p: -abs(row[p]))
    parts = []
    for p in ordered:
        v = row[p]
        if abs(v) < 1:
            continue
        direction = "raises" if v > 0 else "lowers"
        parts.append(f"{p} {direction} it by {abs(v):.0f} points")
    if not parts:
        parts.append("no input moves it by more than one point")
    fuel_note = ""
    if inputs is not None and "fuel" in inputs:
        fuel_note = f" for a {inputs['fuel'].lower()} droplet"
    return (f"Model prediction{fuel_note}: Fire Risk {format_risk(row['fire_risk'])}/100 ({band}). "
            f"Compared with the average FLEX test ({row['base']:.0f}/100), " + "; ".join(parts) + ". "
            "These contributions describe how the model uses the inputs; they are associations learned from "
            "NASA FLEX experiments, not measured effects of changing a condition.")
