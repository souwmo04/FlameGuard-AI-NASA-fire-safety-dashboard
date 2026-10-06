import numpy as np
import pandas as pd
import pytest

from flameguard.data_loader import FLEX_TABLE_PATH
from flameguard.dataset import MODEL_INPUTS, build_modeling_data
from flameguard.features import FEATURE_SETS as FEATURE_SETS_FOR_TEST, FlexFeatures, make_preprocessor, monotone_constraints
from flameguard.schema import POST_OUTCOME_COLUMNS, TARGET
from flameguard.validation import Split, check_splits, repeated_group_kfold, stress_splits

MASTER = FLEX_TABLE_PATH.parents[2] / "processed" / "combustion_master.csv"
requires_master = pytest.mark.skipif(not MASTER.exists(), reason="run scripts/build_master.py first")


@pytest.fixture(scope="module")
def master():
    return pd.read_csv(MASTER)


def toy_inputs():
    return pd.DataFrame({
        "fuel": ["Heptane", "Methanol", "Heptane", "Methanol"],
        "x_o2": [0.21, 0.18, 0.15, 0.30],
        "x_co2": [0.0, 0.2, 0.0, 0.0],
        "x_he": [0.0, 0.0, 0.3, 0.0],
        "pressure_atm": [1.0, 0.7, 1.0, 0.7],
        "d0_mm": [2.0, 3.0, 4.0, np.nan],
    })


# --- features ------------------------------------------------------------------

def test_flex_features_encoding_and_interaction():
    f = FlexFeatures(interaction=True).fit(toy_inputs().iloc[:3])
    out = f.transform(toy_inputs())
    assert list(out.columns) == ["is_heptane", "x_o2", "x_co2", "x_he", "pressure_atm", "d0_mm", "heptane_x_d0"]
    assert out["is_heptane"].tolist() == [1, 0, 1, 0]
    assert f.d0_center_ == pytest.approx(3.0)            # learned from the fitted rows only
    assert out["heptane_x_d0"].tolist() == [-1.0, 0.0, 1.0, 0.0]  # methanol and missing d0 -> 0


def test_with_po2_feature_set():
    out = FlexFeatures(feature_set="with_po2").fit_transform(toy_inputs())
    assert out["p_o2_atm"].iloc[1] == pytest.approx(0.18 * 0.7)


def test_unknown_fuel_rejected():
    bad = toy_inputs().assign(fuel=["Heptane", "Decane", "Heptane", "Methanol"])
    with pytest.raises(ValueError, match="Unknown fuels"):
        FlexFeatures().fit(bad)


def test_preprocessor_statistics_come_from_training_rows_only():
    X = toy_inputs().iloc[:3]
    train, test = X.iloc[:2], X.iloc[2:]
    pipe = make_preprocessor("linear").fit(train)
    scaler = pipe.named_steps["scale"]
    assert scaler.mean_[list(pipe.named_steps["features"].feature_names_out_).index("x_o2")] == pytest.approx(0.195)
    pipe.transform(test)  # must not refit
    assert scaler.n_samples_seen_ == 2


def test_impute_variant_adds_single_missing_indicator():
    out = make_preprocessor("linear", impute=True).fit_transform(toy_inputs())
    assert [c for c in out.columns if c.startswith("missingindicator")] == ["missingindicator_d0_mm"]
    assert not out.isna().any().any()


def test_monotone_constraints_only_on_oxygen():
    names = ["is_heptane", "x_o2", "x_co2", "x_he", "pressure_atm", "d0_mm"]
    assert monotone_constraints(names) == (0, 1, 0, 0, 0, 0)


# --- dataset (Phase 5) ---------------------------------------------------------

@requires_master
def test_primary_dataset_scope(master):
    d = build_modeling_data(master, "primary")
    assert d.summary()["tests"] == 252 and d.summary()["sustained"] == 80
    assert not d.X.isna().any().any()
    assert (d.meta["pressure_level"] != "2-3atm").all()
    assert len(d.excluded) == 274 - 252
    assert set(d.X.columns) == set(MODEL_INPUTS)


@requires_master
def test_no_post_outcome_or_target_columns_in_inputs(master):
    for variant in ["primary", "exclude_disruption", "impute_d0"]:
        d = build_modeling_data(master, variant)
        assert not set(d.X.columns) & set(POST_OUTCOME_COLUMNS)
        assert TARGET not in d.X.columns


@requires_master
def test_variants(master):
    ex = build_modeling_data(master, "exclude_disruption")
    assert (ex.meta["outcome_raw"] != "Disruption").all()
    imp = build_modeling_data(master, "impute_d0")
    assert imp.X["d0_mm"].isna().sum() == 12
    with pytest.raises(ValueError):
        build_modeling_data(master, "nope")


# --- validation (Phase 6) ------------------------------------------------------

@requires_master
def test_repeated_group_kfold_has_no_leakage(master):
    d = build_modeling_data(master, "primary")
    splits = repeated_group_kfold(d.y, d.groups, n_splits=5, n_repeats=3)
    assert len(splits) == 15
    for s in splits:
        assert not set(d.groups.iloc[s.train]) & set(d.groups.iloc[s.test])


@requires_master
def test_stress_splits_hold_out_conditions(master):
    d = build_modeling_data(master, "primary")
    splits = {s.name: s for s in stress_splits(d.meta)}
    check_splits(list(splits.values()), d.y, d.groups)
    assert (d.meta["diluent"].iloc[splits["leave_out_He"].test] == "He").all()
    assert (d.meta["diluent"].iloc[splits["leave_out_He"].train] != "He").all()
    assert (d.meta["pressure_level"].iloc[splits["train_1atm_test_0.7atm"].train] == "1atm").all()


def test_check_splits_detects_group_leak_and_single_class():
    y = pd.Series([0, 1, 0, 1])
    groups = pd.Series(["a", "a", "b", "b"])
    with pytest.raises(ValueError, match="groups in both"):
        check_splits([Split("bad", np.array([0, 2]), np.array([1, 3]))], y, groups)
    with pytest.raises(ValueError, match="only one class"):
        check_splits([Split("bad", np.array([1, 3]), np.array([0, 2]))], pd.Series([0, 1, 0, 1]),
                     pd.Series(["a", "b", "c", "d"]))


# --- Phase 8 additions -----------------------------------------------------------

@pytest.mark.parametrize("feature_set, expected", [
    ("no_pressure", ["is_heptane", "x_o2", "x_co2", "x_he", "d0_mm"]),
    ("no_suppressant", ["is_heptane", "x_o2", "pressure_atm", "d0_mm"]),
    ("o2_fuel", ["is_heptane", "x_o2"]),
])
def test_ablation_feature_sets(feature_set, expected):
    out = FlexFeatures(feature_set=feature_set).fit_transform(toy_inputs())
    assert list(out.columns) == expected


def test_interaction_requires_fuel_and_size():
    with pytest.raises(ValueError, match="interaction needs"):
        FlexFeatures(feature_set="no_d0", interaction=True).fit(toy_inputs())
    assert "heptane_x_d0" not in make_preprocessor("linear", interaction=False).fit_transform(toy_inputs().dropna())


@requires_master
def test_exclude_anomalies_variant(master):
    d = build_modeling_data(master, "exclude_anomalies")
    assert not d.meta["test_id"].isin([70, 73]).any()
    assert d.summary()["tests"] == 250


def test_final_model_does_not_use_pressure():
    from flameguard.model import FINAL_CANDIDATES, FINAL_FEATURE_SET

    assert "pressure_atm" not in FEATURE_SETS_FOR_TEST[FINAL_FEATURE_SET]
    X = toy_inputs().dropna()
    for name, factory in FINAL_CANDIDATES.items():
        est = factory()
        pipe = est.estimator if hasattr(est, "estimator") else est
        names = list(pipe.named_steps["pre"].fit(X).get_feature_names_out())
        assert "pressure_atm" not in names, name
