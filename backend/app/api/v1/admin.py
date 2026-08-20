import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.user import User
from app.schemas.catalog import (
    CompetitionCreate,
    CompetitionRead,
    EventCreate,
    EventRead,
    MarketCreate,
    MarketRead,
    MarketTypeCreate,
    MarketTypeRead,
    SportCreate,
    SportRead,
)
from app.security.dependencies import require_role
from app.services.catalog_service import CatalogService
from app.services.market_service import MarketService

router = APIRouter(prefix="/admin", tags=["admin"])

_require_admin = require_role("admin")


@router.post("/sports", response_model=SportRead, status_code=status.HTTP_201_CREATED)
async def create_sport(
    payload: SportCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> SportRead:
    sport = await CatalogService(db).create_sport(payload)
    return SportRead.model_validate(sport)


@router.post("/competitions", response_model=CompetitionRead, status_code=status.HTTP_201_CREATED)
async def create_competition(
    payload: CompetitionCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> CompetitionRead:
    competition = await CatalogService(db).create_competition(payload)
    return CompetitionRead.model_validate(competition)


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> EventRead:
    event = await CatalogService(db).create_event(payload)
    return EventRead.from_model(event)


@router.post("/market-types", response_model=MarketTypeRead, status_code=status.HTTP_201_CREATED)
async def create_market_type(
    payload: MarketTypeCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> MarketTypeRead:
    market_type = await CatalogService(db).create_market_type(payload)
    return MarketTypeRead.model_validate(market_type)


@router.post("/markets", response_model=MarketRead, status_code=status.HTTP_201_CREATED)
async def create_market(
    payload: MarketCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> MarketRead:
    market = await MarketService(db).create_market(payload)
    return MarketRead.from_model(market)


@router.post("/markets/{market_id}/suspend", response_model=MarketRead)
async def suspend_market(
    market_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> MarketRead:
    market = await MarketService(db).suspend_market(market_id)
    return MarketRead.from_model(market)


@router.post("/markets/{market_id}/reopen", response_model=MarketRead)
async def reopen_market(
    market_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> MarketRead:
    market = await MarketService(db).reopen_market(market_id)
    return MarketRead.from_model(market)


@router.post("/markets/{market_id}/close", response_model=MarketRead)
async def close_market(
    market_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> MarketRead:
    market = await MarketService(db).close_market(market_id)
    return MarketRead.from_model(market)
