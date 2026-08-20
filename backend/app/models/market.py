import enum
import typing
import uuid

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if typing.TYPE_CHECKING:
    from app.models.selection import Selection


class MarketStatus(str, enum.Enum):
    OPEN = "OPEN"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"
    SETTLED = "SETTLED"


class Market(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "markets"

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    market_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("market_types.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[MarketStatus] = mapped_column(
        SqlEnum(MarketStatus, native_enum=False, length=20),
        default=MarketStatus.OPEN,
        nullable=False,
    )
    # Bumped automatically by SQLAlchemy's version_id_col on every UPDATE; a
    # concurrent writer working off a stale version gets StaleDataError
    # instead of silently clobbering the other transition (Section 22).
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    selections: Mapped[list["Selection"]] = relationship(
        back_populates="market",
        order_by="Selection.display_order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    __mapper_args__ = {"version_id_col": version}
