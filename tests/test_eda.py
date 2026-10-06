import pandas as pd
import pytest

from flameguard.eda import rate_table, size_quartiles, wilson_interval


def test_wilson_interval_bounds_and_edge_cases():
    lo, hi = wilson_interval(0, 10)
    assert lo == pytest.approx(0, abs=1e-12) and 0 < hi < 0.35
    lo, hi = wilson_interval(10, 10)
    assert 0.65 < lo < 1 and hi == pytest.approx(1)
    lo, hi = wilson_interval(5, 10)
    assert lo < 0.5 < hi


def test_rate_table_counts():
    df = pd.DataFrame({"g": ["a", "a", "a", "b"], "y_sustained": [1, 0, 1, 0]})
    t = rate_table(df, ["g"]).set_index("g")
    assert t.loc["a", "n"] == 3 and t.loc["a", "sustained"] == 2
    assert t.loc["b", "rate"] == 0


def test_size_quartiles_are_per_group_and_keep_missing():
    df = pd.DataFrame({
        "fuel": ["A"] * 8 + ["B"] * 8 + ["B"],
        "d0_mm": list(range(1, 9)) + list(range(11, 19)) + [None],
    })
    q = size_quartiles(df)
    assert q.iloc[0].startswith("Q1") and q.iloc[7].startswith("Q4")
    assert q.iloc[8].startswith("Q1")  # quartiles computed within fuel B, not pooled
    assert pd.isna(q.iloc[16])
