"""Import every model module so Base.metadata is fully populated before
Alembic (or Base.metadata.create_all in tests) inspects it."""

from app.models.bet import Bet, BetStatus
from app.models.competition import Competition
from app.models.event import Event, EventStatus
from app.models.ledger_entry import LedgerEntry, LedgerEntryType
from app.models.market import Market, MarketStatus
from app.models.market_type import MarketType
from app.models.match_state import MatchSimStatus, MatchState
from app.models.order import Order, OrderSide, OrderStatus
from app.models.order_match import OrderMatch
from app.models.permission import Permission, role_permissions
from app.models.role import Role, user_roles
from app.models.selection import Selection
from app.models.simulator_event import SimulatorEvent, SimulatorEventType
from app.models.sport import Sport
from app.models.user import User, UserStatus
from app.models.wallet import Wallet

__all__ = [
    "Bet",
    "BetStatus",
    "Competition",
    "Event",
    "EventStatus",
    "LedgerEntry",
    "LedgerEntryType",
    "Market",
    "MarketStatus",
    "MarketType",
    "MatchSimStatus",
    "MatchState",
    "Order",
    "OrderMatch",
    "OrderSide",
    "OrderStatus",
    "Permission",
    "role_permissions",
    "Role",
    "user_roles",
    "Selection",
    "SimulatorEvent",
    "SimulatorEventType",
    "Sport",
    "User",
    "UserStatus",
    "Wallet",
]
