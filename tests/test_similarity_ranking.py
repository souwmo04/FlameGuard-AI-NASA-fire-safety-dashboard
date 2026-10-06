import pandas as pd
import pytest

from flameguard.prediction import ApplicabilityDomain
from flameguard.ranking import observed_condition_ranking
from flameguard.similarity import nearest_tests


def _tests():
    return pd.DataFrame({
        "test_id": [1, 2, 3, 4],
        "fuel": ["Methanol", "Methanol", "Methanol", "Heptane"],
        "x_o2": [0.21, 0.18, 0.15, 0.21], "x_co2": [0.0, 0.1, 0.2, 0.0], "x_he": [0.0, 0.0, 0.0, 0.0],
        "d0_mm": [3.0, 3.0, 3.0, 3.0],
    })


def _domain(t):
    return ApplicabilityDomain.fit(t, pd.Series(["a", "b", "c", "d"]))


def test_nearest_tests_same_fuel_sorted_and_scored():
    t = _tests()
    near = nearest_tests(t, _domain(t), {"fuel": "Methanol", "x_o2": 0.21, "x_co2": 0.0, "x_he": 0.0, "d0_mm": 3.0}, k=2)
    assert list(near["test_id"]) == [1, 2]
    assert near["similarity"].iloc[0] == pytest.approx(100)
    assert near["similarity"].iloc[1] < 100


def test_nearest_tests_rejects_bad_k():
    t = _tests()
    with pytest.raises(ValueError):
        nearest_tests(t, _domain(t), {"fuel": "Methanol", "x_o2": 0.2, "x_co2": 0, "x_he": 0, "d0_mm": 3}, k=0)


def test_observed_condition_ranking_respects_min_tests():
    master = pd.DataFrame({
        "test_id": range(7), "fuel": ["Methanol"] * 7, "pressure_level": ["1atm"] * 6 + ["2-3atm"],
        "group_id_atmosphere": ["A", "A", "A", "B", "B", "C", "A"], "y_sustained": [1, 1, 0, 0, 0, 1, 1],
        "x_o2": [0.21] * 3 + [0.15] * 2 + [0.3, 0.21], "x_co2": [0.0] * 7, "x_he": [0.0] * 7,
        "diluent": ["N2"] * 7,
    })
    r = observed_condition_ranking(master, min_tests=2)
    assert list(r["group_id_atmosphere"]) == ["A", "B"]  # C has 1 test; 2-3 atm row excluded
    assert r.loc[0, "observed_rate"] == pytest.approx(2 / 3)
    assert r.loc[0, "test_ids"] == [0, 1, 2]
