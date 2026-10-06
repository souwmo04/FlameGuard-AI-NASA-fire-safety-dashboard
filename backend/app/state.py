"""Everything the API serves, loaded once at startup and shared read-only across requests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

import pandas as pd
from fastapi import Request

from flameguard.dataset import build_modeling_data
from flameguard.prediction import FinalModel

from app.config import Settings

SELECTED_MODEL = "logreg_np"


@dataclass
class AppState:
    settings: Settings
    master: pd.DataFrame          # all 274 FLEX tests (observed)
    tests: pd.DataFrame           # the 252 tests the model was trained on: inputs + identifiers + outcome
    model: FinalModel
    oof: pd.Series                # test_id -> out-of-fold P(sustained), mean over 5 CV repeats
    card: dict                    # models/final_model.json
    o2_50: pd.DataFrame           # reports/phase12/o2_50_by_series.csv
    global_importance: pd.DataFrame
    reliability: pd.DataFrame
    risk_bands: pd.DataFrame
    subgroups: pd.DataFrame
    missed_fires: pd.DataFrame
    data_sha256: str
    excluded: dict[int, str]      # test_id -> why it is outside the model's training scope
    cache: dict = field(default_factory=dict)  # lazily built, read-only derived views

    @property
    def background(self) -> pd.DataFrame:
        """Background distribution for SHAP: the training inputs."""
        return self.tests[["fuel", "x_o2", "x_co2", "x_he", "d0_mm"]]


def load_state(settings: Settings) -> AppState:
    master = pd.read_csv(settings.master_path)
    master["qc_flags"] = master["qc_flags"].fillna("")

    data = build_modeling_data(master, "primary")
    tests = data.X.drop(columns="pressure_atm").copy()
    for col in ["test_id", "flex_identifier", "diluent", "pressure_level", "outcome_raw"]:
        tests[col] = data.meta[col].to_numpy()
    tests["y_sustained"] = data.y.to_numpy()

    reports = settings.reports_dir
    oof_all = pd.read_csv(reports / "phase8" / "final_oof_predictions.csv")
    oof = oof_all[oof_all["model"] == SELECTED_MODEL].groupby("test_id")["p_sustained"].mean()

    importance = pd.read_csv(reports / "phase10" / "global_importance.csv")
    return AppState(
        settings=settings,
        master=master,
        tests=tests.reset_index(drop=True),
        model=FinalModel.load(settings.model_path),
        oof=oof,
        card=json.loads(settings.model_card_path.read_text(encoding="utf-8")),
        o2_50=pd.read_csv(reports / "phase12" / "o2_50_by_series.csv"),
        global_importance=importance[importance["grouping"] == "grouped"].reset_index(drop=True),
        reliability=pd.read_csv(reports / "phase9" / "reliability.csv"),
        risk_bands=pd.read_csv(reports / "phase9" / "risk_bands.csv"),
        subgroups=pd.read_csv(reports / "phase9" / "subgroups.csv"),
        missed_fires=pd.read_csv(reports / "phase9" / "consistently_missed_fires.csv"),
        data_sha256=hashlib.sha256(settings.master_path.read_bytes()).hexdigest(),
        excluded=dict(zip(data.excluded["test_id"].astype(int), data.excluded["reason"])),
    )


def get_state(request: Request) -> AppState:
    """FastAPI dependency."""
    return request.app.state.flameguard
