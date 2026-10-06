"""Phase 5: assemble the modelling dataset (target, scope, row exclusions).

The master table keeps every NASA test. This module decides which tests a given
experiment uses and records why each other test was left out, so every reported
metric can state exactly what it was computed on.

Variants
--------
primary             Main model. y = 1 for Completion or Disruption, 0 for Extinction.
                    Scope 0.7-1 atm; tests with any missing model input are excluded.
exclude_disruption  Sensitivity: drop Disruption tests (y = 1 means Completion only).
                    Checks that conclusions do not hinge on labelling disruption as sustained.
impute_d0           Sensitivity: keep tests without an initial droplet diameter; the
                    model pipeline imputes it inside each training fold (plus a missing flag).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from flameguard.schema import TARGET

VARIANTS = ("primary", "exclude_disruption", "impute_d0")

# Pressure bands with enough tests to learn from. The 2-3 atm tests are a single
# CO2 series (O2 0.21, CO2 0.70); a model cannot separate pressure from CO2 there.
IN_SCOPE_PRESSURE_LEVELS = ("0.7atm", "1atm")

# Pre-test inputs the models use (see features.py for how they are encoded).
MODEL_INPUTS = ["fuel", "x_o2", "x_co2", "x_he", "pressure_atm", "d0_mm"]

GROUP_COLUMN = "group_id_atmosphere"
ID_COLUMNS = ["test_id", "flex_identifier", GROUP_COLUMN, "group_id_fill", "diluent", "pressure_level",
              "outcome_raw", "qc_flags"]


@dataclass
class ModelingData:
    """Inputs, target and grouping for one modelling variant."""

    variant: str
    X: pd.DataFrame
    y: pd.Series
    groups: pd.Series
    meta: pd.DataFrame
    excluded: pd.DataFrame = field(repr=False)

    def summary(self) -> dict:
        return {
            "variant": self.variant,
            "tests": len(self.y),
            "sustained": int(self.y.sum()),
            "extinguished": int((self.y == 0).sum()),
            "groups": int(self.groups.nunique()),
            "excluded": self.excluded["reason"].value_counts().to_dict(),
        }


def build_modeling_data(master: pd.DataFrame, variant: str = "primary") -> ModelingData:
    """Select rows and columns for a modelling variant. Never modifies values."""
    if variant not in VARIANTS:
        raise ValueError(f"Unknown variant {variant!r}; choose from {VARIANTS}")

    df = master.copy()
    df["qc_flags"] = df["qc_flags"].fillna("")
    reasons = pd.Series("", index=df.index)

    def exclude(mask: pd.Series, reason: str) -> None:
        # first matching reason wins, so each excluded test is counted once
        reasons.loc[mask & (reasons == "")] = reason

    exclude(~df["pressure_level"].isin(IN_SCOPE_PRESSURE_LEVELS), "out_of_scope_pressure_2-3atm")
    exclude(df["pressure_atm"].isna(), "missing_pressure")
    if variant != "impute_d0":
        exclude(df["d0_mm"].isna(), "missing_d0")
    if variant == "exclude_disruption":
        exclude(df["outcome_raw"] == "Disruption", "disruption_excluded_by_variant")

    other_missing = df[[c for c in MODEL_INPUTS if c != "d0_mm"]].isna().any(axis=1)
    exclude(other_missing, "missing_model_input")

    keep = reasons == ""
    excluded = df.loc[~keep, ["test_id", "flex_identifier", "fuel", "outcome_raw"]].assign(reason=reasons[~keep])
    kept = df.loc[keep].reset_index(drop=True)

    return ModelingData(
        variant=variant,
        X=kept[MODEL_INPUTS].copy(),
        y=kept[TARGET].astype(int).rename(TARGET),
        groups=kept[GROUP_COLUMN].rename(GROUP_COLUMN),
        meta=kept[ID_COLUMNS].copy(),
        excluded=excluded.reset_index(drop=True),
    )
