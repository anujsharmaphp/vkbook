from fastapi import APIRouter

from app.api.v1 import admin, auth, catalog, health, simulator, trading, wallet

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(catalog.router)
api_router.include_router(admin.router)
api_router.include_router(trading.router)
api_router.include_router(wallet.router)
api_router.include_router(simulator.router)
