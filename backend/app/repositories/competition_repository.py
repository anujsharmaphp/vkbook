import uuid

from sqlalchemy import select

from app.models.competition import Competition
from app.repositories.base import BaseRepository


class CompetitionRepository(BaseRepository[Competition]):
    model = Competition

    async def list_by_sport(self, sport_id: uuid.UUID | None = None) -> list[Competition]:
        stmt = select(Competition).order_by(Competition.name)
        if sport_id is not None:
            stmt = stmt.where(Competition.sport_id == sport_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
