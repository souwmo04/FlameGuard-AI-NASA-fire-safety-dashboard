import numpy as np
import pandas as pd
import pytest
import shap

from flameguard import explainability as ex
from flameguard.prediction import BUNDLE_PATH, FinalModel

requires_bundle = pytest.mark.skipif(not BUNDLE_PATH.exists(), reason="run scripts/finalize_model.py first")


def test_exact_shapley_matches_closed_form_for_additive_function():
    # f(z) = 2 z0 + 3 z1: Shapley value of feature j = coef_j * (x_j - mean(background_j))
    f = lambda Z: 2 * Z[:, 0] + 3 * Z[:, 1]  # noqa: E731
    bg = np.array([[0.0, 0.0], [2.0, 4.0]])
    phi, base = ex.exact_shapley(f, np.array([3.0, 1.0]), bg, [[0], [1]])
    assert base == pytest.approx(f(bg).mean())
    assert phi == pytest.approx([2 * (3 - 1), 3 * (1 - 2)])


def test_exact_shapley_groups_share_interaction_and_stay_additive():
    f = lambda Z: Z[:, 0] * Z[:, 1] + Z[:, 2]  # noqa: E731
    bg = np.zeros((1, 3))
    x = np.array([2.0, 3.0, 1.0])
    phi, base = ex.exact_shapley(f, x, bg, [[0], [1], [2]])
    assert phi[0] == pytest.approx(3.0) and phi[1] == pytest.approx(3.0)  # interaction split equally
    phi_g, _ = ex.exact_shapley(f, x, bg, [[0, 1], [2]])
    assert phi_g == pytest.approx([6.0, 1.0])
    assert base + phi.sum() == pytest.approx(f(x[None])[0])


def test_format_risk_extremes():
    assert ex.format_risk(99.87) == "> 99"
    assert ex.format_risk(0.2) == "< 1"
    assert ex.format_risk(42.4) == "42"


def _inputs():
    return pd.DataFrame([
        {"fuel": "Heptane", "x_o2": 0.21, "x_co2": 0.0, "x_he": 0.0, "d0_mm": 3.0},
        {"fuel": "Methanol", "x_o2": 0.15, "x_co2": 0.3, "x_he": 0.0, "d0_mm": 2.5},
        {"fuel": "Methanol", "x_o2": 0.17, "x_co2": 0.0, "x_he": 0.25, "d0_mm": 3.5},
        {"fuel": "Heptane", "x_o2": 0.30, "x_co2": 0.0, "x_he": 0.0, "d0_mm": 2.0},
    ])


@requires_bundle
@pytest.mark.parametrize("grouping", ["grouped", "detailed", "detailed_symmetric"])
def test_explanations_are_additive_on_final_model(grouping):
    fm = FinalModel.load()
    X = _inputs()
    c = ex.explain(fm, X, X, grouping)
    total = c.drop(columns=["base", "fire_risk"]).sum(axis=1) + c["base"]
    assert np.allclose(total, c["fire_risk"], atol=1e-8)
    assert np.allclose(c["fire_risk"], fm.predict(X)["fire_risk"], atol=0.051)  # predict() rounds to 0.1


@requires_bundle
def test_detailed_values_match_shap_library_exact_explainer():
    fm = FinalModel.load()
    X = _inputs()
    ours = ex.explain(fm, X, X, "detailed_symmetric")[["fuel", "O\u2082", "CO\u2082", "He", "droplet size"]].to_numpy()
    bg = ex.to_raw(X).to_numpy()
    explainer = shap.explainers.Exact(ex.risk_function(fm), shap.maskers.Independent(bg, max_samples=len(bg)))
    assert np.allclose(explainer(bg).values, ours, atol=1e-9)


@requires_bundle
def test_describe_mentions_values_and_caveat():
    fm = FinalModel.load()
    X = _inputs()
    row = ex.explain(fm, X.iloc[[0]], X, "grouped").iloc[0]
    text = ex.describe(row, "HIGH", X.iloc[0])
    assert "Model prediction for a heptane droplet" in text
    assert "not measured effects" in text
    assert "atmosphere" in text


def test_fuel_first_values_follow_the_conditional_effect():
    # f = fuel * d (pure interaction). Symmetric Shapley gives d credit even when fuel = 0;
    # fuel-first gives d exactly the slope it has for the test's own fuel.
    f = lambda Z: Z[:, 0] * Z[:, 1]  # noqa: E731
    bg = np.array([[1.0, 0.0], [0.0, 0.0]])
    x = np.array([0.0, 2.0])  # "methanol" (fuel 0): changing d does nothing for this fuel
    sym, _ = ex.exact_shapley(f, x, bg, [[0], [1]])
    asym, base = ex.exact_shapley(f, x, bg, [[0], [1]], first=0)
    assert sym[1] != pytest.approx(0)          # symmetric credits d via the other fuel
    assert asym[1] == pytest.approx(0)         # fuel-first: d has no effect for this fuel
    assert base + asym.sum() == pytest.approx(f(x[None])[0])


@requires_bundle
def test_methanol_droplet_contribution_matches_model_direction():
    fm = FinalModel.load()
    q = pd.DataFrame([{"fuel": f, "x_o2": 0.21, "x_co2": 0.0, "x_he": 0.0, "d0_mm": d}
                      for f in ["Methanol", "Heptane"] for d in [2.0, 3.0, 4.0]])
    c = ex.explain(fm, q, q, "grouped")["droplet size"].to_numpy()
    risk = fm.predict(q)["fire_risk"].to_numpy()
    assert np.all(np.diff(risk[:3]) > 0) and np.all(np.diff(c[:3]) > 0)   # methanol: both rise
    assert np.all(np.diff(risk[3:]) < 0) and np.all(np.diff(c[3:]) < 0)   # heptane: both fall
