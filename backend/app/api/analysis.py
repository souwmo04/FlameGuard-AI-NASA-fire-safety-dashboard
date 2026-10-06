from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.schemas.common import Fuel
from app.schemas.responses import (ConditionRankingResponse, RankingResponse, SimilarRequest, SimilarResponse,
                                   SuppressantsResponse)
from app.services import analysis
from app.state import AppState, get_state

router = APIRouter(tags=["analysis"])


@router.get("/ranking", response_model=RankingResponse, summary="Rank FLEX tests by predicted risk or burn time")
def ranking(
    by: Literal["risk", "lowest_risk", "extinction", "burn_time"] = "risk",
    fuel: Fuel | None = None,
    limit: int = Query(20, ge=1, le=274),
    state: AppState = Depends(get_state),
) -> RankingResponse:
    return analysis.ranking(state, by, fuel.value if fuel else None, limit)


@router.get("/ranking/conditions", response_model=ConditionRankingResponse,
            summary="Rank tested atmospheres by observed sustained-combustion rate")
def condition_ranking(
    order: Literal["desc", "asc"] = "desc",
    min_tests: int = Query(3, ge=1, le=20),
    limit: int = Query(15, ge=1, le=100),
    state: AppState = Depends(get_state),
) -> ConditionRankingResponse:
    return analysis.condition_ranking(state, order, min_tests, limit)


@router.get("/suppressants", response_model=SuppressantsResponse,
            summary="Suppressant comparison from observed tests (no ML model)")
def suppressants(state: AppState = Depends(get_state)) -> SuppressantsResponse:
    return analysis.suppressants(state)


@router.post("/similar-experiments", response_model=SimilarResponse, summary="Nearest tested FLEX conditions")
def similar(request: SimilarRequest, state: AppState = Depends(get_state)) -> SimilarResponse:
    return analysis.similar(state, request, request.k)
