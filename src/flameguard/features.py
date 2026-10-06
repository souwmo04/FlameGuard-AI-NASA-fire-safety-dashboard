"""Phase 6: feature engineering as scikit-learn transformers.

Everything that learns from data (scaling means, imputation medians, the
centring of the interaction term) lives inside a Pipeline, so it is fitted on
the training fold only and never sees the test fold.

Encoded features
----------------
is_heptane      fuel indicator (0 = methanol, 1 = n-heptane)
x_o2            O2 mole fraction
x_co2, x_he     added suppressant mole fractions (0 when not added)
pressure_atm    absolute chamber pressure
d0_mm           initial droplet diameter
heptane_x_d0    (linear models only) is_heptane x centred d0; EDA showed the droplet-size
                effect has opposite signs for the two fuels, which a linear model cannot
                represent without this term. Trees learn the interaction themselves.

Deliberately NOT used
---------------------
x_n2            O2 + N2 + CO2 + He = 1, so N2 is redundant and would make the linear model
                ill-conditioned.
p_o2_atm        = x_o2 x pressure_atm; available as an ablation ("with_po2") only.
diluent         fully implied by x_co2 > 0 / x_he > 0.
post-outcome    d_ext_mm, burn_rate_mm2_s, burn_time_s (label leakage; see schema.py).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

NUMERIC_FEATURES = ["x_o2", "x_co2", "x_he", "pressure_atm", "d0_mm"]
FEATURE_SETS = {
    "base": ["is_heptane", *NUMERIC_FEATURES],
    "with_po2": ["is_heptane", *NUMERIC_FEATURES, "p_o2_atm"],
}

# Physically motivated sign constraints for tree boosting (XGBoost monotone_constraints).
# Only O2 is constrained: at fixed everything else, more oxygen must not lower the
# predicted chance of sustained burning. Suppressant effects are not constrained
# because O2 and suppressant were varied together (EDA finding 4), so the data
# cannot pin their separate signs and we do not want to impose them.
MONOTONE_SIGNS = {"x_o2": 1}


class FlexFeatures(BaseEstimator, TransformerMixin):
    """Turn MODEL_INPUTS columns into the numeric feature frame.

    Parameters
    ----------
    feature_set : "base" or "with_po2"
    interaction : add heptane_x_d0 (for linear models)
    """

    def __init__(self, feature_set: str = "base", interaction: bool = False):
        self.feature_set = feature_set
        self.interaction = interaction

    def fit(self, X: pd.DataFrame, y=None):
        if self.feature_set not in FEATURE_SETS:
            raise ValueError(f"Unknown feature_set {self.feature_set!r}")
        unknown = set(X["fuel"].dropna()) - {"Methanol", "Heptane"}
        if unknown:
            raise ValueError(f"Unknown fuels: {unknown}")
        # centre for the interaction is learned from the training fold only
        self.d0_center_ = float(np.nanmean(X["d0_mm"]))
        self.feature_names_out_ = self._names()
        return self

    def _names(self) -> list[str]:
        names = list(FEATURE_SETS[self.feature_set])
        if self.interaction:
            names.append("heptane_x_d0")
        return names

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        out = pd.DataFrame(index=X.index)
        out["is_heptane"] = (X["fuel"] == "Heptane").astype(float)
        for col in NUMERIC_FEATURES:
            out[col] = X[col].astype(float)
        if self.feature_set == "with_po2":
            out["p_o2_atm"] = out["x_o2"] * out["pressure_atm"]
        if self.interaction:
            # Unknown d0 (impute_d0 variant only) -> no size adjustment (0 = training-fold mean).
            # d0_mm itself stays NaN for the downstream imputer, which adds the single
            # missing-indicator column.
            out["heptane_x_d0"] = (out["is_heptane"] * (out["d0_mm"] - self.d0_center_)).fillna(0.0)
        return out[self.feature_names_out_]

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.feature_names_out_, dtype=object)


def make_preprocessor(model_kind: str, feature_set: str = "base", impute: bool = False) -> Pipeline:
    """Preprocessing pipeline for a model family.

    model_kind:
      "linear" - interaction term + standard scaling (logistic regression)
      "tree"   - raw features, no scaling (random forest, XGBoost)
    impute: median-impute missing values with missing-indicator columns, fitted per fold
            (only needed for the impute_d0 variant).
    """
    if model_kind not in {"linear", "tree"}:
        raise ValueError("model_kind must be 'linear' or 'tree'")
    steps: list[tuple[str, object]] = [
        ("features", FlexFeatures(feature_set=feature_set, interaction=model_kind == "linear")),
    ]
    if impute:
        steps.append(("impute", SimpleImputer(strategy="median", add_indicator=True)))
    if model_kind == "linear":
        steps.append(("scale", StandardScaler()))
    pipe = Pipeline(steps)
    pipe.set_output(transform="pandas")
    return pipe


def monotone_constraints(feature_names: list[str]) -> tuple[int, ...]:
    """XGBoost monotone_constraints tuple aligned to the given feature order."""
    return tuple(MONOTONE_SIGNS.get(name, 0) for name in feature_names)


def applicability_domain(X: pd.DataFrame) -> pd.DataFrame:
    """Observed range of each numeric input per fuel. The dashboard uses this to bound sliders.

    Being inside every per-feature range is necessary but NOT sufficient for interpolation:
    O2 and suppressant were varied together, so combinations inside the box can still be
    far from any tested atmosphere. A joint (nearest-tested-condition) check is added with
    the what-if feature."""
    rows = []
    for fuel, sub in X.groupby("fuel"):
        for col in NUMERIC_FEATURES:
            rows.append({"fuel": fuel, "feature": col, "min": sub[col].min(), "max": sub[col].max(),
                         "n": int(sub[col].notna().sum())})
    return pd.DataFrame(rows)
