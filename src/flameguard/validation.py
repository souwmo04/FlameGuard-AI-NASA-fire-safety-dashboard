"""Phase 6: validation splits that respect the experiment structure.

Primary scheme: repeated StratifiedGroupKFold on the atmosphere group. Tests that
shared a chamber atmosphere are near-duplicates in every input except droplet
size, so all of them go to the same fold; a random row split would let the model
"recognise" an atmosphere it has already seen and overstate performance.

Stress tests (generalisation beyond the training conditions):
  leave_one_diluent_out   train without CO2 (or He) tests, test on them. Also crosses
                          campaign periods, since diluent is confounded with time.
  pressure_transfer       train on 1 atm, test on 0.7 atm (and the reverse).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


@dataclass(frozen=True)
class Split:
    name: str
    train: np.ndarray
    test: np.ndarray
    repeat: int | None = None
    fold: int | None = None


def repeated_group_kfold(y: pd.Series, groups: pd.Series, n_splits: int = 5, n_repeats: int = 5,
                         seed: int = 0) -> list[Split]:
    """n_repeats x StratifiedGroupKFold with different shuffles; every test appears in exactly
    one test fold per repeat and no atmosphere group is ever split across train and test."""
    splits = []
    for r in range(n_repeats):
        cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed + r)
        for k, (tr, te) in enumerate(cv.split(np.zeros(len(y)), y, groups)):
            splits.append(Split(name=f"r{r}f{k}", train=tr, test=te, repeat=r, fold=k))
    check_splits(splits, y, groups)
    return splits


def stress_splits(meta: pd.DataFrame) -> list[Split]:
    """Held-out-condition splits built from the meta columns of ModelingData."""
    out = []
    for dil in ["CO2", "He"]:
        test = meta["diluent"] == dil
        out.append(Split(name=f"leave_out_{dil}", train=np.flatnonzero(~test), test=np.flatnonzero(test)))
    for train_lvl, test_lvl in [("1atm", "0.7atm"), ("0.7atm", "1atm")]:
        out.append(Split(name=f"train_{train_lvl}_test_{test_lvl}",
                         train=np.flatnonzero(meta["pressure_level"] == train_lvl),
                         test=np.flatnonzero(meta["pressure_level"] == test_lvl)))
    return out


def check_splits(splits: list[Split], y: pd.Series, groups: pd.Series) -> None:
    """Raise if any split leaks a group, overlaps rows, or has a single-class test fold."""
    g = groups.to_numpy()
    yv = y.to_numpy()
    for s in splits:
        if np.intersect1d(s.train, s.test).size:
            raise ValueError(f"{s.name}: rows in both train and test")
        shared = set(g[s.train]) & set(g[s.test])
        if shared:
            raise ValueError(f"{s.name}: groups in both train and test: {sorted(shared)[:3]}")
        if len(np.unique(yv[s.test])) < 2:
            raise ValueError(f"{s.name}: test fold has only one class")
    repeats = {s.repeat for s in splits if s.repeat is not None}
    for r in repeats:
        test_rows = np.concatenate([s.test for s in splits if s.repeat == r])
        if len(test_rows) != len(yv) or len(np.unique(test_rows)) != len(yv):
            raise ValueError(f"repeat {r}: test folds do not partition the data")


def fold_table(splits: list[Split], y: pd.Series, groups: pd.Series) -> pd.DataFrame:
    """Size and class balance of each split, for reporting."""
    yv = y.to_numpy()
    g = groups.to_numpy()
    return pd.DataFrame([{
        "split": s.name,
        "train_tests": len(s.train),
        "test_tests": len(s.test),
        "test_groups": len(set(g[s.test])),
        "test_sustained": int(yv[s.test].sum()),
        "test_sustained_share": round(float(yv[s.test].mean()), 3),
    } for s in splits])
