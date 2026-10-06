"""Phase 7: model definitions.

Every model is a full sklearn Pipeline (feature engineering + estimator), so it can
be refitted per fold without any information from the test fold.

The plain factories use hyperparameters fixed a priori (Phase 7). The tuned_*
factories (Phase 8) wrap them in a grid search over grouped inner folds; the
evaluation harness passes the training-fold groups, so tuning never sees the
outer test fold (nested cross-validation). Tuning optimises log loss, the same
proper scoring rule used for model selection.

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
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from flameguard.features import FEATURE_SETS, make_preprocessor, monotone_constraints

RANDOM_STATE = 42

# Feature set of the final model. Pressure was dropped after Phase 8 (decision log
# D-001, docs/decisions.md): within each FLEX pressure level it only varies by
# measurement noise (sd ~0.005 atm), so a linear model extrapolates it wildly when
# moved between levels, and it added no in-distribution skill. Pressure still
# defines the model's scope (0.7-1 atm) via dataset.IN_SCOPE_PRESSURE_LEVELS.
FINAL_FEATURE_SET = "no_pressure"


def majority_baseline() -> Pipeline:
    """Predicts the training-fold sustained rate for every test (no information)."""
    return Pipeline([("model", DummyClassifier(strategy="prior"))])


def o2_only_logreg() -> Pipeline:
    """Logistic regression on O2 mole fraction alone: the 'obvious' baseline to beat."""
    pre = ColumnTransformer([("o2", StandardScaler(), ["x_o2"])], remainder="drop")
    return Pipeline([("pre", pre), ("model", LogisticRegression(max_iter=1000))])


def logreg(feature_set: str = "base", impute: bool = False, interaction: bool = True,
           C: float = 1.0) -> Pipeline:
    """L2-regularised logistic regression, by default with the fuel x droplet-size interaction."""
    return Pipeline([
        ("pre", make_preprocessor("linear", feature_set=feature_set, impute=impute, interaction=interaction)),
        ("model", LogisticRegression(C=C, max_iter=5000)),
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


INNER_TUNING_SPLITS = 4

GRIDS = {
    "logreg": {"model__C": [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0]},
    "random_forest": {"model__min_samples_leaf": [1, 3, 5, 10],
                      "model__max_features": ["sqrt", 0.5, 1.0],
                      "model__n_estimators": [300]},
    "xgboost": {"model__max_depth": [2, 3, 4],
                "model__learning_rate": [0.03, 0.1],
                "model__n_estimators": [100, 300],
                "model__min_child_weight": [1, 3]},
}


def _grid(pipeline: Pipeline, grid: dict) -> GridSearchCV:
    return GridSearchCV(
        pipeline, grid, scoring="neg_log_loss", refit=True, n_jobs=-1, error_score="raise",
        cv=StratifiedGroupKFold(n_splits=INNER_TUNING_SPLITS, shuffle=True, random_state=RANDOM_STATE),
    )


def tuned_logreg(feature_set: str = "base") -> GridSearchCV:
    return _grid(logreg(feature_set=feature_set), GRIDS["logreg"])


def tuned_random_forest(feature_set: str = "base") -> GridSearchCV:
    rf = random_forest(feature_set=feature_set)
    rf.set_params(model__n_jobs=1)  # parallelise over the grid instead
    return _grid(rf, GRIDS["random_forest"])


def tuned_xgboost(feature_set: str = "base") -> GridSearchCV:
    xgb = xgboost(feature_set=feature_set)
    xgb.set_params(model__n_jobs=1)
    return _grid(xgb, GRIDS["xgboost"])


TUNED_MODELS: dict[str, Callable[[], GridSearchCV]] = {
    "logreg_tuned": tuned_logreg,
    "random_forest_tuned": tuned_random_forest,
    "xgboost_tuned": tuned_xgboost,
}

# Candidates for the final model, all without pressure (D-001). The pre-registered
# selection rule (lowest mean log loss, simplest within 1 SE) is applied to this set.
FINAL_CANDIDATES: dict[str, Callable[[], Pipeline | GridSearchCV]] = {
    "logreg_np": lambda: logreg(feature_set=FINAL_FEATURE_SET),
    "logreg_np_tuned": lambda: tuned_logreg(FINAL_FEATURE_SET),
    "xgboost_np": lambda: xgboost(feature_set=FINAL_FEATURE_SET),
    "xgboost_np_tuned": lambda: tuned_xgboost(FINAL_FEATURE_SET),
    "random_forest_np": lambda: random_forest(feature_set=FINAL_FEATURE_SET),
    "random_forest_np_tuned": lambda: tuned_random_forest(FINAL_FEATURE_SET),
}

MODELS: dict[str, Callable[[], Pipeline]] = {
    "majority_baseline": majority_baseline,
    "o2_only_logreg": o2_only_logreg,
    "logreg": logreg,
    "random_forest": random_forest,
    "xgboost": xgboost,
}
