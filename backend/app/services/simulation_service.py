import random
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.events.publisher import EventPublisher, get_event_publisher
from app.events.types import EventType
from app.models.event import Event, EventStatus
from app.models.market import Market, MarketStatus
from app.models.match_state import MatchSimStatus, MatchState
from app.models.selection import Selection
from app.models.simulator_event import SimulatorEvent, SimulatorEventType
from app.models.user import User
from app.repositories.event_repository import EventRepository
from app.repositories.market_repository import MarketRepository
from app.repositories.match_state_repository import MatchStateRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.simulator_event_repository import SimulatorEventRepository
from app.repositories.user_repository import UserRepository
from app.schemas.trading import OrderCreate
from app.security.password import hash_password
from app.services.market_service import MarketService
from app.services.matching_service import MatchingService
from app.services.settlement_service import SettlementService
from app.services.wallet_service import WalletService

BOT_A_EMAIL = "sim-bot-a@chalkline-sim.io"
BOT_B_EMAIL = "sim-bot-b@chalkline-sim.io"
# Deep enough that continuous re-quoting never runs the bots short mid-match.
BOT_STARTING_BALANCE_MINOR = 5_000_000_00

# Weighted ball outcomes: dot 30%, single 20%, two 10%, four 20%, six 10%, wicket 10%.
_BALL_OUTCOMES = ["DOT", "DOT", "DOT", "ONE", "ONE", "TWO", "FOUR", "FOUR", "SIX", "WICKET"]
_BALL_RUNS = {"DOT": 0, "ONE": 1, "TWO": 2, "FOUR": 4, "SIX": 6, "WICKET": 0}
_QUOTE_OFFSETS = [Decimal("0.01"), Decimal("0.02"), Decimal("0.03")]
_MIN_QUOTE_PRICE = Decimal("1.01")


class SimulationEngine:
    """Drives a simplified single-innings limit-overs chase for one Event:
    ball-by-ball score simulation, bot-quoted liquidity that moves real
    prices through the real matching engine (never faked directly), market
    suspension around wickets, and handoff to SettlementService when the
    match concludes. See docs/architecture.md Section 8/28 for the design
    this implements, and Section H for the settlement flow it triggers.
    """

    def __init__(self, session: AsyncSession, event_publisher: EventPublisher | None = None):
        self.session = session
        self.events = EventRepository(session)
        self.markets = MarketRepository(session)
        self.match_states = MatchStateRepository(session)
        self.sim_events = SimulatorEventRepository(session)
        self.users = UserRepository(session)
        self.event_publisher = event_publisher or get_event_publisher()

    # ---------- admin-facing controls ----------

    async def start_match(self, event_id: uuid.UUID) -> MatchState:
        event = await self.events.get_by_id(event_id)
        if event is None:
            raise NotFoundError(f"Event {event_id} not found.", code="EVENT_NOT_FOUND")

        existing = await self.match_states.get_by_event_id(event_id)
        if existing is not None and existing.status in (MatchSimStatus.LIVE, MatchSimStatus.PAUSED):
            return existing

        team_names = await self._resolve_team_names(event_id)
        if team_names is None:
            raise ConflictError(
                "Event needs a market with exactly two selections before it can be simulated.",
                code="NO_SIMULATABLE_MARKET",
            )
        batting_team, bowling_team = team_names

        if existing is None:
            state = MatchState(
                event_id=event_id,
                batting_team=batting_team,
                bowling_team=bowling_team,
                target_runs=random.randint(90, 170),
                max_overs=10,
                status=MatchSimStatus.LIVE,
            )
            await self.match_states.add(state)
        else:
            state = existing
            state.status = MatchSimStatus.LIVE

        event.status = EventStatus.LIVE
        await self._log(event_id, SimulatorEventType.MATCH_STARTED, {"target": state.target_runs})
        await self.session.commit()
        await self.session.refresh(state)

        await self._ensure_bot(BOT_A_EMAIL, "Market Maker A")
        await self._ensure_bot(BOT_B_EMAIL, "Market Maker B")
        await self._requote_all_markets(event_id, state)
        await self._publish_state(state)
        await self._publish_event_status(event)
        return state

    async def pause_match(self, event_id: uuid.UUID) -> MatchState:
        state = await self._get_state_or_404(event_id)
        if state.status != MatchSimStatus.LIVE:
            raise ConflictError(
                f"Match is {state.status.value}, cannot pause.", code="MATCH_NOT_LIVE"
            )
        state.status = MatchSimStatus.PAUSED
        await self.session.commit()
        await self.session.refresh(state)
        await self._publish_state(state)
        return state

    async def resume_match(self, event_id: uuid.UUID) -> MatchState:
        state = await self._get_state_or_404(event_id)
        if state.status != MatchSimStatus.PAUSED:
            raise ConflictError(
                f"Match is {state.status.value}, cannot resume.", code="MATCH_NOT_PAUSED"
            )
        state.status = MatchSimStatus.LIVE
        await self.session.commit()
        await self.session.refresh(state)
        await self._publish_state(state)
        return state

    async def finish_match(self, event_id: uuid.UUID) -> MatchState:
        state = await self._get_state_or_404(event_id)
        if state.status == MatchSimStatus.COMPLETED:
            return state
        state.status = MatchSimStatus.COMPLETED
        state.winner_team = (
            state.batting_team if state.runs >= state.target_runs else state.bowling_team
        )
        await self.session.commit()
        await self.session.refresh(state)
        await self._finalize_match(event_id, state)
        return state

    async def get_state(self, event_id: uuid.UUID) -> MatchState | None:
        return await self.match_states.get_by_event_id(event_id)

    async def list_log(self, event_id: uuid.UUID, limit: int = 50) -> list[SimulatorEvent]:
        return await self.sim_events.list_by_event(event_id, limit=limit)

    # ---------- the tick loop ----------

    async def tick(self, event_id: uuid.UUID) -> bool:
        """Advances the match by one ball (or reopens markets if this tick
        follows a wicket-suspension). Returns True once the match is no
        longer LIVE — the caller should stop scheduling further ticks."""
        state = await self.match_states.get_for_update_by_event_id(event_id)
        if state is None or state.status != MatchSimStatus.LIVE:
            return True

        if state.markets_suspended:
            await self._reopen_all_markets(event_id)
            state.markets_suspended = False
            await self.session.commit()
            await self.session.refresh(state)
            await self._publish_state(state)
            return False

        outcome = random.choice(_BALL_OUTCOMES)
        state.balls_bowled += 1
        if outcome == "WICKET":
            state.wickets += 1
        else:
            state.runs += _BALL_RUNS[outcome]

        await self._log(
            event_id, SimulatorEventType.BALL, {"outcome": outcome, "over": state.overs_display}
        )

        finished, winner = self._check_completion(state)
        if finished:
            state.status = MatchSimStatus.COMPLETED
            state.winner_team = winner
        elif outcome == "WICKET":
            state.markets_suspended = True

        await self.session.commit()
        await self.session.refresh(state)

        if finished:
            await self._finalize_match(event_id, state)
            return True

        if state.markets_suspended:
            await self._suspend_all_markets(event_id)
        else:
            await self._requote_all_markets(event_id, state)

        await self._publish_state(state)
        return False

    def _check_completion(self, state: MatchState) -> tuple[bool, str | None]:
        if state.runs >= state.target_runs:
            return True, state.batting_team
        if state.wickets >= 10 or state.balls_bowled >= state.max_overs * 6:
            return True, state.bowling_team
        return False, None

    async def _finalize_match(self, event_id: uuid.UUID, state: MatchState) -> None:
        event = await self.events.get_by_id(event_id)
        if event is not None and event.status != EventStatus.COMPLETED:
            event.status = EventStatus.COMPLETED
            await self.session.commit()
            await self._publish_event_status(event)

        await self._log(event_id, SimulatorEventType.MATCH_COMPLETED, {"winner": state.winner_team})
        await self.session.commit()
        await self._publish_state(state)

        markets = await self.markets.list_by_event(event_id)
        for market in markets:
            if market.status == MarketStatus.SETTLED:
                continue
            winning_selection = next(
                (s for s in market.selections if s.name == state.winner_team), None
            )
            if winning_selection is None:
                continue
            await SettlementService(self.session, self.event_publisher).settle_market(
                market.id, winning_selection.id
            )

    # ---------- bot market-making ----------

    async def _ensure_bot(self, email: str, display_name: str) -> User:
        bot = await self.users.get_by_email(email)
        if bot is not None:
            return bot
        bot = User(
            email=email, password_hash=hash_password(str(uuid.uuid4())), display_name=display_name
        )
        await self.users.add(bot)
        await WalletService(self.session).create_wallet(
            bot.id, initial_balance_minor=BOT_STARTING_BALANCE_MINOR
        )
        await self.session.commit()
        await self.session.refresh(bot)
        return bot

    async def _resolve_team_names(self, event_id: uuid.UUID) -> tuple[str, str] | None:
        markets = await self.markets.list_by_event(event_id)
        for market in markets:
            if len(market.selections) == 2:
                names = sorted(s.name for s in market.selections)
                return names[0], names[1]
        return None

    def _fair_price_batting(self, state: MatchState) -> Decimal:
        if state.runs_needed <= 0:
            return Decimal("1.05")
        if state.wickets_remaining <= 0 or state.balls_remaining <= 0:
            return Decimal("15.00")
        required_rate = state.runs_needed / max(state.balls_remaining / 6, 0.1)
        difficulty = required_rate / max(state.wickets_remaining, 1)
        price = max(1.05, min(1.5 + difficulty * 0.35, 15.0))
        return Decimal(str(round(price, 2)))

    def _complementary_price(self, price: Decimal) -> Decimal:
        implied = 1 / float(price)
        other_implied = max(1 - implied, 0.02)
        other_price = min(1 / other_implied, 50.0)
        return Decimal(str(round(other_price, 2)))

    async def _requote_all_markets(self, event_id: uuid.UUID, state: MatchState) -> None:
        bot_a = await self._ensure_bot(BOT_A_EMAIL, "Market Maker A")
        bot_b = await self._ensure_bot(BOT_B_EMAIL, "Market Maker B")

        batting_fair = self._fair_price_batting(state)
        bowling_fair = self._complementary_price(batting_fair)

        markets = await self.markets.list_by_event(event_id)
        for market in markets:
            if market.status != MarketStatus.OPEN:
                continue
            batting_sel = next((s for s in market.selections if s.name == state.batting_team), None)
            bowling_sel = next((s for s in market.selections if s.name == state.bowling_team), None)
            if batting_sel is None or bowling_sel is None:
                continue
            await self._requote_selection(market, batting_sel, batting_fair, bot_a, bot_b)
            await self._requote_selection(market, bowling_sel, bowling_fair, bot_a, bot_b)

    async def _requote_selection(
        self, market: Market, selection: Selection, fair_price: Decimal, bot_a: User, bot_b: User
    ) -> None:
        matching = MatchingService(self.session, self.event_publisher)
        order_repo = OrderRepository(self.session)

        for bot in (bot_a, bot_b):
            resting = await order_repo.list_open_by_market_and_user(market.id, bot.id)
            for order in resting:
                if order.selection_id != selection.id:
                    continue
                try:
                    await matching.cancel_order(bot.id, order.id)
                except Exception:  # noqa: BLE001 — a bot's stale order failing to cancel must never crash the tick
                    pass

        for offset in _QUOTE_OFFSETS:
            back_price = (fair_price + offset).quantize(Decimal("0.01"))
            lay_price = (fair_price - offset).quantize(Decimal("0.01"))
            if lay_price <= _MIN_QUOTE_PRICE:
                continue
            stake_minor = random.randint(150, 600) * 100

            for bot, side, price in ((bot_a, "BACK", back_price), (bot_b, "LAY", lay_price)):
                try:
                    await matching.place_order(
                        bot.id,
                        OrderCreate(
                            market_id=market.id,
                            selection_id=selection.id,
                            side=side,  # type: ignore[arg-type]
                            price=str(price),
                            stake_minor=stake_minor,
                            idempotency_key=str(uuid.uuid4()),
                        ),
                    )
                except Exception:  # noqa: BLE001 — one failed quote must never abort the whole tick
                    pass

    async def _suspend_all_markets(self, event_id: uuid.UUID) -> None:
        market_service = MarketService(self.session, self.event_publisher)
        for market in await self.markets.list_by_event(event_id):
            if market.status == MarketStatus.OPEN:
                try:
                    await market_service.suspend_market(market.id)
                except Exception:  # noqa: BLE001
                    pass
        await self._log(event_id, SimulatorEventType.MARKET_SUSPENDED, {})
        await self.session.commit()

    async def _reopen_all_markets(self, event_id: uuid.UUID) -> None:
        market_service = MarketService(self.session, self.event_publisher)
        for market in await self.markets.list_by_event(event_id):
            if market.status == MarketStatus.SUSPENDED:
                try:
                    await market_service.reopen_market(market.id)
                except Exception:  # noqa: BLE001
                    pass
        await self._log(event_id, SimulatorEventType.MARKET_REOPENED, {})
        await self.session.commit()

    # ---------- events + logging ----------

    async def _log(
        self, event_id: uuid.UUID, event_type: SimulatorEventType, payload: dict
    ) -> None:
        entry = SimulatorEvent(event_id=event_id, event_type=event_type, payload=payload)
        await self.sim_events.add(entry)

    async def _publish_state(self, state: MatchState) -> None:
        await self.event_publisher.publish(
            f"event:{state.event_id}",
            EventType.MATCH_STATE_UPDATED,
            {
                "event_id": str(state.event_id),
                "status": state.status.value,
                "batting_team": state.batting_team,
                "bowling_team": state.bowling_team,
                "runs": state.runs,
                "wickets": state.wickets,
                "overs": state.overs_display,
                "max_overs": state.max_overs,
                "target_runs": state.target_runs,
                "winner_team": state.winner_team,
            },
        )

    async def _publish_event_status(self, event: Event) -> None:
        await self.event_publisher.publish(
            f"event:{event.id}",
            EventType.EVENT_STATUS_CHANGED,
            {"event_id": str(event.id), "status": event.status.value},
        )

    async def _get_state_or_404(self, event_id: uuid.UUID) -> MatchState:
        state = await self.match_states.get_by_event_id(event_id)
        if state is None:
            raise NotFoundError(
                f"No simulation running for event {event_id}.", code="MATCH_STATE_NOT_FOUND"
            )
        return state
