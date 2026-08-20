import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.catalog import (
    CompetitionRead,
    EventDetailRead,
    EventRead,
    MarketRead,
    MarketTypeRead,
    SportRead,
)
from app.schemas.simulator import MatchStateRead
from app.services.catalog_service import CatalogService
from app.services.market_service import MarketService
from app.services.simulation_service import SimulationEngine

router = APIRouter(tags=["catalog"])


@router.get("/sports", response_model=list[SportRead])
async def list_sports(db: AsyncSession = Depends(get_db)) -> list[SportRead]:
    sports = await CatalogService(db).list_sports()
    return [SportRead.model_validate(s) for s in sports]


@router.get("/competitions", response_model=list[CompetitionRead])
async def list_competitions(
    sport_id: uuid.UUID | None = Query(default=None), db: AsyncSession = Depends(get_db)
) -> list[CompetitionRead]:
    competitions = await CatalogService(db).list_competitions(sport_id)
    return [CompetitionRead.model_validate(c) for c in competitions]


@router.get("/events", response_model=list[EventRead])
async def list_events(
    competition_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[EventRead]:
    events = await CatalogService(db).list_events(competition_id=competition_id, status=status)
    return [EventRead.from_model(e) for e in events]


@router.get("/events/{event_id}", response_model=EventDetailRead)
async def get_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> EventDetailRead:
    event = await CatalogService(db).get_event(event_id)
    markets = await MarketService(db).list_markets_for_event(event_id)
    return EventDetailRead.from_model(event, markets)


@router.get("/events/{event_id}/match-state", response_model=MatchStateRead | None)
async def get_match_state(
    event_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> MatchStateRead | None:
    state = await SimulationEngine(db).get_state(event_id)
    return MatchStateRead.from_model(state) if state else None


@router.get("/market-types", response_model=list[MarketTypeRead])
async def list_market_types(db: AsyncSession = Depends(get_db)) -> list[MarketTypeRead]:
    market_types = await CatalogService(db).list_market_types()
    return [MarketTypeRead.model_validate(mt) for mt in market_types]


@router.get("/markets/{market_id}", response_model=MarketRead)
async def get_market(market_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> MarketRead:
    market = await MarketService(db).get_market(market_id)
    return MarketRead.from_model(market)
