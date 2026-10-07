"""Health, statistics, applicability domain and model card."""

from __future__ import annotations

import math

from app.schemas.responses import (BandRow, CalibrationBin, DomainResponse, ExperimentCounts, FuelDomain,
                                   HealthResponse, ImportanceRow, MetricWithInterval, ModelInfoResponse, ModelSummary,
                                   StatsResponse, SubgroupRow)
from app.services.sources import SOURCES
from app.state import AppState

SUPPRESSANT_LABELS = {"N2": "none (O₂/N₂ only)", "CO2": "CO2", "He": "He"}
LIMITATIONS = [
    "Two fuels (methanol, n-heptane), single droplets, quiescent atmosphere, 0.7-1 atm, ambient temperature. No solid "
    "materials, airflow, cabin geometry or large fires.",
    "252 training tests from 44 tested atmospheres; methanol with helium has only 2 sustained tests.",
    "The model cannot separate a suppressant's effect from the oxygen reduction it was tested with.",
    "Methanol fires are missed more often (recall 0.83) than heptane fires (0.94).",
    "NASA chose tests to locate extinction limits, so outcome rates are not real-world fire frequencies.",
    "Fuel-needle contamination: NASA attributes methanol disruptions probably to a needle coating "
    "(NASA/TP-2015-216046, pp. 16-17). Disruption counts as sustained here, so methanol scores are uncertain; "
    "each methanol prediction shows a contamination check (decision D-002).",
    "Research prototype; not a certified spacecraft fire-safety system.",
]


def health(state: AppState) -> HealthResponse:
    return HealthResponse(status="ok", api_version=state.settings.api_version, model=state.card["metadata"]["model"],
                          training_tests=int(state.card["metadata"]["training_tests"]), data_sha256=state.data_sha256)


def _nested(state: AppState) -> dict:
    return state.card["metadata"]["validation"]["nested_threshold_estimates"]


def stats(state: AppState) -> StatsResponse:
    m = state.master
    outcome = m["outcome_raw"].value_counts()
    nested = _nested(state)
    val = state.card["metadata"]["validation"]
    dates = m["test_datetime_gmt"].str[:10]
    return StatsResponse(
        program="FLEX — Flame Extinguishment Experiment (International Space Station, 2009-2011)",
        nasa_investigations=1,
        nasa_sources=len(SOURCES),
        experiments=ExperimentCounts(
            total=len(m), in_model_scope=len(state.tests), extinction=int(outcome.get("Extinction", 0)),
            completion=int(outcome.get("Completion", 0)), disruption=int(outcome.get("Disruption", 0)),
            sustained=int(m["y_sustained"].sum())),
        fuels=sorted(m["fuel"].unique()),
        suppressants_tested=[SUPPRESSANT_LABELS[d] for d in ["N2", "CO2", "He"] if d in set(m["diluent"])],
        pressure_levels=sorted(m["pressure_level"].unique()),
        date_start=dates.min(),
        date_end=dates.max(),
        model=ModelSummary(
            name=state.card["metadata"]["model"],
            validation=val["scheme"],
            roc_auc=round(nested["roc_auc"][0], 4), roc_auc_sd=round(nested["roc_auc"][1], 4),
            pr_auc=round(nested["pr_auc"][0], 4), brier=round(nested["brier"][0], 4),
            recall_at_alert=round(nested["recall@safe"][0], 4), precision_at_alert=round(nested["precision@safe"][0], 4),
            calibration_slope_min=round(val["calibration_slope_range"][0], 3),
            calibration_slope_max=round(val["calibration_slope_range"][1], 3),
            alert_threshold_score=round(100 * state.model.bands.alert_threshold, 1)),
    )


def domain(state: AppState) -> DomainResponse:
    fuels = {}
    for fuel, r in state.model.domain.ranges.items():
        fuels[fuel] = FuelDomain(
            oxygen_percent=(round(100 * r["x_o2"][0], 2), round(100 * r["x_o2"][1], 2)),
            co2_percent=(round(100 * r["x_co2"][0], 2), round(100 * r["x_co2"][1], 2)),
            he_percent=(round(100 * r["x_he"][0], 2), round(100 * r["x_he"][1], 2)),
            droplet_diameter_mm=(round(r["d0_mm"][0], 2), round(r["d0_mm"][1], 2)))
    return DomainResponse(fuels=fuels, pressure_scope_atm=(0.7, 1.0), notes=[
        "Ranges are the minimum and maximum tested for each fuel; inside every range a combination can still be "
        "untested, which /api/predict reports as an extrapolation.",
        "Pressure is not a model input (decision D-001); predictions apply to 0.7-1 atm only.",
        "Temperature and airflow are not inputs: FLEX burned droplets at ambient temperature in a quiescent chamber.",
    ])


def _f(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else float(v)


def model_info(state: AppState) -> ModelInfoResponse:
    meta = state.card["metadata"]
    nested = _nested(state)
    boot = meta["validation"]["oof_bootstrap_95ci"]
    pairs = [("ROC-AUC", "roc_auc", "roc_auc"), ("PR-AUC", "pr_auc", "pr_auc"), ("Brier score", "brier", "brier"),
             ("Log loss", "log_loss", "log_loss"), ("Recall at alert threshold", "recall@safe", "recall"),
             ("Precision at alert threshold", "precision@safe", "precision"),
             ("Missed-fire rate", "false_negative_rate@safe", "false_negative_rate")]
    metrics = []
    for name, nkey, bkey in pairs:
        b = boot.get(bkey)
        metrics.append(MetricWithInterval(name=name, nested_mean=round(nested[nkey][0], 4),
                                          nested_sd=round(nested[nkey][1], 4),
                                          pooled_estimate=round(b[0], 4) if b else None,
                                          pooled_ci_low=round(b[1], 4) if b else None,
                                          pooled_ci_high=round(b[2], 4) if b else None))
    alert = 100 * state.model.bands.alert_threshold
    edges = {"LOW": (0.0, alert), "ELEVATED": (alert, 50.0), "HIGH": (50.0, 100.0)}
    bands = [BandRow(level=r["band"], score_from=round(edges[r["band"]][0], 1), score_to=round(edges[r["band"]][1], 1),
                     tests=int(r["tests"]), sustained=int(r["sustained"]),
                     observed_sustained_rate=round(r["observed_sustained_rate"], 4),
                     ci_low=round(max(r["ci_low"], 0.0), 4), ci_high=round(r["ci_high"], 4))
             for _, r in state.risk_bands.iterrows()]
    return ModelInfoResponse(
        name=meta["model"], features=meta["features"],
        standardised_coefficients={k: float(v) for k, v in meta["standardised_coefficients"].items()},
        training_tests=int(meta["training_tests"]), training_sustained=int(meta["training_sustained"]),
        validation=meta["validation"]["scheme"], metrics=metrics,
        calibration=[CalibrationBin(mean_predicted=round(r["mean_predicted"], 4), observed_rate=round(r["observed_rate"], 4),
                                    ci_low=round(max(r["ci_low"], 0.0), 4), ci_high=round(r["ci_high"], 4),
                                    tests=int(r["n"])) for _, r in state.reliability.iterrows()],
        bands=bands,
        subgroups=[SubgroupRow(subgroup=r["subgroup"], tests=int(r["tests"]), sustained=int(r["sustained"]),
                               roc_auc=_f(r["roc_auc"]), recall=_f(r["recall"]), missed_fires=int(r["missed_fires"]),
                               false_alarms=int(r["false_alarms"])) for _, r in state.subgroups.iterrows()],
        global_importance=[ImportanceRow(player=r["player"], mean_abs_points=round(r["mean_abs_points"], 2),
                                         share=round(r["share"], 4)) for _, r in state.global_importance.iterrows()],
        consistently_missed_test_ids=[int(t) for t in state.missed_fires["test_id"]],
        limitations=LIMITATIONS,
    )
