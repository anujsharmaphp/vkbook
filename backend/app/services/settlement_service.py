import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.events.publisher import EventPublisher, get_event_publisher
from app.events.types import EventType
from app.models.bet import Bet, BetStatus
from app.models.ledger_entry import LedgerEntryType
from app.models.market import MarketStatus
from app.models.order import OrderSide, OrderStatus
from app.repositories.bet_repository import BetRepository
from app.repositories.market_repository import MarketRepository
from app.repositories.order_repository import OrderRepository
from app.services.wallet_service import WalletService


def _settle_bet_deltas(bet: Bet, selection_won: bool) -> tuple[int, int, LedgerEntryType]:
    """(balance_delta, reserved_delta, entry_type) for settling one matched
    bet, given whether the selection *it was placed on* won.

    BACK's exposure hold equals its stake; LAY's equals its liability
    (already computed and stored on the bet at match time). A win releases
    the hold and adds profit; a loss releases the hold by consuming it —
    the money that was held is the money that's lost.
    """
    owner_won = (bet.side == OrderSide.BACK) == selection_won

    if bet.side == OrderSide.BACK:
        hold = bet.stake_minor
        if owner_won:
            profit = int((Decimal(bet.stake_minor) * (bet.price - 1)).quantize(Decimal("1")))
            return profit, -hold, LedgerEntryType.SETTLEMENT_WIN
        return -bet.stake_minor, -hold, LedgerEntryType.SETTLEMENT_LOSS

    hold = bet.liability_minor
    if owner_won:
        return bet.stake_minor, -hold, LedgerEntryType.SETTLEMENT_WIN
    return -bet.liability_minor, -hold, LedgerEntryType.SETTLEMENT_LOSS


def _release_amount(side: OrderSide, price: Decimal, remaining_minor: int) -> int:
    if side == OrderSide.BACK:
        return remaining_minor
    return int((Decimal(remaining_minor) * (price - 1)).quantize(Decimal("1")))


class SettlementService:
    """The settlement engine: resolves every MATCHED bet on a market once
    its winning selection is known, and cancels whatever's still resting.
    Settlement is a distinct authority from MarketService's normal state
    machine — it can settle a market from OPEN, SUSPENDED, or CLOSED, and
    is idempotent (re-settling an already-SETTLED market is a no-op) so a
    retried or resumed simulator tick can never double-pay a bet.
    """

    def __init__(self, session: AsyncSession, event_publisher: EventPublisher | None = None):
        self.session = session
        self.markets = MarketRepository(session)
        self.bets = BetRepository(session)
        self.orders = OrderRepository(session)
        self.wallets = WalletService(session)
        self.event_publisher = event_publisher or get_event_publisher()

    async def settle_market(self, market_id: uuid.UUID, winning_selection_id: uuid.UUID) -> None:
        market = await self.markets.get_by_id(market_id)
        if market is None:
            raise NotFoundError(f"Market {market_id} not found.", code="MARKET_NOT_FOUND")
        if market.status == MarketStatus.SETTLED:
            return

        affected_users: set[uuid.UUID] = set()

        matched_bets = await self.bets.list_by_market(market_id, status=BetStatus.MATCHED)
        for bet in matched_bets:
            selection_won = bet.selection_id == winning_selection_id
            balance_delta, reserved_delta, entry_type = _settle_bet_deltas(bet, selection_won)
            await self.wallets.post_settlement(
                bet.user_id,
                balance_delta=balance_delta,
                reserved_delta=reserved_delta,
                entry_type=entry_type,
                ref_bet_id=bet.id,
                idempotency_key=f"settle:{bet.id}",
            )
            bet.status = BetStatus.SETTLED
            affected_users.add(bet.user_id)

        open_orders = await self.orders.list_open_by_market(market_id)
        for order in open_orders:
            release = _release_amount(order.side, order.price, order.remaining_minor)
            if release > 0:
                await self.wallets.release(
                    order.user_id,
                    release,
                    ref_order_id=order.id,
                    idempotency_key=f"release-settle:{order.id}",
                )
            order.status = OrderStatus.CANCELLED
            affected_users.add(order.user_id)

        market.status = MarketStatus.SETTLED
        await self.session.commit()

        await self.event_publisher.publish(
            f"market:{market.id}",
            EventType.MARKET_SETTLED,
            {"market_id": str(market.id), "winning_selection_id": str(winning_selection_id)},
        )
        for bet in matched_bets:
            await self.event_publisher.publish(
                f"user:{bet.user_id}",
                EventType.BET_SETTLED,
                {"bet_id": str(bet.id), "market_id": str(market.id), "status": bet.status.value},
            )
        for user_id in affected_users:
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
