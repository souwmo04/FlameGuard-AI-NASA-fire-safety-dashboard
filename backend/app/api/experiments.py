from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.common import Fuel, Suppressant
from app.schemas.responses import ExperimentDetail, ExperimentList
from app.services import experiments
from app.state import AppState, get_state

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=ExperimentList, summary="Observed FLEX tests with filters")
def list_experiments(
    fuel: Fuel | None = None,
    suppressant: Suppressant | None = None,
    pressure_level: Literal["0.7atm", "1atm", "2-3atm"] | None = None,
    outcome: Literal["Extinction", "Completion", "Disruption"] | None = None,
    in_model_scope: bool | None = None,
    oxygen_min: float | None = Query(None, ge=0, le=100),
    oxygen_max: float | None = Query(None, ge=0, le=100),
    search: str | None = Query(None, max_length=40, description="FLEX identifier fragment or exact test number"),
    sort: Literal["test_id", "-test_id", "oxygen", "-oxygen", "risk", "-risk", "date", "-date"] = "test_id",
    limit: int = Query(50, ge=1, le=300),
    offset: int = Query(0, ge=0),
    state: AppState = Depends(get_state),
) -> ExperimentList:
    return experiments.list_experiments(
        state, fuel=fuel.value if fuel else None, suppressant=suppressant.value if suppressant else None,
        pressure_level=pressure_level, outcome=outcome, in_model_scope=in_model_scope, oxygen_min=oxygen_min,
        oxygen_max=oxygen_max, search=search, sort=sort, limit=limit, offset=offset)


@router.get("/{test_id}", response_model=ExperimentDetail, summary="One FLEX test with source and notes")
def get_experiment(test_id: int, state: AppState = Depends(get_state)) -> ExperimentDetail:
    detail = experiments.get_experiment(state, test_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"No FLEX test {test_id}")
    return detail
