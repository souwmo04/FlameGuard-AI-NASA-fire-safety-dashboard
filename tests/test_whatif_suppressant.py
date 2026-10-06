import numpy as np
import pandas as pd
import pytest

from flameguard.prediction import BUNDLE_PATH, FinalModel
from flameguard.suppressant import o2_50, summarize_series
from flameguard.whatif import predict_one, scenario_path, sweep

requires_bundle = pytest.mark.skipif(not BUNDLE_PATH.exists(), reason="run scripts/finalize_model.py first")
BASE = {"fuel": "Methanol", "x_o2": 0.21, "x_co2": 0.0, "x_he": 0.0, "d0_mm": 3.0}


@requires_bundle
def test_scenario_path_steps_and_totals():
    fm = FinalModel.load()
    target = {**BASE, "x_o2": 0.18, "x_co2": 0.10}
    path = scenario_path(fm, BASE, target)
    assert list(path["step"]) == ["baseline", "oxygen", "suppressant"]
    assert path["fire_risk"].iloc[0] == pytest.approx(predict_one(fm, BASE)["fire_risk"])
    assert path["fire_risk"].iloc[-1] == pytest.approx(predict_one(fm, target)["fire_risk"])
    assert path["delta"].sum() == pytest.approx(path["fire_risk"].iloc[-1] - path["fire_risk"].iloc[0])
    assert path["delta"].iloc[1] < 0  # less oxygen -> lower risk


@requires_bundle
def test_identical_scenarios_give_single_row():
    assert len(scenario_path(FinalModel.load(), BASE, dict(BASE))) == 1


@requires_bundle
def test_sweep_is_monotone_in_oxygen_and_flags_extrapolation():
    fm = FinalModel.load()
    s = sweep(fm, BASE, "x_o2", np.linspace(0.12, 0.34, 23))
    assert np.all(np.diff(s["fire_risk"]) > 0)
    assert s["supported"].dtype == bool
    far = sweep(fm, {**BASE, "x_co2": 0.45}, "x_o2", np.array([0.30]))
    assert not far["supported"].iloc[0]  # high O2 with high CO2 was never tested


def test_mixed_suppressants_rejected():
    with pytest.raises(ValueError, match="never combined"):
        scenario_path(None, BASE, {**BASE, "x_co2": 0.1, "x_he": 0.1})


def test_o2_50_recovers_known_threshold():
    rng = np.random.default_rng(1)
    o2 = np.repeat(np.linspace(0.14, 0.28, 15), 6)
    y = (o2 + rng.normal(0, 0.01, len(o2)) > 0.21).astype(int)
    df = pd.DataFrame({"x_o2": o2, "d0_mm": 3.0, "y_sustained": y})
    assert o2_50(df) == pytest.approx(0.21, abs=0.01)
    assert np.isnan(o2_50(df.assign(y_sustained=0)))


def test_summarize_series_applies_estimability_rules():
    master = pd.read_csv(BUNDLE_PATH.parents[1] / "data" / "processed" / "combustion_master.csv")
    t = summarize_series(master, n_boot=200).set_index(["fuel", "pressure", "diluent"])
    assert t.loc[("Methanol", "1atm", "He"), "status"].startswith("not estimable")   # 0 sustained
    est = t[t["status"] == "estimated"]
    assert (est["o2_50"].between(est["o2_tested_min"], est["o2_tested_max"])).all()
    assert (est["ci_low"] <= est["o2_50"]).all() and (est["o2_50"] <= est["ci_high"]).all()
    assert ((est["sustained"] >= 3) & (est["extinguished"] >= 3)).all()
