"""Seeds baseline reference data. Run with: python -m app.db.seed

Runs on every boot (idempotent — every step checks before inserting) so a
freshly-provisioned database (e.g. a new deploy's Postgres instance) always
ends up in the same rich, browsable state: roles, market types, a demo-admin
and demo-user account (Section 36), several sports/competitions/events with
real resting order-book liquidity, and one event with the cricket simulator
actually running so there's a genuinely LIVE match on first load.
"""

import asyncio
import datetime
import random
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import AsyncSessionFactory
from app.models.competition import Competition
from app.models.event import Event
from app.models.market import Market
from app.models.market_type import MarketType
from app.models.role import Role
from app.models.selection import Selection
from app.models.sport import Sport
from app.models.user import User
from app.schemas.trading import OrderCreate
from app.security.password import hash_password
from app.services.matching_service import MatchingService
from app.services.simulation_service import SimulationEngine
from app.services.wallet_service import WalletService

DEFAULT_ROLES = [
    ("user", "Standard User"),
    ("admin", "Administrator"),
]

# settlement_rule is intentionally generic — the settlement engine
# interprets "kind" to resolve a market without per-market-type code paths.
DEFAULT_MARKET_TYPES = [
    ("MATCH_ODDS", "Match Odds", {"kind": "WINNER_TAKES_ALL"}),
    ("BOOKMAKER", "Bookmaker", {"kind": "WINNER_TAKES_ALL"}),
    ("OVER_UNDER", "Over/Under", {"kind": "OVER_UNDER_LINE"}),
]

LIQUIDITY_PROVIDER_A = "seed-liquidity-a@vkbook.app"
LIQUIDITY_PROVIDER_B = "seed-liquidity-b@vkbook.app"
LIQUIDITY_BALANCE_MINOR = 50_000_000_00

# (sport code, sport name, competition name, [(event name, hours from now)])
DEMO_FIXTURES: list[tuple[str, str, str, list[tuple[str, float]]]] = [
    (
        "CRICKET",
        "Cricket",
        "Test Championship",
        [("England vs Pakistan", 0), ("Australia vs India", 30)],
    ),
    (
        "FOOTBALL",
        "Football",
        "Premier Cup",
        [("Ravensburg FC vs Union Dortmund", 3), ("Real Madrid vs Barcelona", 26)],
    ),
    (
        "TENNIS",
        "Tennis",
        "ATP Masters",
        [("D. Halvorsen vs M. Ferreira", 5)],
    ),
    (
        "BASKETBALL",
        "Basketball",
        "National League",
        [("Ironclad City vs Harborview", 8)],
    ),
]

# The first fixture (index 0) gets the live cricket simulator started on it
# instead of static seeded liquidity — see seed_demo_catalog().
LIVE_SIMULATOR_EVENT_INDEX = 0


async def seed_roles() -> None:
    async with AsyncSessionFactory() as session:
        for code, name in DEFAULT_ROLES:
            existing = await session.execute(select(Role).where(Role.code == code))
            if existing.scalar_one_or_none() is None:
                session.add(Role(code=code, name=name))
        await session.commit()


async def seed_market_types() -> None:
    async with AsyncSessionFactory() as session:
        for code, name, rule in DEFAULT_MARKET_TYPES:
            existing = await session.execute(select(MarketType).where(MarketType.code == code))
            if existing.scalar_one_or_none() is None:
                session.add(MarketType(code=code, name=name, settlement_rule=rule))
        await session.commit()


async def _ensure_user(
    session: AsyncSession,
    email: str,
    password: str,
    display_name: str,
    role_code: str | None,
    balance_minor: int | None = None,
) -> User:
    existing = await session.execute(select(User).where(User.email == email))
    user = existing.scalar_one_or_none()
    if user is not None:
        return user

    role = None
    if role_code is not None:
        role_result = await session.execute(select(Role).where(Role.code == role_code))
        role = role_result.scalar_one_or_none()

    user = User(email=email, password_hash=hash_password(password), display_name=display_name)
    if role is not None:
        user.roles.append(role)
    session.add(user)
    await session.flush()

    await WalletService(session).create_wallet(user.id, initial_balance_minor=balance_minor)
    await session.commit()
    await session.refresh(user)
    return user


async def seed_demo_users() -> None:
    settings = get_settings()
    async with AsyncSessionFactory() as session:
        await _ensure_user(
            session, settings.demo_admin_email, settings.demo_admin_password, "Demo Admin", "admin"
        )
    async with AsyncSessionFactory() as session:
        await _ensure_user(
            session, settings.demo_user_email, settings.demo_user_password, "Demo User", "user"
        )


async def _seed_two_sided_liquidity(
    session: AsyncSession,
    market: Market,
    base_prices: dict[str, Decimal],
    provider_back: User,
    provider_lay: User,
) -> None:
    """Places resting BACK orders above and LAY orders below each
    selection's base price, so `back.price > lay.price` always — the
    invariant that keeps them from matching each other (they'd only match a
    real user crossing in). Gives every seeded market real order-book depth
    without needing the simulator running."""
    matching = MatchingService(session)
    for selection in market.selections:
        base = base_prices.get(selection.name, Decimal("2.00"))
        for offset in (Decimal("0"), Decimal("0.05"), Decimal("0.10")):
            lay_price = (base - offset).quantize(Decimal("0.01"))
            back_price = (base + Decimal("0.05") + offset).quantize(Decimal("0.01"))
            if lay_price <= Decimal("1.01"):
                continue
            await matching.place_order(
                provider_lay.id,
                OrderCreate(
                    market_id=market.id,
                    selection_id=selection.id,
                    side="LAY",
                    price=str(lay_price),
                    stake_minor=random.randint(100, 500) * 100,
                    idempotency_key=str(uuid.uuid4()),
                ),
            )
            await matching.place_order(
                provider_back.id,
                OrderCreate(
                    market_id=market.id,
                    selection_id=selection.id,
                    side="BACK",
                    price=str(back_price),
                    stake_minor=random.randint(100, 500) * 100,
                    idempotency_key=str(uuid.uuid4()),
                ),
            )


async def seed_demo_catalog() -> None:
    """Only runs if there are zero sports — never touches a database an
    admin has already started building a real catalog on."""
    async with AsyncSessionFactory() as session:
        existing = await session.execute(select(Sport))
        if existing.first() is not None:
            return

        provider_a = await _ensure_user(
            session, LIQUIDITY_PROVIDER_A, str(uuid.uuid4()), "Market Liquidity A", None,
            balance_minor=LIQUIDITY_BALANCE_MINOR,
        )
        provider_b = await _ensure_user(
            session, LIQUIDITY_PROVIDER_B, str(uuid.uuid4()), "Market Liquidity B", None,
            balance_minor=LIQUIDITY_BALANCE_MINOR,
        )

        match_odds_type = (
            await session.execute(select(MarketType).where(MarketType.code == "MATCH_ODDS"))
        ).scalar_one()

        now = datetime.datetime.now(datetime.UTC)
        live_event_id: uuid.UUID | None = None

        for fixture_index, (sport_code, sport_name, competition_name, events) in enumerate(
            DEMO_FIXTURES
        ):
            sport = Sport(code=sport_code, name=sport_name)
            session.add(sport)
            await session.flush()

            competition = Competition(sport_id=sport.id, name=competition_name)
            session.add(competition)
            await session.flush()

            for event_index, (event_name, hours_from_now) in enumerate(events):
                names = event_name.split(" vs ")
                event = Event(
                    competition_id=competition.id,
                    name=event_name,
                    start_time=now + datetime.timedelta(hours=hours_from_now),
                )
                session.add(event)
                await session.flush()

                market = Market(
                    event_id=event.id, market_type_id=match_odds_type.id, name="Match Odds"
                )
                market.selections = [
                    Selection(name=names[0], display_order=0),
                    Selection(name=names[1], display_order=1),
                ]
                session.add(market)
                await session.flush()

                is_live_slot = fixture_index == LIVE_SIMULATOR_EVENT_INDEX and event_index == 0
                if is_live_slot:
                    live_event_id = event.id
                else:
                    base_a = Decimal(str(round(random.uniform(1.6, 2.4), 2)))
                    base_b = Decimal(str(round(random.uniform(1.6, 2.4), 2)))
                    bases = {names[0]: base_a, names[1]: base_b}
                    await _seed_two_sided_liquidity(session, market, bases, provider_a, provider_b)

        await session.commit()

    if live_event_id is not None:
        async with AsyncSessionFactory() as session:
            await SimulationEngine(session).start_match(live_event_id)


async def main() -> None:
    await seed_roles()
    await seed_market_types()
    await seed_demo_users()
    await seed_demo_catalog()


if __name__ == "__main__":
    asyncio.run(main())
