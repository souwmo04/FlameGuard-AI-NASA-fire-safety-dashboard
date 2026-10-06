"""Headless smoke tests of every dashboard page with Streamlit's AppTest."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from flameguard.prediction import BUNDLE_PATH  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "dashboard" / "app.py")
PAGES = ["views/home.py", "views/explorer.py", "views/predictor.py", "views/ranking.py", "views/performance.py",
         "views/about.py"]

pytestmark = pytest.mark.skipif(not BUNDLE_PATH.exists(), reason="run scripts/finalize_model.py first")


def run(page: str | None = None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    if page:
        at.switch_page(page)
        at.run()
    return at


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_exceptions(page):
    at = run(page)
    assert not at.exception, [e.value for e in at.exception]
    assert at.title


def test_home_shows_dataset_counts():
    at = run()
    labels = {m.label: m.value for m in at.metric}
    assert labels["FLEX tests"] == "274"
    assert labels["Self-extinguished"] == "186"


def test_predictor_returns_risk_explanation_and_neighbours():
    at = run("views/predictor.py")
    at.radio(key="fuel").set_value("Heptane")
    at.button(key="analyze").click()
    at.run()
    assert not at.exception
    metrics = {m.label: m.value for m in at.metric}
    assert "Fire Risk" in metrics and metrics["Fire Risk"].endswith("/ 100")
    assert any("Model prediction for a heptane droplet" in md.value for md in at.markdown)
    assert len(at.dataframe) >= 1  # most similar NASA tests


def test_predictor_flags_untested_combination():
    at = run("views/predictor.py")
    at.radio(key="fuel").set_value("Methanol")
    at.slider(key="o2").set_value(0.25)
    at.selectbox(key="supp").set_value("CO₂")
    at.run()
    at.slider(key="co2").set_value(0.45)  # never tested together with O2 0.25
    at.button(key="analyze").click()
    at.run()
    assert not at.exception
    assert any("Extrapolation" in w.value for w in at.warning)


def test_explorer_filters_to_observed_subset():
    at = run("views/explorer.py")
    at.multiselect[0].set_value(["Heptane"])
    at.run()
    shown = {m.label: m.value for m in at.metric}["Tests shown"]
    assert shown == "117"


def test_predictor_marks_stale_results_after_input_change():
    at = run("views/predictor.py")
    at.button(key="analyze").click()
    at.run()
    at.slider(key="o2").set_value(0.15)
    at.run()
    assert any("Inputs changed" in i.value for i in at.info)


def test_switching_fuel_keeps_sliders_inside_new_range():
    at = run("views/predictor.py")
    at.radio(key="fuel").set_value("Heptane")
    at.run()
    at.slider(key="d0").set_value(1.2)   # valid for heptane (min 1.1), below methanol's minimum
    at.run()
    at.radio(key="fuel").set_value("Methanol")
    at.run()
    assert not at.exception
    assert at.slider(key="d0").value >= at.slider(key="d0").min
