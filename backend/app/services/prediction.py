"""POST /api/predict: Fire Risk, evidence, Shapley explanation and a template interpretation."""

from __future__ import annotations

import pandas as pd

from flameguard import explainability as ex
from flameguard.explainability import format_risk
from flameguard.similarity import nearest_tests

from app.schemas.common import Conditions, RiskLevel
from app.schemas.responses import (BandEvidence, Contribution, Evidence, Explanation, Interpretation,
                                   InterpretationPoint, PredictResponse)
from app.services.experiments import risk_level
from app.state import AppState

PLAYERS = {
    "fuel": ("fuel", "Fuel"),
    "atmosphere (O₂ + CO₂ + He)": ("atmosphere", "Atmosphere (O₂ + CO₂ + He)"),
    "droplet size": ("droplet_size", "Droplet size"),
}
SCOPE = ("Single methanol or n-heptane droplets burning in a quiescent microgravity atmosphere at 0.7-1 atm "
         "(NASA FLEX test conditions). Not a certified spacecraft fire-safety system.")
EXPLANATION_METHOD = ("Exact interventional Shapley values on the model inputs, fuel accounted for first "
                      "(asymmetric Shapley values); O₂, CO₂ and He grouped as one atmosphere contribution.")
EXPLANATION_NOTE = ("Contributions show how the model uses each input relative to the average FLEX test. They are "
                    "associations learned from NASA data, not measured effects of changing a condition. NASA varied "
                    "oxygen and suppressant together, so their separate effects cannot be isolated.")


def band_evidence(state: AppState, level: RiskLevel) -> BandEvidence:
    s = state.model.bands.band_stats[level.value]
    return BandEvidence(level=level, tests=int(s["tests"]), observed_sustained_rate=round(s["observed_sustained_rate"], 4),
                        ci_low=round(s["ci_low"], 4), ci_high=round(s["ci_high"], 4))


def contributions(state: AppState, inputs: dict) -> tuple[float, list[Contribution]]:
    row = ex.explain(state.model, pd.DataFrame([inputs]), state.background, "grouped").iloc[0]
    out = []
    for player, (key, label) in PLAYERS.items():
        v = float(row[player])
        direction = "neutral" if abs(v) < 0.5 else ("raises" if v > 0 else "lowers")
        out.append(Contribution(key=key, label=label, impact=round(v, 2), direction=direction))
    out.sort(key=lambda c: -abs(c.impact))
    return round(float(row["base"]), 2), out


def interpret(conditions: Conditions, fire_risk: float, level: RiskLevel, p: float, base: float,
              contribs: list[Contribution], evidence: Evidence) -> Interpretation:
    fuel = "n-heptane" if conditions.fuel.value == "Heptane" else "methanol"
    points = [InterpretationPoint(
        kind="summary",
        # Fire Risk is 100 x P(sustained): print one rounded number for both so they never disagree (22 vs 21%).
        text=f"Fire Risk {format_risk(fire_risk)}/100 ({level.value}): the model estimates a {format_risk(fire_risk)}% probability "
             f"that a burning {fuel} droplet under these conditions keeps burning instead of putting itself out.")]
    movers = [c for c in contribs if c.direction != "neutral"]
    if movers:
        phrases = []
        for c in movers:
            pts = round(abs(c.impact))
            phrases.append(f"{c.label.split(' (')[0].lower()} {c.direction} it by {pts} point{'s' if pts != 1 else ''}")
        points.append(InterpretationPoint(
            kind="drivers", text=f"Compared with the average FLEX test ({base:.0f}/100), " + "; ".join(phrases) + "."))
    b = evidence.band
    points.append(InterpretationPoint(
        kind="evidence", text=f"In cross-validation, {b.observed_sustained_rate:.0%} of the {b.tests} FLEX tests the "
                              f"model placed in the {level.value} band actually kept burning."))
    if not evidence.supported_by_data or not evidence.in_tested_range:
        points.append(InterpretationPoint(
            kind="extrapolation", text="These conditions are far from any tested FLEX condition, so this estimate is "
                                       "an extrapolation and may be poorly calibrated."))
    if conditions.suppressant.value != "none":
        points.append(InterpretationPoint(
            kind="suppressant", text="The model cannot separate the effect of the suppressant from the lower oxygen it "
                                     "was tested with in FLEX."))
    points.append(InterpretationPoint(kind="disclaimer", text="This is a model prediction, not a NASA measurement."))
    return Interpretation(text=" ".join(pt.text for pt in points), points=points)


def predict(state: AppState, conditions: Conditions) -> PredictResponse:
    inputs = conditions.to_inputs()
    res = state.model.predict(pd.DataFrame([inputs])).iloc[0]
    p = float(res["p_sustained"])
    level = risk_level(state, p)
    fire_risk = round(100 * p, 1)
    fuel = inputs["fuel"]
    near = nearest_tests(state.tests, state.model.domain, inputs, k=3)
    evidence = Evidence(
        in_tested_range=bool(res["in_tested_range"]),
        supported_by_data=bool(res["supported_by_data"]),
        nearest_tested_distance=round(float(res["nearest_tested_distance"]), 3),
        support_radius=round(state.model.domain.support_radius[fuel], 3),
        warnings=list(res["warnings"]),
        band=band_evidence(state, level),
        nearest_experiment_ids=[int(t) for t in near["test_id"]],
    )
    base, contribs = contributions(state, inputs)
    return PredictResponse(
        conditions=conditions,
        fire_risk=fire_risk,
        risk_level=level,
        sustained_probability=round(p, 4),
        extinction_probability=round(1 - p, 4),
        evidence=evidence,
        explanation=Explanation(method=EXPLANATION_METHOD, base_value=base, contributions=contribs,
                                note=EXPLANATION_NOTE),
        interpretation=interpret(conditions, fire_risk, level, p, base, contribs, evidence),
        model=state.card["metadata"]["model"],
        scope=SCOPE,
    )
