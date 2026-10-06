"""Observed FLEX experiments, each paired (where in scope) with its out-of-fold model prediction."""

from __future__ import annotations

import math

import pandas as pd

from flameguard.schema import QC_FLAGS

from app.schemas.common import RiskLevel
from app.schemas.responses import ExperimentDetail, ExperimentList, ExperimentSummary, OutOfFoldPrediction
from app.services.sources import source_ref
from app.state import AppState

SUPPRESSANT = {"N2": "none", "CO2": "CO2", "He": "He"}
EXCLUSION_TEXT = {
    "out_of_scope_pressure_2-3atm": "Tested at 2-3 atm, outside the model's 0.7-1 atm scope (a single CO2 series).",
    "missing_d0": "NASA did not report the initial droplet diameter, a required model input.",
    "missing_pressure": "The recorded pressure is invalid (0.0 mmHg), so the test was not used for training.",
}


def num(value, digits: int | None = None) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)) or pd.isna(value):
        return None
    f = float(value)
    return round(f, digits) if digits is not None else f


def risk_level(state: AppState, p: float) -> RiskLevel:
    return RiskLevel(state.model.bands.band(p))


def _summary(row: pd.Series, state: AppState) -> dict:
    tid = int(row["test_id"])
    pred = None
    if tid in state.oof.index:
        p = float(state.oof[tid])
        pred = OutOfFoldPrediction(fire_risk=round(100 * p, 1), risk_level=risk_level(state, p),
                                   sustained_probability=round(p, 4))
    return {
        "test_id": tid,
        "flex_identifier": row["flex_identifier"],
        "datetime_gmt": row["test_datetime_gmt"],
        "fuel": row["fuel"],
        "pressure_atm": num(row["pressure_atm"], 4),
        "pressure_level": row["pressure_level"],
        "oxygen_percent": round(100 * float(row["x_o2"]), 2),
        "nitrogen_percent": round(100 * float(row["x_n2"]), 2),
        "co2_percent": round(100 * float(row["x_co2"]), 2),
        "he_percent": round(100 * float(row["x_he"]), 2),
        "suppressant": SUPPRESSANT[row["diluent"]],
        "droplet_diameter_mm": num(row["d0_mm"], 2),
        "outcome": row["outcome_raw"],
        "sustained": bool(row["y_sustained"]),
        "burn_time_s": num(row["burn_time_s"], 2),
        "qc_flags": [f for f in str(row["qc_flags"]).split(";") if f],
        "in_model_scope": pred is not None,
        "prediction": pred,
        "source_id": "psi-69",
    }


def all_summaries(state: AppState) -> dict[int, ExperimentSummary]:
    """All 274 summaries, built once and cached."""
    if "summaries" not in state.cache:
        state.cache["summaries"] = {int(r["test_id"]): ExperimentSummary(**_summary(r, state))
                                    for _, r in state.master.iterrows()}
    return state.cache["summaries"]


def list_experiments(state: AppState, *, fuel: str | None = None, suppressant: str | None = None,
                     pressure_level: str | None = None, outcome: str | None = None,
                     in_model_scope: bool | None = None, oxygen_min: float | None = None,
                     oxygen_max: float | None = None, search: str | None = None,
                     sort: str = "test_id", limit: int = 50, offset: int = 0) -> ExperimentList:
    items = list(all_summaries(state).values())
    if fuel:
        items = [e for e in items if e.fuel.value == fuel]
    if suppressant:
        items = [e for e in items if e.suppressant == suppressant]
    if pressure_level:
        items = [e for e in items if e.pressure_level == pressure_level]
    if outcome:
        items = [e for e in items if e.outcome == outcome]
    if in_model_scope is not None:
        items = [e for e in items if e.in_model_scope == in_model_scope]
    if oxygen_min is not None:
        items = [e for e in items if e.oxygen_percent >= oxygen_min]
    if oxygen_max is not None:
        items = [e for e in items if e.oxygen_percent <= oxygen_max]
    if search:
        needle = search.strip().lower()
        items = [e for e in items if needle in e.flex_identifier.lower() or needle == str(e.test_id)]

    keys = {
        "test_id": lambda e: e.test_id,
        "oxygen": lambda e: e.oxygen_percent,
        "risk": lambda e: e.prediction.fire_risk if e.prediction else -1.0,
        "date": lambda e: e.datetime_gmt,
    }
    reverse = sort.startswith("-")
    items.sort(key=keys[sort.lstrip("-")], reverse=reverse)
    return ExperimentList(total=len(items), limit=limit, offset=offset, items=items[offset:offset + limit])


def get_experiment(state: AppState, test_id: int) -> ExperimentDetail | None:
    summary = all_summaries(state).get(test_id)
    if summary is None:
        return None
    row = state.master.loc[state.master["test_id"] == test_id].iloc[0]
    notes = [QC_FLAGS[f] for f in summary.qc_flags if f in QC_FLAGS]
    if test_id in state.excluded:
        notes.insert(0, EXCLUSION_TEXT.get(state.excluded[test_id], state.excluded[test_id]))
    return ExperimentDetail(
        **summary.model_dump(),
        extinction_diameter_mm=num(row["d_ext_mm"], 2),
        burning_rate_mm2_s=num(row["burn_rate_mm2_s"], 3),
        source=source_ref("psi-69"),
        notes=notes,
    )
