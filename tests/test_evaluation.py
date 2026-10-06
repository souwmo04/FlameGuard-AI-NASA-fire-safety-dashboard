import numpy as np
import pandas as pd
import pytest

from flameguard.dataset import ModelingData
from flameguard.evaluation import choose_threshold, cross_validate, pooled_metrics, threshold_metrics
from flameguard.model import MODELS, logreg, xgboost
from flameguard.validation import repeated_group_kfold


def test_threshold_metrics_counts_missed_fires():
    y = np.array([1, 1, 1, 0, 0])
    p = np.array([0.9, 0.6, 0.2, 0.7, 0.1])
    m = threshold_metrics(y, p, 0.5)
    assert (m["tp"], m["fn"], m["fp"], m["tn"]) == (2, 1, 1, 1)
    assert m["false_negative_rate"] == pytest.approx(1 / 3)
    assert m["recall"] == pytest.approx(2 / 3)


def test_choose_threshold_reaches_target_recall():
    y = np.array([1, 1, 1, 1, 0, 0, 0, 0, 1, 0])
    p = np.array([0.9, 0.8, 0.4, 0.3, 0.7, 0.2, 0.1, 0.05, 0.6, 0.35])
    t = choose_threshold(y, p, target_recall=0.8)
    assert threshold_metrics(y, p, t)["recall"] >= 0.8
    # it is the LARGEST such threshold: the next higher candidate falls below target
    higher = np.sort(p[p > t])
    if higher.size:
        assert threshold_metrics(y, p, higher[0])["recall"] < 0.8


def synthetic_data(n_groups=20, per_group=6, seed=0) -> ModelingData:
    rng = np.random.default_rng(seed)
    rows = []
    for g in range(n_groups):
        o2 = rng.uniform(0.12, 0.34)
        fuel = "Heptane" if g % 2 else "Methanol"
        for _ in range(per_group):
            d0 = rng.uniform(1.5, 4.5)
            logit = 40 * (o2 - 0.21) + (0.8 if fuel == "Heptane" else -0.8) + rng.normal(0, 0.5)
            rows.append({"fuel": fuel, "x_o2": o2, "x_co2": 0.0, "x_he": 0.0, "pressure_atm": 1.0,
                         "d0_mm": d0, "y": int(logit > 0), "g": f"g{g}"})
    df = pd.DataFrame(rows)
    meta = pd.DataFrame({"test_id": range(len(df))})
    return ModelingData(variant="synthetic", X=df.drop(columns=["y", "g"]), y=df["y"], groups=df["g"],
                        meta=meta, excluded=pd.DataFrame())


@pytest.mark.parametrize("factory", [logreg, xgboost, MODELS["o2_only_logreg"]])
def test_cross_validate_produces_one_prediction_per_test_per_repeat(factory):
    data = synthetic_data()
    splits = repeated_group_kfold(data.y, data.groups, n_splits=4, n_repeats=2)
    folds, preds = cross_validate(factory, data, splits, model_name="m")
    assert len(folds) == 8
    assert preds.groupby("repeat")["row"].apply(lambda r: sorted(r) == list(range(len(data.y)))).all()
    assert preds["p_sustained"].between(0, 1).all()
    assert folds["threshold"].notna().all()
    assert folds["roc_auc"].mean() > 0.8  # clear synthetic signal must be learned
    pooled = pooled_metrics(preds)
    assert len(pooled) == 2 and pooled["roc_auc"].between(0, 1).all()


def test_cross_validate_never_trains_on_test_rows():
    data = synthetic_data()
    splits = repeated_group_kfold(data.y, data.groups, n_splits=4, n_repeats=1)
    seen = []

    class Spy:
        def __init__(self):
            self.inner = logreg()

        def fit(self, X, y):
            seen.append(set(X.index))
            self.inner.fit(X, y)
            return self

        def predict_proba(self, X):
            return self.inner.predict_proba(X)

        def get_params(self, deep=True):
            return {}

        def set_params(self, **params):
            return self

    cross_validate(Spy, data, splits, model_name="spy", select_threshold=False)
    for s, train_rows in zip(splits, seen):
        assert train_rows.isdisjoint(set(s.test))
