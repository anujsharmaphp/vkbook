from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.user import User
from app.schemas.wallet import LedgerEntryRead, WalletRead
from app.security.dependencies import get_current_user
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("", response_model=WalletRead)
async def get_wallet(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> WalletRead:
    wallet = await WalletService(db).get_wallet(user.id)
    return WalletRead.from_model(wallet)


@router.get("/ledger", response_model=list[LedgerEntryRead])
async def get_ledger(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> list[LedgerEntryRead]:
    entries = await WalletService(db).list_ledger(user.id)
    return [LedgerEntryRead.from_model(e) for e in entries]
