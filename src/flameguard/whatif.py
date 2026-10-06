"""Phase 12: what-if analysis on the final model.

Every scenario here is HYPOTHETICAL: the user sets conditions, the model predicts.
Each step and curve point carries the applicability-domain verdict, so a path that
leaves the tested region is visible as such rather than presented as a clean number.

Caveat built into the interpretation: O2 and suppressant were varied together in
FLEX, so "change the suppressant at fixed O2" is usually outside the tested region,
and the model cannot isolate a separate suppressant effect (Phase 8 ablation).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from flameguard.prediction import FinalModel

INPUTS = ["fuel", "x_o2", "x_co2", "x_he", "d0_mm"]
STEP_ORDER = [("x_o2", "oxygen"), ("suppressant", "suppressant"), ("d0_mm", "droplet size"), ("fuel", "fuel")]


def _row(conditions: dict) -> pd.DataFrame:
    missing = set(INPUTS) - set(conditions)
    if missing:
        raise ValueError(f"Missing conditions: {sorted(missing)}")
    if conditions["x_co2"] > 0 and conditions["x_he"] > 0:
        raise ValueError("FLEX never combined CO2 and He; choose one suppressant")
    return pd.DataFrame([{k: conditions[k] for k in INPUTS}])


def predict_one(model: FinalModel, conditions: dict) -> pd.Series:
    return model.predict(_row(conditions)).iloc[0]


def scenario_path(model: FinalModel, baseline: dict, target: dict) -> pd.DataFrame:
    """Move from baseline to target one input at a time (oxygen, suppressant, droplet size, fuel).

    Returns one row per state: the baseline, then each changed input. Inputs that do not
    change are skipped. Because inputs interact (fuel x droplet size), the size of each
    step depends on the order; the order is fixed and stated so results are reproducible.
    """
    _row(baseline)  # validate both ends before touching the model
    _row(target)
    state = dict(baseline)
    rows = [{"step": "baseline", "change": "", **state}]
    for key, label in STEP_ORDER:
        if key == "suppressant":
            if (state["x_co2"], state["x_he"]) == (target["x_co2"], target["x_he"]):
                continue
            before = _supp_text(state)
            state["x_co2"], state["x_he"] = target["x_co2"], target["x_he"]
            rows.append({"step": label, "change": f"{before} → {_supp_text(state)}", **state})
        elif state[key] != target[key]:
            before = state[key]
            state[key] = target[key]
            rows.append({"step": label, "change": f"{_fmt(key, before)} → {_fmt(key, state[key])}", **state})
    frame = pd.DataFrame(rows)
    pred = model.predict(frame[INPUTS])
    out = pd.concat([frame.reset_index(drop=True), pred[["fire_risk", "risk_band", "supported_by_data",
                                                         "in_tested_range", "warnings"]].reset_index(drop=True)],
                    axis=1)
    out["delta"] = out["fire_risk"].diff().fillna(0.0)
    return out


def sweep(model: FinalModel, baseline: dict, feature: str, values: np.ndarray) -> pd.DataFrame:
    """Fire Risk as one numeric input varies, all others held at the baseline."""
    if feature not in {"x_o2", "x_co2", "x_he", "d0_mm"}:
        raise ValueError(f"Cannot sweep {feature!r}")
    frame = pd.DataFrame([{**baseline, feature: float(v)} for v in values])[INPUTS]
    pred = model.predict(frame)
    return pd.DataFrame({feature: frame[feature].to_numpy(), "fire_risk": pred["fire_risk"].to_numpy(),
                         "supported": pred["supported_by_data"].to_numpy() & pred["in_tested_range"].to_numpy()})


def _supp_text(state: dict) -> str:
    if state["x_co2"] > 0:
        return f"CO₂ {state['x_co2']:.2f}"
    if state["x_he"] > 0:
        return f"He {state['x_he']:.2f}"
    return "none"


def _fmt(key: str, value) -> str:
    if key == "x_o2":
        return f"O₂ {value:.2f}"
    if key == "d0_mm":
        return f"{value:.2f} mm"
    return str(value)
