import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.core.errors import ConflictError, NotFoundError
from app.events.publisher import EventPublisher, get_event_publisher
from app.events.types import EventType
from app.models.market import Market, MarketStatus
from app.models.selection import Selection
from app.repositories.event_repository import EventRepository
from app.repositories.market_repository import MarketRepository
from app.repositories.market_type_repository import MarketTypeRepository
from app.schemas.catalog import MarketCreate

# Legal market status transitions (Section 27 admin panel: Open / Suspended /
# Closed / Settled). SETTLED is a terminal state reached only via the
# settlement engine (Step 9), not exposed as a manual admin transition here.
_ALLOWED_TRANSITIONS: dict[MarketStatus, set[MarketStatus]] = {
    MarketStatus.OPEN: {MarketStatus.SUSPENDED, MarketStatus.CLOSED},
    MarketStatus.SUSPENDED: {MarketStatus.OPEN, MarketStatus.CLOSED},
    MarketStatus.CLOSED: {MarketStatus.SETTLED},
    MarketStatus.SETTLED: set(),
}


class MarketService:
    """The market engine: owns Market/Selection creation and the market
    status state machine. Order-book/odds state is layered on top of this in
    Step 4 (matching engine) — this service never touches liquidity."""

    def __init__(self, session: AsyncSession, event_publisher: EventPublisher | None = None):
        self.session = session
        self.markets = MarketRepository(session)
        self.market_types = MarketTypeRepository(session)
        self.event_repo = EventRepository(session)
        self.event_publisher = event_publisher or get_event_publisher()

    async def create_market(self, payload: MarketCreate) -> Market:
        event = await self.event_repo.get_by_id(payload.event_id)
        if event is None:
            raise NotFoundError(f"Event {payload.event_id} not found.", code="EVENT_NOT_FOUND")
        market_type = await self.market_types.get_by_id(payload.market_type_id)
        if market_type is None:
            raise NotFoundError(
                f"Market type {payload.market_type_id} not found.", code="MARKET_TYPE_NOT_FOUND"
            )

        market = Market(
            event_id=payload.event_id, market_type_id=payload.market_type_id, name=payload.name
        )
        market.selections = [
            Selection(name=s.name, display_order=s.display_order) for s in payload.selections
        ]

        await self.markets.add(market)
        await self.session.commit()
        await self.session.refresh(market, attribute_names=["selections"])

        await self.event_publisher.publish(
            f"market:{market.id}",
            EventType.MARKET_CREATED,
            {
                "market_id": str(market.id),
                "event_id": str(market.event_id),
                "status": market.status.value,
            },
        )
        return market

    async def get_market(self, market_id: uuid.UUID) -> Market:
        market = await self.markets.get_by_id(market_id)
        if market is None:
            raise NotFoundError(f"Market {market_id} not found.", code="MARKET_NOT_FOUND")
        return market

    async def list_markets_for_event(self, event_id: uuid.UUID) -> list[Market]:
        return await self.markets.list_by_event(event_id)

    async def suspend_market(self, market_id: uuid.UUID) -> Market:
        return await self._transition(market_id, MarketStatus.SUSPENDED, EventType.MARKET_SUSPENDED)

    async def reopen_market(self, market_id: uuid.UUID) -> Market:
        return await self._transition(market_id, MarketStatus.OPEN, EventType.MARKET_REOPENED)

    async def close_market(self, market_id: uuid.UUID) -> Market:
        return await self._transition(market_id, MarketStatus.CLOSED, EventType.MARKET_CLOSED)

    async def _transition(
        self, market_id: uuid.UUID, target: MarketStatus, event_type: str
    ) -> Market:
        market = await self.get_market(market_id)
        allowed = _ALLOWED_TRANSITIONS[market.status]
        if target not in allowed:
            raise ConflictError(
                f"Cannot transition market from {market.status.value} to {target.value}.",
                code="INVALID_MARKET_TRANSITION",
            )

        market.status = target
        try:
            await self.session.commit()
        except StaleDataError as exc:
            await self.session.rollback()
            raise ConflictError(
                "Market was modified concurrently; reload and retry.",
                code="MARKET_VERSION_CONFLICT",
            ) from exc

        await self.session.refresh(market)
        await self.event_publisher.publish(
            f"market:{market.id}",
            event_type,
            {"market_id": str(market.id), "status": market.status.value, "version": market.version},
        )
        return market
