import uuid

from sqlalchemy import select

from app.models.market import Market
from app.repositories.base import BaseRepository


class MarketRepository(BaseRepository[Market]):
    model = Market

    async def list_by_event(self, event_id: uuid.UUID) -> list[Market]:
        stmt = select(Market).where(Market.event_id == event_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
