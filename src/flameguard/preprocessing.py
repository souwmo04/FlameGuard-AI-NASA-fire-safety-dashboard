"""Clean the raw FLEX table into the combustion master schema.

Principles:
  * Never invent values. Unparseable or invalid entries become missing (NaN)
    and are recorded in `qc_flags`; nothing is imputed here. Any imputation
    belongs in the model pipeline, fitted inside cross-validation.
  * Never drop rows silently. Anomalous tests stay in the table, flagged, so
    the modelling phase can decide (and document) whether to exclude them.
  * Fail loudly on anything unexpected (new outcome labels, unknown tokens,
    unrecognised identifiers) rather than guessing.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from flameguard.data_loader import FLEX_TABLE_PATH
from flameguard.schema import MASTER_COLUMNS, OUTCOME_TO_TARGET, QC_FLAGS

MMHG_PER_ATM = 760.0

# Tokens the NASA table uses for "no value": blank, en dash (cp1252 0x96), dashes.
MISSING_TOKENS = {"", "–", "—", "-"}
_NUMBER = re.compile(r"^-?\d+(\.\d+)?$|^-?\.\d+$")

FLEX_PROVENANCE = {
    "source_program": "FLEX",
    "psi_id": "PSI-69",
    "source_doi": "10.60555/mbq8-0451",
    "source_file": FLEX_TABLE_PATH.name,
    "fuel_phase": "liquid_droplet",
    "geometry": "spherical_droplet",
    # FLEX burned droplets in a nominally quiescent chamber: there is no
    # imposed airflow and none is recorded, so flow speed stays missing (not 0).
    "flow_regime": "quiescent_nominal",
}

MOLE_FRACTION_TOLERANCE = 0.025


def parse_numeric(values: pd.Series, column: str) -> tuple[pd.Series, pd.Series]:
    """Parse raw strings to floats.

    Returns (numbers, is_approximate). Missing tokens become NaN; values written
    as '~6' parse to 6.0 with is_approximate=True.

    Raises:
        ValueError: on any token that is neither a number, '~number', nor a
        known missing marker.
    """
    text = values.astype(str).str.strip()
    is_missing = text.isin(MISSING_TOKENS)
    is_approx = text.str.startswith("~")
    numeric_text = text.str.lstrip("~").str.strip()

    bad = ~is_missing & ~numeric_text.str.match(_NUMBER)
    if bad.any():
        examples = text[bad].unique()[:5].tolist()
        raise ValueError(f"Unparseable values in column '{column}': {examples}")

    numbers = pd.to_numeric(numeric_text.where(~is_missing), errors="coerce").astype(float)
    return numbers, is_approx & ~is_missing


def fill_group_id(identifier: str) -> str:
    """Group tests that share a chamber-atmosphere setpoint, from the CIR identifier.

    Identifier patterns in PSI-69:
      C10M101 / H05H201 / N01M102 -> series letter (C=CO2, H=He, N=N2 dilution)
                                     + 2-digit setpoint -> 'C10'
      193F001 / 189R002           -> 3-digit test point            -> 'TP193'
      20CAL08                     -> 2009 calibration tests in air -> 'CAL'
    """
    if m := re.match(r"^([CHN])(\d{2})[MH]\d+$", identifier):
        return f"{m.group(1)}{m.group(2)}"
    if m := re.match(r"^(\d{3})[FR]\d+$", identifier):
        return f"TP{m.group(1)}"
    if re.match(r"^\d{2}CAL\d+$", identifier):
        return "CAL"
    raise ValueError(f"Unrecognised FLEX identifier pattern: {identifier!r}")


def pressure_level(pressure_atm: float) -> str | None:
    """Coarse pressure band. FLEX ran at ~0.7 atm, ~1 atm and 2-3 atm."""
    if pd.isna(pressure_atm):
        return None
    if pressure_atm < 0.85:
        return "0.7atm"
    if pressure_atm < 1.5:
        return "1atm"
    return "2-3atm"


def _diluent(x_co2: float, x_he: float) -> str:
    if x_co2 > 0 and x_he > 0:
        raise ValueError("Test with both CO2 and He added; diluent rule needs revisiting")
    if x_he > 0:
        return "He"
    if x_co2 > 0:
        return "CO2"
    return "N2"


def _test_datetime(date: str, time: str) -> str:
    # The table mixes 4-digit (3/5/2009) and 2-digit (10/24/09) years.
    fmt = "%m/%d/%Y" if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", date) else "%m/%d/%y"
    day = pd.to_datetime(date, format=fmt)
    if not time:
        return day.strftime("%Y-%m-%d")
    clock = pd.to_datetime(time, format="%H:%M:%S")
    return f"{day:%Y-%m-%d}T{clock:%H:%M:%S}Z"


def clean_flex(raw: pd.DataFrame) -> pd.DataFrame:
    """Transform the raw FLEX table (from data_loader.load_flex_raw) to the master schema."""
    flags: list[list[str]] = [[] for _ in range(len(raw))]

    def flag(mask: pd.Series, name: str) -> None:
        assert name in QC_FLAGS, name
        for i in np.flatnonzero(mask.to_numpy()):
            flags[i].append(name)

    df = pd.DataFrame(index=raw.index)
    for key, value in FLEX_PROVENANCE.items():
        df[key] = value
    df["source_row"] = raw["source_row"].astype(int)

    # --- identifiers and time ------------------------------------------------
    df["test_id"] = raw["test_no"].astype(int)
    if df["test_id"].duplicated().any():
        raise ValueError("Duplicate FLEX test numbers")
    df["flex_identifier"] = raw["flex_identifier"]
    df["test_datetime_gmt"] = [_test_datetime(d, t) for d, t in zip(raw["test_date"], raw["test_gmt"])]
    flag(raw["test_gmt"] == "", "missing_test_time")

    dup_key = raw["flex_identifier"] + "|" + raw["test_date"] + "|" + raw["test_gmt"]
    flag(dup_key.duplicated(keep=False), "duplicate_identifier")

    # --- fuel ----------------------------------------------------------------
    df["fuel"] = raw["fuel"]
    unknown_fuels = set(df["fuel"]) - {"Methanol", "Heptane"}
    if unknown_fuels:
        raise ValueError(f"Unexpected fuels: {unknown_fuels}")

    # --- numeric columns -----------------------------------------------------
    num: dict[str, pd.Series] = {}
    for col in ["pressure_mmhg", "x_o2", "x_n2", "x_co2", "x_he", "d0_mm",
                "d_ext_mm", "burn_rate_mm2_s", "burn_time_s"]:
        num[col], approx = parse_numeric(raw[col], col)
        if col == "burn_time_s":
            flag(approx, "approx_burn_time")
        elif approx.any():
            raise ValueError(f"Unexpected approximate values in '{col}'")

    # Pressure: 0.0 mmHg is an invalid record, not vacuum.
    invalid_p = num["pressure_mmhg"] <= 0
    flag(invalid_p, "pressure_invalid_zero")
    df["pressure_mmhg"] = num["pressure_mmhg"].mask(invalid_p)
    df["pressure_atm"] = (df["pressure_mmhg"] / MMHG_PER_ATM).round(4)

    # Composition
    for col in ["x_o2", "x_n2", "x_co2", "x_he"]:
        df[col] = num[col]
    df["mole_fraction_sum"] = df[["x_o2", "x_n2", "x_co2", "x_he"]].sum(axis=1).round(3)
    flag((df["mole_fraction_sum"] - 1).abs() > MOLE_FRACTION_TOLERANCE, "mole_fraction_sum_off")
    df["p_o2_atm"] = (df["x_o2"] * df["pressure_atm"]).round(4)
    df["diluent"] = [_diluent(c, h) for c, h in zip(df["x_co2"], df["x_he"])]

    # Droplet and flow
    df["d0_mm"] = num["d0_mm"]
    flag(df["d0_mm"].isna(), "missing_d0")
    df["flow_cm_s"] = np.nan

    # --- validation groups ---------------------------------------------------
    df["group_id_fill"] = raw["flex_identifier"].map(fill_group_id)
    levels = df["pressure_atm"].map(pressure_level)
    needs_level = levels.isna()
    if needs_level.any():
        # Pressure band from the other tests in the same chamber fill. This is
        # only used to form validation groups, never as a model input.
        group_levels = (
            pd.DataFrame({"g": df["group_id_fill"], "lvl": levels})
            .dropna()
            .groupby("g")["lvl"]
            .agg(lambda s: s.mode().iloc[0] if s.nunique() == 1 else None)
        )
        levels = levels.fillna(df["group_id_fill"].map(group_levels))
        flag(needs_level & levels.notna(), "pressure_level_from_group")
    df["pressure_level"] = levels
    df["group_id_atmosphere"] = [
        f"{lvl}|O2={o2:.2f}|CO2={co2:.2f}|He={he:.2f}"
        for lvl, o2, co2, he in zip(df["pressure_level"], df["x_o2"], df["x_co2"], df["x_he"])
    ]

    # --- outcome -------------------------------------------------------------
    df["outcome_raw"] = raw["test_end"]
    unknown = set(df["outcome_raw"]) - set(OUTCOME_TO_TARGET)
    if unknown:
        raise ValueError(f"Unexpected 'Test end' values: {unknown}")
    df["outcome_class"] = df["outcome_raw"].str.lower()
    df["y_sustained"] = df["outcome_raw"].map(OUTCOME_TO_TARGET).astype("int8")

    # --- post-outcome measurements -------------------------------------------
    df["d_ext_mm"] = num["d_ext_mm"]
    df["burn_rate_mm2_s"] = num["burn_rate_mm2_s"]
    df["burn_time_s"] = num["burn_time_s"]
    is_ext = df["outcome_raw"] == "Extinction"
    flag(df["d_ext_mm"] > df["d0_mm"], "d_ext_gt_d0")
    flag(~is_ext & df["d_ext_mm"].notna(), "d_ext_without_extinction")
    flag(is_ext & df["d_ext_mm"].isna(), "extinction_d_ext_unmeasured")

    df["qc_flags"] = [";".join(f) for f in flags]
    return validate_master(df[MASTER_COLUMNS].reset_index(drop=True))


def validate_master(df: pd.DataFrame) -> pd.DataFrame:
    """Check invariants of the master table; raise ValueError listing every violation."""
    problems: list[str] = []

    if list(df.columns) != MASTER_COLUMNS:
        problems.append("columns do not match schema.MASTER_COLUMNS")
    if df["test_id"].duplicated().any():
        problems.append("duplicate test_id")
    if not df["y_sustained"].isin([0, 1]).all():
        problems.append("y_sustained not binary")
    for col in ["x_o2", "x_n2", "x_co2", "x_he"]:
        if not df[col].between(0, 1).all():
            problems.append(f"{col} outside [0, 1] or missing")
    if (df["pressure_atm"].dropna() <= 0).any():
        problems.append("non-positive pressure_atm")
    if (df["d0_mm"].dropna() <= 0).any():
        problems.append("non-positive d0_mm")
    for col in ["group_id_fill", "group_id_atmosphere", "pressure_level", "diluent"]:
        if df[col].isna().any():
            problems.append(f"missing {col}")
    unknown_flags = {f for cell in df["qc_flags"] for f in cell.split(";") if f} - set(QC_FLAGS)
    if unknown_flags:
        problems.append(f"unknown qc flags {unknown_flags}")

    if problems:
        raise ValueError("Master table validation failed: " + "; ".join(problems))
    return df


def qc_summary(df: pd.DataFrame) -> dict:
    """Counts used in the build log and the data card."""
    flag_counts = {name: int(df["qc_flags"].str.split(";").apply(lambda f: name in f).sum())
                   for name in QC_FLAGS}
    return {
        "rows": len(df),
        "outcome_counts": df["outcome_raw"].value_counts().to_dict(),
        "y_sustained_counts": {str(k): int(v) for k, v in df["y_sustained"].value_counts().sort_index().items()},
        "fuel_counts": df["fuel"].value_counts().to_dict(),
        "diluent_counts": df["diluent"].value_counts().to_dict(),
        "pressure_level_counts": df["pressure_level"].value_counts().to_dict(),
        "n_group_id_fill": int(df["group_id_fill"].nunique()),
        "n_group_id_atmosphere": int(df["group_id_atmosphere"].nunique()),
        "missing_values": {c: int(n) for c, n in df.isna().sum().items() if n and c != "flow_cm_s"},
        "qc_flag_counts": {k: v for k, v in flag_counts.items() if v},
    }
