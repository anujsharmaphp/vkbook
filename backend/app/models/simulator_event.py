import enum
import uuid
from typing import Any

from sqlalchemy import JSON, ForeignKey, Uuid
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SimulatorEventType(str, enum.Enum):
    MATCH_STARTED = "MATCH_STARTED"
    BALL = "BALL"
    MARKET_SUSPENDED = "MARKET_SUSPENDED"
    MARKET_REOPENED = "MARKET_REOPENED"
    MATCH_COMPLETED = "MATCH_COMPLETED"


class SimulatorEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Append-only audit log of every simulated match event — the raw feed
    MatchState is derived from. Kept as its own table (per the master
    prompt's core table list) so a match's play-by-play can be replayed or
    inspected independent of the current-state snapshot."""

    __tablename__ = "simulator_events"

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True
    )
    event_type: Mapped[SimulatorEventType] = mapped_column(
        SqlEnum(SimulatorEventType, native_enum=False, length=20), nullable=False
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict
    )
