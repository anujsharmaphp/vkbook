import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.user import User
from app.repositories.bet_repository import BetRepository
from app.schemas.trading import BetRead, OrderBookRead, OrderCreate, OrderRead
from app.security.dependencies import get_current_user
from app.services.matching_service import MatchingService

router = APIRouter(tags=["trading"])


@router.post("/orders", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def place_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderRead:
    order = await MatchingService(db).place_order(user.id, payload)
    return OrderRead.from_model(order)


@router.delete("/orders/{order_id}", response_model=OrderRead)
async def cancel_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderRead:
    order = await MatchingService(db).cancel_order(user.id, order_id)
    return OrderRead.from_model(order)


@router.get("/orders", response_model=list[OrderRead])
async def list_orders(
    market_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OrderRead]:
    orders = await MatchingService(db).list_orders(user.id, market_id)
    return [OrderRead.from_model(o) for o in orders]


@router.get("/bets", response_model=list[BetRead])
async def list_bets(
    market_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[BetRead]:
    bets = await BetRepository(db).list_by_user(user.id, market_id)
    return [BetRead.from_model(b) for b in bets]


@router.get("/markets/{market_id}/order-book", response_model=OrderBookRead)
async def get_order_book(market_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> OrderBookRead:
    return await MatchingService(db).get_order_book(market_id)
