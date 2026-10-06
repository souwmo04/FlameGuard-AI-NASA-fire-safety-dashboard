import hashlib
import json

import numpy as np
import pandas as pd
import pytest

from flameguard.data_loader import FLEX_TABLE_PATH, RAW_FLEX_DIR, load_flex_raw
from flameguard.preprocessing import clean_flex, fill_group_id, parse_numeric, pressure_level
from flameguard.schema import MASTER_COLUMNS, POST_OUTCOME_COLUMNS, PRE_TEST_FEATURES, TARGET

requires_raw = pytest.mark.skipif(
    not FLEX_TABLE_PATH.exists(), reason="raw FLEX data not downloaded (scripts/download_flex.py)"
)


# --- unit tests --------------------------------------------------------------

def test_parse_numeric_handles_missing_and_approximate_tokens():
    values, approx = parse_numeric(pd.Series(["1.5", "", "–", "~6", ".3", "0"]), "x")
    assert values.iloc[0] == 1.5
    assert np.isnan(values.iloc[1]) and np.isnan(values.iloc[2])
    assert values.iloc[3] == 6.0 and approx.iloc[3]
    assert values.iloc[4] == 0.3
    assert values.iloc[5] == 0.0
    assert approx.sum() == 1


def test_parse_numeric_rejects_unknown_tokens():
    with pytest.raises(ValueError, match="Unparseable"):
        parse_numeric(pd.Series(["1.0", "n/a"]), "x")


@pytest.mark.parametrize(
    "identifier, group",
    [("C10M101", "C10"), ("H15H201", "H15"), ("N01H202", "N01"),
     ("193F001", "TP193"), ("189R002", "TP189"), ("20CAL08", "CAL")],
)
def test_fill_group_id(identifier, group):
    assert fill_group_id(identifier) == group


def test_fill_group_id_rejects_unknown_pattern():
    with pytest.raises(ValueError):
        fill_group_id("XYZ")


def test_pressure_level_bands():
    assert pressure_level(0.70) == "0.7atm"
    assert pressure_level(1.01) == "1atm"
    assert pressure_level(2.73) == "2-3atm"
    assert pressure_level(np.nan) is None


def test_loader_rejects_changed_header(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n1,2\n", encoding="cp1252")
    with pytest.raises(ValueError, match="Unexpected FLEX header"):
        load_flex_raw(bad)


# --- integration tests on the real NASA file ----------------------------------

@pytest.fixture(scope="module")
def master():
    return clean_flex(load_flex_raw())


@requires_raw
def test_raw_file_matches_manifest_checksum():
    manifest = json.loads((RAW_FLEX_DIR / "MANIFEST.json").read_text(encoding="utf-8"))
    entry = next(f for f in manifest["files"] if f["path"].endswith(FLEX_TABLE_PATH.name))
    assert hashlib.sha256(FLEX_TABLE_PATH.read_bytes()).hexdigest() == entry["sha256"]


@requires_raw
def test_master_shape_and_schema(master):
    assert list(master.columns) == MASTER_COLUMNS
    assert len(master) == 274
    assert master["test_id"].is_unique


@requires_raw
def test_outcomes_and_target(master):
    assert master["outcome_raw"].value_counts().to_dict() == {
        "Extinction": 186, "Disruption": 61, "Completion": 27}
    assert (master.loc[master["outcome_raw"] == "Extinction", TARGET] == 0).all()
    assert (master.loc[master["outcome_raw"] != "Extinction", TARGET] == 1).all()


@requires_raw
def test_invalid_pressure_left_missing_and_flagged(master):
    row = master.set_index("test_id").loc[114]
    assert row["flex_identifier"] == "C11M201"
    assert np.isnan(row["pressure_atm"]) and np.isnan(row["p_o2_atm"])
    assert "pressure_invalid_zero" in row["qc_flags"]
    assert row["pressure_level"] == "0.7atm"  # from its chamber-fill siblings, for grouping only


@requires_raw
def test_duplicate_identifier_rows_kept_and_flagged(master):
    dups = master[master["qc_flags"].str.contains("duplicate_identifier")]
    assert sorted(dups["test_id"]) == [70, 73]


@requires_raw
def test_values_not_invented(master):
    raw = load_flex_raw()
    # every blank / dash in the source stays missing
    for raw_col, col in [("d0_mm", "d0_mm"), ("d_ext_mm", "d_ext_mm"), ("burn_time_s", "burn_time_s")]:
        blank = raw[raw_col].isin(["", "–"]).to_numpy()
        assert master.loc[blank, col].isna().all()
    assert master["flow_cm_s"].isna().all()
    # no renormalisation of NASA's mole fractions
    assert master["x_o2"].tolist() == pd.to_numeric(raw["x_o2"]).tolist()


@requires_raw
def test_composition_and_diluent(master):
    assert master["mole_fraction_sum"].between(0.975, 1.025).all()
    assert (master.loc[master["diluent"] == "He", "x_he"] > 0).all()
    assert (master.loc[master["diluent"] == "CO2", "x_co2"] > 0).all()
    assert ((master["x_co2"] > 0) & (master["x_he"] > 0)).sum() == 0


@requires_raw
def test_dates_parsed_in_test_period(master):
    dates = pd.to_datetime(master["test_datetime_gmt"].str[:10])
    assert dates.min() == pd.Timestamp("2009-03-05")
    assert dates.max() == pd.Timestamp("2011-12-08")


def test_feature_lists_do_not_leak_outcome():
    assert not set(PRE_TEST_FEATURES) & set(POST_OUTCOME_COLUMNS)
    assert TARGET not in PRE_TEST_FEATURES
    assert set(PRE_TEST_FEATURES) <= set(MASTER_COLUMNS)
