import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.competition import Competition
from app.models.event import Event
from app.models.market_type import MarketType
from app.models.sport import Sport
from app.repositories.competition_repository import CompetitionRepository
from app.repositories.event_repository import EventRepository
from app.repositories.market_type_repository import MarketTypeRepository
from app.repositories.sport_repository import SportRepository
from app.schemas.catalog import CompetitionCreate, EventCreate, MarketTypeCreate, SportCreate


class CatalogService:
    """Read-mostly reference data: Sport -> Competition -> Event, plus
    MarketType definitions. Market/Selection creation and state transitions
    live in MarketService (the market engine proper)."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.sports = SportRepository(session)
        self.competitions = CompetitionRepository(session)
        self.events = EventRepository(session)
        self.market_types = MarketTypeRepository(session)

    async def create_sport(self, payload: SportCreate) -> Sport:
        if await self.sports.get_by_code(payload.code) is not None:
            raise ConflictError(
                f"Sport code '{payload.code}' already exists.", code="SPORT_CODE_TAKEN"
            )
        sport = Sport(code=payload.code, name=payload.name)
        await self.sports.add(sport)
        await self.session.commit()
        return sport

    async def list_sports(self) -> list[Sport]:
        return await self.sports.list_all()

    async def create_competition(self, payload: CompetitionCreate) -> Competition:
        sport = await self.sports.get_by_id(payload.sport_id)
        if sport is None:
            raise NotFoundError(f"Sport {payload.sport_id} not found.", code="SPORT_NOT_FOUND")
        competition = Competition(sport_id=payload.sport_id, name=payload.name)
        await self.competitions.add(competition)
        await self.session.commit()
        return competition

    async def list_competitions(self, sport_id: uuid.UUID | None = None) -> list[Competition]:
        return await self.competitions.list_by_sport(sport_id)

    async def create_event(self, payload: EventCreate) -> Event:
        competition = await self.competitions.get_by_id(payload.competition_id)
        if competition is None:
            raise NotFoundError(
                f"Competition {payload.competition_id} not found.", code="COMPETITION_NOT_FOUND"
            )
        event = Event(
            competition_id=payload.competition_id, name=payload.name, start_time=payload.start_time
        )
        await self.events.add(event)
        await self.session.commit()
        return event

    async def list_events(
        self, competition_id: uuid.UUID | None = None, status: str | None = None
    ) -> list[Event]:
        return await self.events.list_filtered(competition_id=competition_id, status=status)

    async def get_event(self, event_id: uuid.UUID) -> Event:
        event = await self.events.get_by_id(event_id)
        if event is None:
            raise NotFoundError(f"Event {event_id} not found.", code="EVENT_NOT_FOUND")
        return event

    async def create_market_type(self, payload: MarketTypeCreate) -> MarketType:
        if await self.market_types.get_by_code(payload.code) is not None:
            raise ConflictError(
                f"Market type code '{payload.code}' already exists.", code="MARKET_TYPE_CODE_TAKEN"
            )
        market_type = MarketType(
            code=payload.code, name=payload.name, settlement_rule=payload.settlement_rule
        )
        await self.market_types.add(market_type)
        await self.session.commit()
        return market_type

    async def list_market_types(self) -> list[MarketType]:
        return await self.market_types.list_all()
