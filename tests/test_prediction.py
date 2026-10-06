import numpy as np
import pandas as pd
import pytest

from flameguard.prediction import BUNDLE_PATH, PREDICTION_LABEL, ApplicabilityDomain, FinalModel, RiskBands

requires_bundle = pytest.mark.skipif(not BUNDLE_PATH.exists(), reason="run scripts/finalize_model.py first")


def test_risk_bands_boundaries():
    b = RiskBands(alert_threshold=0.2)
    assert b.band(0.19) == "LOW"
    assert b.band(0.2) == "ELEVATED"
    assert b.band(0.49) == "ELEVATED"
    assert b.band(0.5) == "HIGH"


def _domain():
    X = pd.DataFrame({
        "fuel": ["Methanol"] * 4 + ["Heptane"] * 4,
        "x_o2": [0.15, 0.18, 0.21, 0.24] * 2,
        "x_co2": [0.3, 0.2, 0.1, 0.0] * 2,
        "x_he": [0.0] * 8,
        "d0_mm": [2.0, 2.5, 3.0, 3.5] * 2,
    })
    groups = pd.Series([f"g{i}" for i in range(4)] * 2)
    return ApplicabilityDomain.fit(X, groups)


def test_domain_accepts_tested_point_and_flags_far_combination():
    dom = _domain()
    near = dom.check(pd.Series({"fuel": "Methanol", "x_o2": 0.18, "x_co2": 0.2, "x_he": 0.0, "d0_mm": 2.5}))
    assert near["in_range"] and near["supported"] and not near["warnings"]
    # every value inside its own range, but the combination is off the tested diagonal
    far = dom.check(pd.Series({"fuel": "Methanol", "x_o2": 0.15, "x_co2": 0.0, "x_he": 0.0, "d0_mm": 3.5}))
    assert far["in_range"] and not far["supported"]


def test_domain_flags_out_of_range_and_unknown_fuel():
    dom = _domain()
    out = dom.check(pd.Series({"fuel": "Heptane", "x_o2": 0.40, "x_co2": 0.0, "x_he": 0.0, "d0_mm": 3.0}))
    assert not out["in_range"]
    assert any("x_o2" in w for w in out["warnings"])
    unknown = dom.check(pd.Series({"fuel": "Decane", "x_o2": 0.21, "x_co2": 0.0, "x_he": 0.0, "d0_mm": 3.0}))
    assert not unknown["supported"]


@requires_bundle
def test_saved_model_predicts_with_labels_and_bands():
    fm = FinalModel.load()
    q = pd.DataFrame([{"fuel": "Heptane", "x_o2": 0.21, "x_co2": 0.0, "x_he": 0.0, "d0_mm": 3.0},
                      {"fuel": "Methanol", "x_o2": 0.13, "x_co2": 0.0, "x_he": 0.0, "d0_mm": 3.0}])
    r = fm.predict(q)
    assert np.allclose(r["p_sustained"] + r["p_extinction"], 1)
    assert r["fire_risk"].between(0, 100).all()
    assert set(r["risk_band"]) <= {"LOW", "ELEVATED", "HIGH"}
    assert (r["label"] == PREDICTION_LABEL).all()
    assert r.loc[0, "fire_risk"] > r.loc[1, "fire_risk"]  # more O2 and heptane -> higher risk


@requires_bundle
def test_saved_model_is_monotone_in_oxygen_and_ignores_pressure():
    fm = FinalModel.load()
    base = {"fuel": "Methanol", "x_co2": 0.0, "x_he": 0.0, "d0_mm": 3.0}
    grid = pd.DataFrame([{**base, "x_o2": o} for o in np.linspace(0.12, 0.34, 12)])
    p = fm.predict(grid)["p_sustained"].to_numpy()
    assert np.all(np.diff(p) > 0)
    with_p = fm.predict(grid.assign(pressure_atm=0.7))["p_sustained"].to_numpy()
    assert np.allclose(p, with_p)
    assert "pressure_atm" not in fm.metadata["features"]


@requires_bundle
def test_saved_model_rejects_missing_inputs():
    with pytest.raises(ValueError, match="Missing inputs"):
        FinalModel.load().predict(pd.DataFrame([{"fuel": "Heptane", "x_o2": 0.21}]))
