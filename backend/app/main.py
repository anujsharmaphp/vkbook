from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.db.session import AsyncSessionFactory
from app.models.match_state import MatchSimStatus, MatchState
from app.services.simulation_runner import start_simulation_task
from app.websocket.routes import router as websocket_router

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Resume any match the simulator had left LIVE — the ticking background
    # task only lives in-process, so it never survives a redeploy or (on
    # Render's free tier) the service sleeping and waking back up.
    async with AsyncSessionFactory() as session:
        live_states = await session.execute(
            select(MatchState).where(MatchState.status == MatchSimStatus.LIVE)
        )
        for state in live_states.scalars().all():
            start_simulation_task(state.event_id)
    yield


app = FastAPI(title="Sports Exchange Simulator API", version="0.1.0", lifespan=lifespan)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(api_router)
app.include_router(websocket_router)
