"""Phase 12: suppressant comparison from OBSERVED FLEX data (no ML model involved).

FLEX ran test series per fuel, pressure and diluent (N2 only, CO2 added, He added),
stepping oxygen down until burning stopped. We summarise each series by

    O2_50 = the O2 mole fraction at which half of 3 mm droplets kept burning,

from a small logistic fit  P(sustained) = logistic(b0 + b1 * O2[%] + b2 * (d0 - 3 mm))
on that series' tests only. A HIGHER O2_50 means flames in that atmosphere needed
more oxygen to keep burning.

This is NOT NASA's limiting oxygen index (LOI). NASA defines LOI as the oxygen level
below which quasi-steady burning is not observed at all; our outcome is whether the
flame survived until the fuel was gone. The two are related but not the same number.

Estimability rules (otherwise the series is reported as not estimable):
  * >= MIN_EACH sustained and >= MIN_EACH extinguished tests;
  * the estimate lies inside the O2 range tested in that series;
  * >= MIN_VALID_BOOT of bootstrap refits give a valid estimate (positive O2 slope).
Uncertainty: percentile intervals from resampling atmosphere groups within the series.

Within a CO2 or He series the suppressant fraction rose as O2 fell, so each O2_50 also
corresponds to a suppressant level; it is reported alongside.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

REFERENCE_D0_MM = 3.0
MIN_EACH = 3
MIN_VALID_BOOT = 0.8
N_BOOT = 1000
C = 10.0  # weak L2 penalty: keeps fits finite when a series is nearly separable


def o2_50(df: pd.DataFrame, reference_d0: float = REFERENCE_D0_MM) -> float:
    """O2 mole fraction with P(sustained) = 0.5 at the reference droplet size; NaN if undefined."""
    y = df["y_sustained"].to_numpy()
    if y.min() == y.max():
        return np.nan
    X = np.column_stack([100 * df["x_o2"].to_numpy(), df["d0_mm"].to_numpy() - reference_d0])
    fit = LogisticRegression(C=C, max_iter=5000).fit(X, y)
    b1 = fit.coef_[0][0]
    return float(-fit.intercept_[0] / b1 / 100) if b1 > 0 else np.nan


def _suppressant_at(df: pd.DataFrame, o2: float) -> float:
    """Suppressant fraction of the tested atmosphere closest in O2 to `o2` (CO2 or He series)."""
    added = df["x_co2"] + df["x_he"]
    if (added == 0).all() or np.isnan(o2):
        return np.nan
    i = (df["x_o2"] - o2).abs().idxmin()
    return float(added.loc[i])


def summarize_series(master: pd.DataFrame, seed: int = 0, n_boot: int = N_BOOT) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    m = master[master["pressure_level"].isin(["0.7atm", "1atm"])].dropna(subset=["d0_mm"])
    rows = []
    for (fuel, pressure, diluent), df in m.groupby(["fuel", "pressure_level", "diluent"]):
        n_s = int(df["y_sustained"].sum())
        n_e = len(df) - n_s
        lo, hi = float(df["x_o2"].min()), float(df["x_o2"].max())
        row = {"fuel": fuel, "pressure": pressure, "diluent": diluent, "tests": len(df), "sustained": n_s,
               "extinguished": n_e, "o2_tested_min": lo, "o2_tested_max": hi,
               "o2_50": np.nan, "ci_low": np.nan, "ci_high": np.nan, "boot_valid": np.nan,
               "ci_beyond_tested": False, "suppressant_at_o2_50": np.nan, "status": ""}
        if n_s < MIN_EACH or n_e < MIN_EACH:
            row["status"] = f"not estimable: {n_s} sustained / {n_e} extinguished (need {MIN_EACH} of each)"
            rows.append(row)
            continue
        est = o2_50(df)
        groups = df["group_id_atmosphere"].unique()
        by_group = {g: d for g, d in df.groupby("group_id_atmosphere")}
        boots = np.array([o2_50(pd.concat([by_group[g] for g in rng.choice(groups, len(groups))]))
                          for _ in range(n_boot)])
        valid = ~np.isnan(boots)
        row["boot_valid"] = float(valid.mean())
        if np.isnan(est) or not (lo <= est <= hi):
            row["status"] = "not estimable: estimate falls outside the tested O₂ range"
        elif valid.mean() < MIN_VALID_BOOT:
            row["status"] = f"not estimable: only {valid.mean():.0%} of bootstrap refits valid"
        else:
            ci_lo, ci_hi = np.quantile(boots[valid], [0.025, 0.975])
            row.update(o2_50=est, ci_low=float(ci_lo), ci_high=float(ci_hi),
                       ci_beyond_tested=bool(ci_lo < lo or ci_hi > hi),
                       suppressant_at_o2_50=_suppressant_at(df, est), status="estimated")
        rows.append(row)
    return pd.DataFrame(rows)
