import uuid

from sqlalchemy import select

from app.models.wallet import Wallet
from app.repositories.base import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    model = Wallet

    async def get_by_user_id(self, user_id: uuid.UUID) -> Wallet | None:
        stmt = select(Wallet).where(Wallet.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_for_update(self, user_id: uuid.UUID) -> Wallet | None:
        stmt = select(Wallet).where(Wallet.user_id == user_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
