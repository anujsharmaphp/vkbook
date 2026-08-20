from sqlalchemy import select

from app.models.sport import Sport
from app.repositories.base import BaseRepository


class SportRepository(BaseRepository[Sport]):
    model = Sport

    async def list_all(self) -> list[Sport]:
        result = await self.session.execute(select(Sport).order_by(Sport.name))
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Sport | None:
        result = await self.session.execute(select(Sport).where(Sport.code == code))
        return result.scalar_one_or_none()
