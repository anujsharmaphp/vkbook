import uuid

from sqlalchemy import func, select

from app.models.order import Order, OrderSide, OrderStatus
from app.repositories.base import BaseRepository

_OPEN_STATUSES = (OrderStatus.OPEN, OrderStatus.PARTIALLY_MATCHED)


class OrderRepository(BaseRepository[Order]):
    model = Order

    async def get_by_idempotency_key(
        self, user_id: uuid.UUID, idempotency_key: str
    ) -> Order | None:
        stmt = select(Order).where(
            Order.user_id == user_id, Order.idempotency_key == idempotency_key
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_matchable_opposite(
        self, market_id: uuid.UUID, selection_id: uuid.UUID, opposite_side: OrderSide
    ) -> list[Order]:
        """Resting opposite-side orders for one selection, row-locked so two
        concurrent takers can never both consume the same liquidity
        (Section 22 — on SQLite this lock is a no-op, but the query compiles
        correctly for PostgreSQL where it provides real row-level locking).

        Ordering matches MatchingService's derivation: against a BACK taker,
        LAY makers are offered highest-price-first (best for the backer);
        against a LAY taker, BACK makers are offered lowest-price-first
        (best for the layer). Earliest-created wins ties either way.
        """
        stmt = (
            select(Order)
            .where(
                Order.market_id == market_id,
                Order.selection_id == selection_id,
                Order.side == opposite_side,
                Order.status.in_(_OPEN_STATUSES),
            )
            .with_for_update()
        )
        if opposite_side == OrderSide.LAY:
            stmt = stmt.order_by(Order.price.desc(), Order.created_at.asc())
        else:
            stmt = stmt.order_by(Order.price.asc(), Order.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_user(
        self, user_id: uuid.UUID, market_id: uuid.UUID | None = None
    ) -> list[Order]:
        stmt = select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        if market_id is not None:
            stmt = stmt.where(Order.market_id == market_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_open_by_market(self, market_id: uuid.UUID) -> list[Order]:
        stmt = select(Order).where(
            Order.market_id == market_id, Order.status.in_(_OPEN_STATUSES)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_open_by_market_and_user(
        self, market_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[Order]:
        stmt = select(Order).where(
            Order.market_id == market_id,
            Order.user_id == user_id,
            Order.status.in_(_OPEN_STATUSES),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def aggregate_order_book(self, market_id: uuid.UUID) -> list[tuple]:
        stmt = (
            select(
                Order.selection_id,
                Order.side,
                Order.price,
                func.sum(Order.stake_minor - Order.matched_minor).label("available"),
            )
            .where(Order.market_id == market_id, Order.status.in_(_OPEN_STATUSES))
            .group_by(Order.selection_id, Order.side, Order.price)
        )
        result = await self.session.execute(stmt)
        return list(result.all())
