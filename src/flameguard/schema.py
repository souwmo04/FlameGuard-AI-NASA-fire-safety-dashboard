"""Schema of the combustion master table and the roles of its columns.

Every downstream module (features, models, dashboard) should take column lists
from here instead of hard-coding names. The most important distinction is
between PRE_TEST_FEATURES (known before ignition, allowed as model inputs) and
POST_OUTCOME_COLUMNS (measured during/after the burn, never model inputs).
"""

from __future__ import annotations

# Column order of data/processed/combustion_master.csv.
MASTER_COLUMNS: list[str] = [
    # provenance
    "source_program",
    "psi_id",
    "source_doi",
    "source_file",
    "source_row",
    "test_id",
    "flex_identifier",
    "test_datetime_gmt",
    # validation groups (not model features)
    "group_id_fill",
    "group_id_atmosphere",
    # fuel and geometry
    "fuel",
    "fuel_phase",
    "geometry",
    # ambient conditions
    "pressure_mmhg",
    "pressure_atm",
    "pressure_level",
    "x_o2",
    "x_n2",
    "x_co2",
    "x_he",
    "mole_fraction_sum",
    "p_o2_atm",
    "diluent",
    "d0_mm",
    "flow_cm_s",
    "flow_regime",
    # outcome
    "outcome_raw",
    "outcome_class",
    "y_sustained",
    # post-outcome measurements
    "d_ext_mm",
    "burn_rate_mm2_s",
    "burn_time_s",
    # quality control
    "qc_flags",
]

# Known before ignition -> allowed as model inputs.
PRE_TEST_FEATURES: list[str] = [
    "fuel",
    "pressure_atm",
    "x_o2",
    "x_co2",
    "x_he",
    "p_o2_atm",
    "diluent",
    "d0_mm",
]

# Measured during or after the burn -> NEVER model inputs (label leakage).
# d_ext_mm is the worst offender: it is mostly blank exactly when the flame
# did not extinguish, so it nearly encodes the label.
POST_OUTCOME_COLUMNS: list[str] = [
    "d_ext_mm",
    "burn_rate_mm2_s",
    "burn_time_s",
    "outcome_raw",
    "outcome_class",
]

TARGET = "y_sustained"

# Raw NASA outcome -> binary target. Disruption counts as sustained: the flame
# had not self-extinguished while fuel remained when the droplet broke up.
OUTCOME_TO_TARGET: dict[str, int] = {
    "Extinction": 0,
    "Completion": 1,
    "Disruption": 1,
}

# Quality-control flags written to the semicolon-separated `qc_flags` column.
QC_FLAGS: dict[str, str] = {
    "pressure_invalid_zero": "Recorded pressure is 0.0 mmHg (invalid record); pressure_atm left missing.",
    "pressure_level_from_group": "pressure_level taken from other tests in the same chamber fill (own pressure invalid).",
    "duplicate_identifier": "FLEX identifier and GMT time shared with another test (as printed in NASA/TP-2015-216046).",
    "approx_burn_time": "Burn time reported as approximate ('~') in the source.",
    "missing_d0": "Initial droplet diameter not reported.",
    "missing_test_time": "Test GMT time not reported.",
    "d_ext_gt_d0": "Extinction diameter exceeds initial diameter (measurement noise).",
    "d_ext_without_extinction": "Extinction diameter reported although the test did not end in extinction.",
    "extinction_d_ext_unmeasured": "Ended in extinction but extinction diameter not measured (e.g. droplet left camera view).",
    "mole_fraction_sum_off": "O2+N2+CO2+He deviates from 1 by more than 0.025.",
}
