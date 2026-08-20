import uuid

from sqlalchemy import select

from app.models.bet import Bet, BetStatus
from app.repositories.base import BaseRepository


class BetRepository(BaseRepository[Bet]):
    model = Bet

    async def list_by_user(
        self, user_id: uuid.UUID, market_id: uuid.UUID | None = None
    ) -> list[Bet]:
        stmt = select(Bet).where(Bet.user_id == user_id).order_by(Bet.created_at.desc())
        if market_id is not None:
            stmt = stmt.where(Bet.market_id == market_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_market(
        self, market_id: uuid.UUID, status: BetStatus | None = None
    ) -> list[Bet]:
        stmt = select(Bet).where(Bet.market_id == market_id)
        if status is not None:
            stmt = stmt.where(Bet.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
