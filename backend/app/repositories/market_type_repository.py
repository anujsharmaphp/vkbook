from sqlalchemy import select

from app.models.market_type import MarketType
from app.repositories.base import BaseRepository


class MarketTypeRepository(BaseRepository[MarketType]):
    model = MarketType

    async def get_by_code(self, code: str) -> MarketType | None:
        result = await self.session.execute(select(MarketType).where(MarketType.code == code))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[MarketType]:
        result = await self.session.execute(select(MarketType).order_by(MarketType.name))
        return list(result.scalars().all())
