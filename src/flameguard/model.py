"""Phase 7: model definitions.

Every model is a full sklearn Pipeline (feature engineering + estimator), so it can
be refitted per fold without any information from the test fold.

Hyperparameters here are fixed a priori (sensible small-data defaults, no tuning);
Phase 8 tunes them inside nested cross-validation.

class_weight is left at None on purpose: re-weighting classes distorts predicted
probabilities, and the Fire Risk Score must be a probability. The safety goal
(catch sustained fires) is met by choosing the decision threshold instead.
"""

from __future__ import annotations

from typing import Callable

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from flameguard.features import FEATURE_SETS, make_preprocessor, monotone_constraints

RANDOM_STATE = 42


def majority_baseline() -> Pipeline:
    """Predicts the training-fold sustained rate for every test (no information)."""
    return Pipeline([("model", DummyClassifier(strategy="prior"))])


def o2_only_logreg() -> Pipeline:
    """Logistic regression on O2 mole fraction alone: the 'obvious' baseline to beat."""
    pre = ColumnTransformer([("o2", StandardScaler(), ["x_o2"])], remainder="drop")
    return Pipeline([("pre", pre), ("model", LogisticRegression(max_iter=1000))])


def logreg(feature_set: str = "base", impute: bool = False) -> Pipeline:
    """L2-regularised logistic regression with the fuel x droplet-size interaction."""
    return Pipeline([
        ("pre", make_preprocessor("linear", feature_set=feature_set, impute=impute)),
        ("model", LogisticRegression(C=1.0, max_iter=2000)),
    ])


def random_forest(feature_set: str = "base", impute: bool = False) -> Pipeline:
    return Pipeline([
        ("pre", make_preprocessor("tree", feature_set=feature_set, impute=impute)),
        ("model", RandomForestClassifier(n_estimators=500, min_samples_leaf=3, max_features="sqrt",
                                         random_state=RANDOM_STATE, n_jobs=-1)),
    ])


def xgboost(feature_set: str = "base", impute: bool = False) -> Pipeline:
    """Shallow, slowly-learning gradient boosting with a monotone-increasing O2 constraint."""
    names = list(FEATURE_SETS[feature_set])
    if impute:
        names.append("missingindicator_d0_mm")
    return Pipeline([
        ("pre", make_preprocessor("tree", feature_set=feature_set, impute=impute)),
        ("model", XGBClassifier(
            n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
            min_child_weight=2, reg_lambda=1.0, monotone_constraints=monotone_constraints(names),
            eval_metric="logloss", random_state=RANDOM_STATE, n_jobs=4, verbosity=0,
        )),
    ])


MODELS: dict[str, Callable[[], Pipeline]] = {
    "majority_baseline": majority_baseline,
    "o2_only_logreg": o2_only_logreg,
    "logreg": logreg,
    "random_forest": random_forest,
    "xgboost": xgboost,
}
