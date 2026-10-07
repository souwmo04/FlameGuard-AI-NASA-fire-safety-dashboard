"""HTTP-level tests of the FlameGuard API (FastAPI TestClient, real data and model)."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

METHANOL_AIR = {"fuel": "Methanol", "oxygen_percent": 21, "suppressant": "none", "suppressant_percent": 0,
                "droplet_diameter_mm": 3.0}


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app()) as c:
        yield c


# --- system ------------------------------------------------------------------------

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["training_tests"] == 252
    assert len(body["data_sha256"]) == 64


def test_stats_are_real_counts(client):
    s = client.get("/api/stats").json()
    assert s["experiments"] == {"total": 274, "in_model_scope": 252, "extinction": 186, "completion": 27,
                                "disruption": 61, "sustained": 88}
    assert s["fuels"] == ["Heptane", "Methanol"]
    assert s["nasa_investigations"] == 1
    assert 0.9 < s["model"]["roc_auc"] < 0.95
    assert s["date_start"] == "2009-03-05" and s["date_end"] == "2011-12-08"


def test_sources_have_doi_for_dataset(client):
    sources = {s["id"]: s for s in client.get("/api/sources").json()}
    assert sources["psi-69"]["doi"] == "10.60555/mbq8-0451"
    assert sources["psi-69"]["license"] == "CC0-1.0"


def test_domain_ranges(client):
    d = client.get("/api/domain").json()
    assert d["fuels"]["Methanol"]["oxygen_percent"] == [12.0, 34.0]
    assert d["pressure_scope_atm"] == [0.7, 1.0]


def test_model_card(client):
    m = client.get("/api/model").json()
    names = {x["name"] for x in m["metrics"]}
    assert {"ROC-AUC", "Brier score", "Recall at alert threshold"} <= names
    assert [b["level"] for b in m["bands"]] == ["LOW", "ELEVATED", "HIGH"]
    assert sum(b["tests"] for b in m["bands"]) == 252
    assert abs(sum(g["share"] for g in m["global_importance"]) - 1) < 1e-3
    assert 151 in m["consistently_missed_test_ids"]


# --- experiments ---------------------------------------------------------------------

def test_list_filters_and_pagination(client):
    r = client.get("/api/experiments", params={"fuel": "Heptane", "limit": 5}).json()
    assert r["total"] == 117 and len(r["items"]) == 5
    assert all(e["fuel"] == "Heptane" and e["provenance"] == "observed" for e in r["items"])
    he = client.get("/api/experiments", params={"suppressant": "He", "limit": 300}).json()
    assert he["total"] == 50 and all(e["he_percent"] > 0 for e in he["items"])


def test_sort_by_risk_and_scope(client):
    r = client.get("/api/experiments", params={"sort": "-risk", "limit": 10}).json()["items"]
    risks = [e["prediction"]["fire_risk"] for e in r]
    assert risks == sorted(risks, reverse=True)
    out = client.get("/api/experiments", params={"in_model_scope": False, "limit": 300}).json()
    assert out["total"] == 22 and all(e["prediction"] is None for e in out["items"])


def test_experiment_detail(client):
    e = client.get("/api/experiments/151").json()
    assert e["flex_identifier"] == "C03M101" and e["outcome"] == "Completion"
    assert e["prediction"]["provenance"] == "prediction" and e["prediction"]["risk_level"] == "LOW"
    assert e["source"]["doi"] == "10.60555/mbq8-0451"
    out = client.get("/api/experiments/10").json()
    assert out["in_model_scope"] is False and "2-3 atm" in out["notes"][0]
    assert client.get("/api/experiments/999").status_code == 404


def test_missing_values_are_null_not_nan(client):
    e = client.get("/api/experiments/9").json()  # NASA reported no droplet diameter
    assert e["droplet_diameter_mm"] is None


# --- prediction ------------------------------------------------------------------------

def test_predict_matches_model_and_is_explained(client):
    p = client.post("/api/predict", json=METHANOL_AIR).json()
    assert p["fire_risk"] == pytest.approx(28.7, abs=0.1)
    assert p["risk_level"] == "ELEVATED"
    assert p["sustained_probability"] + p["extinction_probability"] == pytest.approx(1)
    total = p["explanation"]["base_value"] + sum(c["impact"] for c in p["explanation"]["contributions"])
    assert total == pytest.approx(p["fire_risk"], abs=0.1)
    assert {c["key"] for c in p["explanation"]["contributions"]} == {"fuel", "atmosphere", "droplet_size"}
    assert p["evidence"]["supported_by_data"] is True and len(p["evidence"]["nearest_experiment_ids"]) == 3
    text = p["interpretation"]["text"]
    assert "not a NASA measurement" in text and "28%" in text
    assert p["interpretation"]["provenance"] == "interpretation"
    points = p["interpretation"]["points"]
    assert [pt["kind"] for pt in points] == ["summary", "drivers", "evidence", "disclaimer"]
    assert " ".join(pt["text"] for pt in points) == text


def test_predict_flags_untested_combination(client):
    body = {**METHANOL_AIR, "oxygen_percent": 25, "suppressant": "CO2", "suppressant_percent": 45}
    p = client.post("/api/predict", json=body).json()
    assert p["evidence"]["supported_by_data"] is False
    assert p["evidence"]["warnings"]
    assert "extrapolation" in p["interpretation"]["text"]
    assert "cannot separate the effect of the suppressant" in p["interpretation"]["text"]
    summary = p["interpretation"]["points"][0]["text"]
    risk = summary.split("Fire Risk ")[1].split("/100")[0]
    assert f"a {risk}% probability" in summary                        # one rounding for score and probability
    kinds = {pt["kind"] for pt in p["interpretation"]["points"]}
    assert {"extrapolation", "suppressant"} <= kinds


@pytest.mark.parametrize("bad", [
    {**METHANOL_AIR, "suppressant_percent": 5},                       # amount without suppressant
    {**METHANOL_AIR, "fuel": "Decane"},                                # untested fuel
    {**METHANOL_AIR, "oxygen_percent": 70, "suppressant": "CO2", "suppressant_percent": 40},  # > 100 %
    {**METHANOL_AIR, "droplet_diameter_mm": 0},
])
def test_predict_rejects_invalid_conditions(client, bad):
    assert client.post("/api/predict", json=bad).status_code == 422


def test_predict_monotone_in_oxygen(client):
    risks = [client.post("/api/predict", json={**METHANOL_AIR, "oxygen_percent": o}).json()["fire_risk"]
             for o in (14, 18, 22, 26, 30)]
    assert risks == sorted(risks)


# --- what-if ---------------------------------------------------------------------------

def test_what_if_path_and_sweep(client):
    body = {"scenario_a": METHANOL_AIR,
            "scenario_b": {**METHANOL_AIR, "oxygen_percent": 18, "suppressant": "CO2", "suppressant_percent": 10},
            "sweep": "oxygen", "sweep_points": 15}
    w = client.post("/api/what-if", json=body).json()
    assert [s["step"] for s in w["path"]] == ["baseline", "oxygen", "suppressant"]
    assert [s["change"] for s in w["path"][1:]] == ["O₂ 21% → O₂ 18%", "no suppressant → CO₂ 10%"]
    assert w["delta"] == pytest.approx(w["b"]["fire_risk"] - w["a"]["fire_risk"], abs=0.11)
    assert sum(s["delta"] for s in w["path"]) == pytest.approx(w["delta"], abs=0.2)
    assert len(w["sweep"]["points"]) == 15 and w["sweep"]["unit"] == "% O₂"
    assert any("cannot separate" in n for n in w["notes"])


def test_what_if_without_sweep(client):
    w = client.post("/api/what-if", json={"scenario_a": METHANOL_AIR, "scenario_b": METHANOL_AIR, "sweep": None}).json()
    assert w["sweep"] is None and len(w["path"]) == 1 and w["delta"] == 0


# --- ranking, suppressants, similar --------------------------------------------------------

def test_ranking_orders_and_provenance(client):
    top = client.get("/api/ranking", params={"by": "risk", "limit": 5}).json()
    vals = [i["value"] for i in top["items"]]
    assert vals == sorted(vals, reverse=True) and top["provenance"] == "prediction"
    assert [i["rank"] for i in top["items"]] == [1, 2, 3, 4, 5]
    burn = client.get("/api/ranking", params={"by": "burn_time", "limit": 3}).json()
    assert burn["provenance"] == "observed" and burn["items"][0]["value"] == 39.2
    ext = client.get("/api/ranking", params={"by": "extinction", "fuel": "Methanol", "limit": 3}).json()
    assert all(i["experiment"]["fuel"] == "Methanol" for i in ext["items"])


def test_condition_ranking(client):
    r = client.get("/api/ranking/conditions", params={"limit": 50}).json()
    rates = [i["observed_rate"] for i in r["items"]]
    assert rates == sorted(rates, reverse=True) and r["provenance"] == "observed"
    assert all(i["tests"] >= 3 and i["ci_low"] <= i["observed_rate"] <= i["ci_high"] for i in r["items"])


def test_suppressants_conclusion_is_data_driven(client):
    s = client.get("/api/suppressants").json()
    assert len(s["estimates"]) == 12 and sum(e["estimable"] for e in s["estimates"]) == 6
    assert len(s["comparisons"]) == 1 and s["comparisons"][0]["intervals_overlap"] is True
    assert "do not establish a ranking" in s["conclusion"]
    assert any("not NASA's limiting oxygen index" in c for c in s["caveats"])


def test_similar_experiments(client):
    r = client.post("/api/similar-experiments", json={**METHANOL_AIR, "k": 4}).json()
    sims = [i["similarity"] for i in r["items"]]
    assert len(sims) == 4 and sims == sorted(sims, reverse=True) and all(0 < s <= 100 for s in sims)
    assert all(i["experiment"]["fuel"] == "Methanol" for i in r["items"])


def test_cors_allows_frontend_origin(client):
    r = client.options("/api/stats", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"
