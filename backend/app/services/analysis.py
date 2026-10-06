"""Ranking, suppressant comparison and similar-experiment search."""

from __future__ import annotations

import itertools

from flameguard.ranking import observed_condition_ranking
from flameguard.similarity import nearest_tests

from app.schemas.common import Conditions
from app.schemas.responses import (ConditionRank, ConditionRankingResponse, ObservedPoint, RankingItem,
                                   RankingResponse, SeriesComparison, SeriesEstimate, SimilarItem, SimilarResponse,
                                   SuppressantsResponse)
from app.services.experiments import SUPPRESSANT, all_summaries, num
from app.state import AppState

# --- ranking ---------------------------------------------------------------------------

RANKINGS = {
    "risk": ("Predicted Fire Risk (highest first)", "prediction"),
    "lowest_risk": ("Predicted Fire Risk (lowest first)", "prediction"),
    "extinction": ("Predicted probability of self-extinction (highest first)", "prediction"),
    "burn_time": ("Observed burn time in seconds (longest first)", "observed"),
}


def ranking(state: AppState, by: str, fuel: str | None, limit: int) -> RankingResponse:
    exps = [e for e in all_summaries(state).values() if fuel is None or e.fuel.value == fuel]
    if by == "burn_time":
        exps = [e for e in exps if e.burn_time_s is not None]
        exps.sort(key=lambda e: -e.burn_time_s)
        values = [e.burn_time_s for e in exps]
        method = "Observed NASA burn times (all FLEX tests with a recorded burn time)."
    else:
        exps = [e for e in exps if e.prediction is not None]
        if by == "risk":
            exps.sort(key=lambda e: -e.prediction.fire_risk)
            values = [e.prediction.fire_risk for e in exps]
        elif by == "lowest_risk":
            exps.sort(key=lambda e: e.prediction.fire_risk)
            values = [e.prediction.fire_risk for e in exps]
        else:
            exps.sort(key=lambda e: e.prediction.sustained_probability)
            values = [round(100 * (1 - e.prediction.sustained_probability), 1) for e in exps]
        method = ("Out-of-fold predictions: each test was scored by models that never saw it during training, "
                  "averaged over 5 cross-validation repeats. Compare with each test's observed outcome.")
    label, prov = RANKINGS[by]
    items = [RankingItem(rank=i + 1, value=v, experiment=e) for i, (e, v) in enumerate(zip(exps, values))][:limit]
    return RankingResponse(by=by, metric_label=label, provenance=prov, method=method, items=items)


def condition_ranking(state: AppState, order: str, min_tests: int, limit: int) -> ConditionRankingResponse:
    r = observed_condition_ranking(state.master, min_tests=min_tests)
    if order == "asc":
        r = r.sort_values(["observed_rate", "tests"], ascending=[True, False]).reset_index(drop=True)
    items = [ConditionRank(rank=i + 1, fuel=row["fuel"], pressure_level=row["pressure_level"],
                           suppressant=SUPPRESSANT[row["diluent"]], oxygen_percent=round(100 * row["x_o2"], 2),
                           co2_percent=round(100 * row["x_co2"], 2), he_percent=round(100 * row["x_he"], 2),
                           tests=int(row["tests"]), sustained=int(row["sustained"]),
                           observed_rate=round(float(row["observed_rate"]), 4), ci_low=round(float(row["ci_low"]), 4),
                           ci_high=round(float(row["ci_high"]), 4), test_ids=row["test_ids"])
             for i, (_, row) in enumerate(r.head(limit).iterrows())]
    return ConditionRankingResponse(
        method=f"Share of ISS tests that kept burning per fuel and tested atmosphere (0.7-1 atm, >= {min_tests} "
               "tests), with 95% Wilson intervals. Droplet sizes differ between conditions, so this is not a "
               "controlled comparison.", items=items)


# --- suppressants ----------------------------------------------------------------------


def _pct(v):
    x = num(v)
    return None if x is None else round(100 * x, 2)


def suppressants(state: AppState) -> SuppressantsResponse:
    m = state.master[state.master["pressure_level"].isin(["0.7atm", "1atm"])]
    observed = [ObservedPoint(test_id=int(r["test_id"]), fuel=r["fuel"], pressure_level=r["pressure_level"],
                              suppressant=SUPPRESSANT[r["diluent"]], oxygen_percent=round(100 * r["x_o2"], 2),
                              co2_percent=round(100 * r["x_co2"], 2), he_percent=round(100 * r["x_he"], 2),
                              droplet_diameter_mm=num(r["d0_mm"], 2), outcome=r["outcome_raw"],
                              sustained=bool(r["y_sustained"])) for _, r in m.iterrows()]
    estimates = []
    for _, r in state.o2_50.iterrows():
        ok = r["status"] == "estimated"
        estimates.append(SeriesEstimate(
            fuel=r["fuel"], pressure_level=r["pressure"], suppressant=SUPPRESSANT[r["diluent"]],
            tests=int(r["tests"]), sustained=int(r["sustained"]), extinguished=int(r["extinguished"]),
            oxygen_tested_min=round(100 * r["o2_tested_min"], 2), oxygen_tested_max=round(100 * r["o2_tested_max"], 2),
            estimable=ok, o2_50_percent=_pct(r["o2_50"]), ci_low_percent=_pct(r["ci_low"]),
            ci_high_percent=_pct(r["ci_high"]), ci_beyond_tested=bool(r["ci_beyond_tested"]),
            suppressant_percent_at_o2_50=_pct(r["suppressant_at_o2_50"]), status=r["status"]))

    comparisons = []
    est = [e for e in estimates if e.estimable]
    for (fuel, pressure), group in itertools.groupby(sorted(est, key=lambda e: (e.fuel.value, e.pressure_level)),
                                                     key=lambda e: (e.fuel.value, e.pressure_level)):
        g = list(group)
        if len(g) < 2:
            continue
        overlap = all(x.ci_low_percent <= y.ci_high_percent and y.ci_low_percent <= x.ci_high_percent
                      for x, y in itertools.combinations(g, 2))
        names = {e.suppressant: (e.suppressant if e.suppressant != "none" else "N₂ only") for e in g}
        desc = "; ".join(f"{names[e.suppressant]} {e.o2_50_percent:.1f}% "
                         f"(95% CI {e.ci_low_percent:.1f}-{e.ci_high_percent:.1f}%)" for e in g)
        verdict = ("the intervals overlap, so these series cannot be ranked" if overlap
                   else "at least one pair of intervals does not overlap")
        comparisons.append(SeriesComparison(fuel=fuel, pressure_level=pressure,
                                            suppressants=[e.suppressant for e in g], intervals_overlap=overlap,
                                            statement=f"{fuel} at {pressure.replace('atm', ' atm')}: O₂₅₀ "
                                                      f"{desc}; {verdict}."))
    if comparisons and all(c.intervals_overlap for c in comparisons):
        conclusion = ("The observed FLEX data do not establish a ranking of the suppressants: wherever more than one "
                      "series can be estimated, the 95% intervals overlap.")
    elif comparisons:
        conclusion = "Some series differ beyond their 95% intervals; see the comparisons for which ones."
    else:
        conclusion = "No fuel and pressure has more than one estimable series, so no comparison is possible."
    return SuppressantsResponse(
        method=("O₂₅₀ = O₂ level at which half of 3 mm droplets kept burning, from a logistic fit "
                "to each fuel x pressure x suppressant series of observed tests (adjusted for droplet size), with 95% "
                "intervals from resampling tested atmospheres. A series is estimated only with >= 3 sustained and "
                ">= 3 extinguished tests and an estimate inside its tested O₂ range. No ML model is used."),
        observed=observed, estimates=estimates, comparisons=comparisons, conclusion=conclusion,
        caveats=[
            "O₂₅₀ is not NASA's limiting oxygen index (LOI), which is the O₂ level below which "
            "quasi-steady burning is not observed at all.",
            "Series were run on different days with different droplet sizes, and the suppressant fraction rose as "
            "O₂ fell, so differences can reflect the test design as well as the gas.",
            "SF₆ is named in FLEX's objectives but no SF₆ tests are in this dataset.",
        ])


# --- similar ---------------------------------------------------------------------------


def similar(state: AppState, conditions: Conditions, k: int) -> SimilarResponse:
    inputs = conditions.to_inputs()
    near = nearest_tests(state.tests, state.model.domain, inputs, k=k)
    summaries = all_summaries(state)
    items = [SimilarItem(similarity=round(float(r["similarity"]), 1), distance=round(float(r["distance"]), 3),
                         experiment=summaries[int(r["test_id"])]) for _, r in near.iterrows()]
    return SimilarResponse(
        method=("Nearest tested FLEX conditions for the same fuel by distance in standardised O₂, CO₂, He "
                "and droplet diameter. Similarity = 100 × exp(−distance / support radius): 100 for an "
                "identical condition, about 37 at the typical spacing between tested atmospheres. Searches the 252 "
                "tests in the model's 0.7-1 atm scope."),
        query=conditions, support_radius=round(state.model.domain.support_radius[inputs["fuel"]], 3), items=items)
