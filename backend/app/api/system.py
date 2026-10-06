from fastapi import APIRouter, Depends

from app.schemas.responses import DomainResponse, HealthResponse, ModelInfoResponse, Source, StatsResponse
from app.services import system
from app.services.sources import SOURCES
from app.state import AppState, get_state

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Service health and loaded model")
def health(state: AppState = Depends(get_state)) -> HealthResponse:
    return system.health(state)


@router.get("/stats", response_model=StatsResponse, summary="Dataset counts and headline model performance")
def stats(state: AppState = Depends(get_state)) -> StatsResponse:
    return system.stats(state)


@router.get("/sources", response_model=list[Source], summary="NASA sources behind the data")
def sources() -> list[Source]:
    return SOURCES


@router.get("/domain", response_model=DomainResponse, summary="Tested input ranges per fuel (for UI controls)")
def domain(state: AppState = Depends(get_state)) -> DomainResponse:
    return system.domain(state)


@router.get("/model", response_model=ModelInfoResponse, summary="Model card: metrics, calibration, bands, limits")
def model(state: AppState = Depends(get_state)) -> ModelInfoResponse:
    return system.model_info(state)
