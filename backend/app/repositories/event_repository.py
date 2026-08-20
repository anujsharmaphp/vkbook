import uuid

from sqlalchemy import select

from app.models.event import Event
from app.repositories.base import BaseRepository


class EventRepository(BaseRepository[Event]):
    model = Event

    async def list_filtered(
        self, competition_id: uuid.UUID | None = None, status: str | None = None
    ) -> list[Event]:
        stmt = select(Event).order_by(Event.start_time)
        if competition_id is not None:
            stmt = stmt.where(Event.competition_id == competition_id)
        if status is not None:
            stmt = stmt.where(Event.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
