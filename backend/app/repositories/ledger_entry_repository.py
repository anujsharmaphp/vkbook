import uuid

from sqlalchemy import select

from app.models.ledger_entry import LedgerEntry
from app.repositories.base import BaseRepository


class LedgerEntryRepository(BaseRepository[LedgerEntry]):
    model = LedgerEntry

    async def get_by_idempotency_key(self, idempotency_key: str) -> LedgerEntry | None:
        stmt = select(LedgerEntry).where(LedgerEntry.idempotency_key == idempotency_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_wallet(self, wallet_id: uuid.UUID) -> list[LedgerEntry]:
        stmt = (
            select(LedgerEntry)
            .where(LedgerEntry.wallet_id == wallet_id)
            .order_by(LedgerEntry.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
