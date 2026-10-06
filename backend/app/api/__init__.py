from fastapi import APIRouter

from app.api import analysis, experiments, predictions, system

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(experiments.router)
api_router.include_router(predictions.router)
api_router.include_router(analysis.router)
