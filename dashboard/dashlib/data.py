"""Cached data access for the dashboard. Everything shown comes from files produced by the
pipeline scripts; the dashboard computes nothing it cannot trace to those files."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import streamlit as st

from flameguard import explainability as ex
from flameguard.data_loader import PROJECT_ROOT
from flameguard.dataset import build_modeling_data
from flameguard.eda import wilson_interval
from flameguard.prediction import CARD_PATH, DOMAIN_FEATURES, FinalModel

REPORTS = PROJECT_ROOT / "reports"
MASTER_PATH = PROJECT_ROOT / "data" / "processed" / "combustion_master.csv"
FLEX_DOI = "10.60555/mbq8-0451"
FLEX_URL = "https://psi.nasa.gov/physci/repo/data/investigations/PSI-69"
REPORT_URL = "https://ntrs.nasa.gov/citations/20150023456"


@st.cache_data
def master() -> pd.DataFrame:
    df = pd.read_csv(MASTER_PATH)
    df["qc_flags"] = df["qc_flags"].fillna("")
    return df


@st.cache_resource
def model() -> FinalModel:
    return FinalModel.load()


@st.cache_data
def model_card() -> dict:
    return json.loads(CARD_PATH.read_text(encoding="utf-8"))


@st.cache_data
def training_frame() -> pd.DataFrame:
    """The 252 primary tests the final model was trained on (inputs + identifiers + outcome)."""
    data = build_modeling_data(master(), "primary")
    frame = data.X.drop(columns="pressure_atm").copy()
    for c in ["test_id", "flex_identifier", "diluent", "pressure_level", "outcome_raw"]:
        frame[c] = data.meta[c].to_numpy()
    frame["y_sustained"] = data.y.to_numpy()
    return frame


@st.cache_data
def report(phase: str, name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(REPORTS / phase / name, **kwargs)


@st.cache_data
def oof_final() -> pd.DataFrame:
    """Out-of-fold predictions of the final model, averaged over the 5 CV repeats (one row per test)."""
    oof = report("phase8", "final_oof_predictions.csv")
    oof = oof[oof["model"] == "logreg_np"]
    avg = oof.groupby("test_id").agg(p_oof=("p_sustained", "mean")).reset_index()
    return training_frame().merge(avg, on="test_id")


def explain_query(query: pd.DataFrame) -> pd.Series:
    """Fuel-first grouped Shapley contributions for one query row (Fire Risk points)."""
    bg = training_frame()[["fuel", *DOMAIN_FEATURES]]
    return ex.explain(model(), query, bg, "grouped").iloc[0]


def nearest_tests(query: pd.Series, k: int = 5) -> pd.DataFrame:
    """The k most similar tested FLEX conditions for the same fuel (standardised O2, CO2, He, d0)."""
    tr = training_frame()
    same = tr[tr["fuel"] == query["fuel"]].copy()
    scale = model().domain.scale
    d2 = sum(((same[c] - float(query[c])) / scale[c]) ** 2 for c in DOMAIN_FEATURES)
    same["distance"] = np.sqrt(d2)
    radius = model().domain.support_radius[query["fuel"]]
    same["similarity"] = (100 * np.exp(-same["distance"] / radius)).round(0)
    return same.nsmallest(k, "distance")


def observed_condition_ranking(min_tests: int = 3) -> pd.DataFrame:
    """Observed sustained rate per fuel x tested atmosphere (only cells with >= min_tests)."""
    m = master()
    m = m[m["pressure_level"].isin(["0.7atm", "1atm"])]
    g = (m.groupby(["fuel", "group_id_atmosphere"])
         .agg(tests=("y_sustained", "size"), sustained=("y_sustained", "sum"), x_o2=("x_o2", "first"),
              x_co2=("x_co2", "first"), x_he=("x_he", "first"), pressure=("pressure_level", "first"),
              diluent=("diluent", "first"))
         .reset_index())
    g = g[g["tests"] >= min_tests].copy()
    ci = [wilson_interval(int(s), int(n)) for s, n in zip(g["sustained"], g["tests"])]
    g["observed_rate"] = g["sustained"] / g["tests"]
    g["ci_low"], g["ci_high"] = [c[0] for c in ci], [c[1] for c in ci]
    return g
