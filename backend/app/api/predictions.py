from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.schemas.common import Conditions
from app.schemas.responses import PredictResponse, WhatIfResponse
from app.services import prediction, whatif
from app.state import AppState, get_state

router = APIRouter(tags=["predictions"])


class WhatIfRequest(BaseModel):
    scenario_a: Conditions
    scenario_b: Conditions
    sweep: Literal["oxygen", "droplet"] | None = "oxygen"
    sweep_points: int = Field(40, ge=5, le=200)


@router.post("/predict", response_model=PredictResponse, summary="Fire Risk with evidence and explanation")
def predict(conditions: Conditions, state: AppState = Depends(get_state)) -> PredictResponse:
    return prediction.predict(state, conditions)


@router.post("/what-if", response_model=WhatIfResponse, summary="Compare two hypothetical scenarios")
def what_if(request: WhatIfRequest, state: AppState = Depends(get_state)) -> WhatIfResponse:
    return whatif.what_if(state, request.scenario_a, request.scenario_b, request.sweep, request.sweep_points)
