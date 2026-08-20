import uuid

from sqlalchemy import select

from app.models.match_state import MatchState
from app.repositories.base import BaseRepository


class MatchStateRepository(BaseRepository[MatchState]):
    model = MatchState

    async def get_by_event_id(self, event_id: uuid.UUID) -> MatchState | None:
        stmt = select(MatchState).where(MatchState.event_id == event_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_update_by_event_id(self, event_id: uuid.UUID) -> MatchState | None:
        stmt = select(MatchState).where(MatchState.event_id == event_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
