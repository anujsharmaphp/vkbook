"""Seeds baseline reference data (roles, market types). Run with:
python -m app.db.seed

Sport/competition/event/market instance data (e.g. "England vs Pakistan") and
demo-user wallet funding are seeded by the simulator (Step 9) and wallet
engine (Step 5) respectively — this script only seeds catalog *types* that
the admin/simulator later builds instances from.
"""

import asyncio

from sqlalchemy import select

from app.db.session import AsyncSessionFactory
from app.models.market_type import MarketType
from app.models.role import Role

DEFAULT_ROLES = [
    ("user", "Standard User"),
    ("admin", "Administrator"),
]

# settlement_rule is intentionally generic — the settlement engine (Step 9)
# interprets "kind" to resolve a market without per-market-type code paths.
DEFAULT_MARKET_TYPES = [
    ("MATCH_ODDS", "Match Odds", {"kind": "WINNER_TAKES_ALL"}),
    ("BOOKMAKER", "Bookmaker", {"kind": "WINNER_TAKES_ALL"}),
    ("OVER_UNDER", "Over/Under", {"kind": "OVER_UNDER_LINE"}),
]


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


async def main() -> None:
    await seed_roles()
    await seed_market_types()


if __name__ == "__main__":
    asyncio.run(main())
