import uuid

from sqlalchemy import select

from app.models.simulator_event import SimulatorEvent
from app.repositories.base import BaseRepository


class SimulatorEventRepository(BaseRepository[SimulatorEvent]):
    model = SimulatorEvent

    async def list_by_event(self, event_id: uuid.UUID, limit: int = 50) -> list[SimulatorEvent]:
        stmt = (
            select(SimulatorEvent)
            .where(SimulatorEvent.event_id == event_id)
            .order_by(SimulatorEvent.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
