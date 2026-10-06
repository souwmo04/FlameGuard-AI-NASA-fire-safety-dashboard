"""Rankings of tested conditions from OBSERVED FLEX outcomes (no model involved)."""

from __future__ import annotations

import pandas as pd

from flameguard.eda import wilson_interval

IN_SCOPE = ("0.7atm", "1atm")


def observed_condition_ranking(master: pd.DataFrame, min_tests: int = 3) -> pd.DataFrame:
    """Observed sustained-combustion rate per fuel x tested atmosphere (0.7-1 atm).

    Only cells with at least `min_tests` tests are kept; each has a 95% Wilson interval.
    Sorted from most to least often sustained (ties: more tests first).
    """
    m = master[master["pressure_level"].isin(IN_SCOPE)]
    g = (m.groupby(["fuel", "group_id_atmosphere"])
         .agg(tests=("y_sustained", "size"), sustained=("y_sustained", "sum"), x_o2=("x_o2", "first"),
              x_co2=("x_co2", "first"), x_he=("x_he", "first"), pressure_level=("pressure_level", "first"),
              diluent=("diluent", "first"), test_ids=("test_id", lambda s: sorted(int(v) for v in s)))
         .reset_index())
    g = g[g["tests"] >= min_tests].copy()
    ci = [wilson_interval(int(s), int(n)) for s, n in zip(g["sustained"], g["tests"])]
    g["observed_rate"] = g["sustained"] / g["tests"]
    g["ci_low"] = [c[0] for c in ci]
    g["ci_high"] = [c[1] for c in ci]
    return g.sort_values(["observed_rate", "tests"], ascending=[False, False]).reset_index(drop=True)
