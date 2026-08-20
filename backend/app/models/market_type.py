from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MarketType(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Classifies a Market (MATCH_ODDS, BOOKMAKER, FANCY, PLAYER_RUNS,
    OVER_UNDER, WICKETS, ...). settlement_rule is a generic, data-driven
    description of how the settlement engine (Step 9) resolves this market
    type, so adding a new market type is a data operation, not new code."""

    __tablename__ = "market_types"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    settlement_rule: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict
    )
