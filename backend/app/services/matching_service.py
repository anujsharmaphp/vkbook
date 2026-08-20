import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.events.publisher import EventPublisher, get_event_publisher
from app.events.types import EventType
from app.models.bet import Bet, BetStatus
from app.models.market import MarketStatus
from app.models.order import Order, OrderSide, OrderStatus
from app.models.order_match import OrderMatch
from app.repositories.market_repository import MarketRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.selection_repository import SelectionRepository
from app.schemas.trading import OrderBookLevel, OrderBookRead, OrderBookSelection, OrderCreate
from app.services.wallet_service import WalletService


def _liability_minor(side: OrderSide, price: Decimal, size_minor: int) -> int:
    """What a fill of this size at this price risks for this side. Also
    used, applied to an order's own (price, stake) rather than a fill, as
    the wallet exposure to reserve/release for that order — see the
    deliberate simplification noted on `place_order` below."""
    if side == OrderSide.BACK:
        return size_minor
    liability = Decimal(size_minor) * (price - 1)
    return int(liability.quantize(Decimal("1")))


class MatchingService:
    """The matching engine: maintains each market's BACK/LAY order book and
    matches compatible orders against it.

    Matching rule (decimal odds P): a BACK order's price is the *minimum*
    odds its owner will accept; a LAY order's price is the *maximum* odds
    (liability ceiling) its owner will accept. A BACK order and a LAY order
    are compatible whenever `lay.price >= back.price` — trades always
    execute at the resting (maker) order's price (price-time priority /
    price improvement for the taker).

    Among several eligible makers, a BACK taker is filled against the
    highest-price LAY makers first (the best price achievable for a
    backer); a LAY taker is filled against the lowest-price BACK makers
    first (the best price achievable for a layer) — earliest-created wins
    ties either way. This is what produces the familiar quoted "back odds
    sit below lay odds for the same selection" spread: the best (displayed)
    back price is sourced from the best (highest) resting LAY order, and
    the best (displayed) lay price is sourced from the best (lowest)
    resting BACK order.

    Wallet exposure: on placement, the order's *full* worst-case exposure
    (its own limit price x its full stake) is reserved up front and never
    adjusted for price improvement on individual fills — a deliberate
    simplification (a production exchange trues reservations up to each
    fill's actual matched price; here we simply over-reserve, which is
    safe). On cancellation, only the unmatched remainder's share of that
    exposure is released — the matched portion stays held against the Bets
    it produced until settlement (Step 9) resolves them.
    """

    def __init__(self, session: AsyncSession, event_publisher: EventPublisher | None = None):
        self.session = session
        self.orders = OrderRepository(session)
        self.markets = MarketRepository(session)
        self.selections = SelectionRepository(session)
        self.wallets = WalletService(session)
        self.event_publisher = event_publisher or get_event_publisher()

    async def place_order(self, user_id: uuid.UUID, payload: OrderCreate) -> Order:
        existing = await self.orders.get_by_idempotency_key(user_id, payload.idempotency_key)
        if existing is not None:
            return existing

        market = await self.markets.get_by_id(payload.market_id)
        if market is None:
            raise NotFoundError(f"Market {payload.market_id} not found.", code="MARKET_NOT_FOUND")
        if market.status != MarketStatus.OPEN:
            raise ConflictError(
                f"Market is {market.status.value}, not accepting orders.", code="MARKET_NOT_OPEN"
            )

        selection = await self.selections.get_by_id(payload.selection_id)
        if selection is None or selection.market_id != market.id:
            raise NotFoundError(
                f"Selection {payload.selection_id} not found on this market.",
                code="SELECTION_NOT_FOUND",
            )

        side = OrderSide(payload.side)
        order = Order(
            user_id=user_id,
            market_id=market.id,
            selection_id=selection.id,
            side=side,
            price=payload.price,
            stake_minor=payload.stake_minor,
            idempotency_key=payload.idempotency_key,
        )
        await self.orders.add(order)

        required_exposure = _liability_minor(side, order.price, order.stake_minor)
        await self.wallets.reserve(
            user_id,
            required_exposure,
            ref_order_id=order.id,
            idempotency_key=f"hold:{order.id}",
        )

        opposite_side = OrderSide.LAY if side == OrderSide.BACK else OrderSide.BACK
        makers = await self.orders.list_matchable_opposite(market.id, selection.id, opposite_side)

        for maker in makers:
            if order.remaining_minor <= 0:
                break
            eligible = (
                maker.price >= order.price if side == OrderSide.BACK else maker.price <= order.price
            )
            if not eligible:
                # Makers are sorted best-first for this taker, so once one
                # is ineligible every later (strictly worse-priced) one is
                # too — safe to stop scanning.
                break

            match_size = min(order.remaining_minor, maker.remaining_minor)
            order_match = OrderMatch(
                id=uuid.uuid4(),
                taker_order_id=order.id,
                maker_order_id=maker.id,
                matched_price=maker.price,
                matched_size_minor=match_size,
            )
            self.session.add(order_match)

            order.matched_minor += match_size
            maker.matched_minor += match_size
            maker.status = (
                OrderStatus.MATCHED if maker.remaining_minor == 0 else OrderStatus.PARTIALLY_MATCHED
            )

            back_order, lay_order = (order, maker) if side == OrderSide.BACK else (maker, order)
            self.session.add(
                Bet(
                    user_id=back_order.user_id,
                    order_id=back_order.id,
                    order_match_id=order_match.id,
                    market_id=market.id,
                    selection_id=selection.id,
                    side=OrderSide.BACK,
                    price=maker.price,
                    stake_minor=match_size,
                    liability_minor=_liability_minor(OrderSide.BACK, maker.price, match_size),
                    status=BetStatus.MATCHED,
                )
            )
            self.session.add(
                Bet(
                    user_id=lay_order.user_id,
                    order_id=lay_order.id,
                    order_match_id=order_match.id,
                    market_id=market.id,
                    selection_id=selection.id,
                    side=OrderSide.LAY,
                    price=maker.price,
                    stake_minor=match_size,
                    liability_minor=_liability_minor(OrderSide.LAY, maker.price, match_size),
                    status=BetStatus.MATCHED,
                )
            )

        if order.remaining_minor == 0:
            order.status = OrderStatus.MATCHED
        elif order.matched_minor > 0:
            order.status = OrderStatus.PARTIALLY_MATCHED
        else:
            order.status = OrderStatus.OPEN

        await self.session.commit()
        await self.session.refresh(order)

        await self.event_publisher.publish(
            f"market:{market.id}",
            EventType.ORDER_MATCHED if order.matched_minor > 0 else EventType.ORDER_PLACED,
            {
                "order_id": str(order.id),
                "market_id": str(market.id),
                "selection_id": str(selection.id),
                "side": order.side.value,
                "status": order.status.value,
                "matched_minor": order.matched_minor,
            },
        )
        await self._publish_balance_updated(user_id)
        return order

    async def cancel_order(self, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
        order = await self.orders.get_by_id(order_id)
        if order is None or order.user_id != user_id:
            raise NotFoundError(f"Order {order_id} not found.", code="ORDER_NOT_FOUND")
        if order.status not in (OrderStatus.OPEN, OrderStatus.PARTIALLY_MATCHED):
            raise ConflictError(
                f"Order is {order.status.value} and cannot be cancelled.",
                code="ORDER_NOT_CANCELLABLE",
            )

        release_amount = _liability_minor(order.side, order.price, order.remaining_minor)
        order.status = OrderStatus.CANCELLED
        await self.wallets.release(
            user_id,
            release_amount,
            ref_order_id=order.id,
            idempotency_key=f"release:{order.id}",
        )

        await self.session.commit()
        await self.session.refresh(order)

        await self.event_publisher.publish(
            f"market:{order.market_id}",
            EventType.ORDER_CANCELLED,
            {"order_id": str(order.id), "market_id": str(order.market_id)},
        )
        await self._publish_balance_updated(user_id)
        return order

    async def _publish_balance_updated(self, user_id: uuid.UUID) -> None:
        wallet = await self.wallets.get_wallet(user_id)
        await self.event_publisher.publish(
            f"user:{user_id}",
            EventType.BALANCE_UPDATED,
            {
                "balance_minor": wallet.balance_minor,
                "reserved_minor": wallet.reserved_minor,
                "available_minor": wallet.available_minor,
            },
        )

    async def list_orders(
        self, user_id: uuid.UUID, market_id: uuid.UUID | None = None
    ) -> list[Order]:
        return await self.orders.list_by_user(user_id, market_id)

    async def get_order_book(self, market_id: uuid.UUID) -> OrderBookRead:
        """Displayed "back" prices are sourced from resting LAY orders, and
        displayed "lay" prices from resting BACK orders — the standard
        exchange display convention. This is deliberate, not a literal dump
        of `Order.side`: it's what makes "click a displayed price to bet"
        actually cross and match immediately, since a new BACK order at the
        displayed back price trades directly against the LAY order that
        price came from (see the crossing rule in this class's docstring).
        Each side is sorted best-for-a-new-trader first: displayed back
        prices descending (highest lay price), displayed lay prices
        ascending (lowest back price).
        """
        market = await self.markets.get_by_id(market_id)
        if market is None:
            raise NotFoundError(f"Market {market_id} not found.", code="MARKET_NOT_FOUND")

        rows = await self.orders.aggregate_order_book(market_id)
        by_selection: dict[uuid.UUID, dict[str, list[OrderBookLevel]]] = {}
        for selection_id, side, price, available in rows:
            bucket = by_selection.setdefault(selection_id, {"back": [], "lay": []})
            key = "back" if side == OrderSide.LAY else "lay"
            bucket[key].append(OrderBookLevel(price=price, available_size_minor=int(available)))

        selections = []
        for selection_id, levels in by_selection.items():
            levels["back"].sort(key=lambda level: level.price, reverse=True)
            levels["lay"].sort(key=lambda level: level.price)
            selections.append(
                OrderBookSelection(
                    selection_id=selection_id, back=levels["back"], lay=levels["lay"]
                )
            )
        return OrderBookRead(market_id=market_id, selections=selections)
