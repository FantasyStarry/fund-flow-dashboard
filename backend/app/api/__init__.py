from fastapi import APIRouter

from app.api.funds import router as funds_router
from app.api.market import router as market_router

api_router = APIRouter()
api_router.include_router(funds_router)
api_router.include_router(market_router)
