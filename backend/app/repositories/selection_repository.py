from app.models.selection import Selection
from app.repositories.base import BaseRepository


class SelectionRepository(BaseRepository[Selection]):
    model = Selection
