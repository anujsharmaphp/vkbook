import enum
import uuid
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class OrderSide(str, enum.Enum):
    BACK = "BACK"
    LAY = "LAY"


class OrderStatus(str, enum.Enum):
    OPEN = "OPEN"
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"
    MATCHED = "MATCHED"
    CANCELLED = "CANCELLED"


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A resting/working limit order in one market's BACK/LAY order book.

    `price` is decimal odds. For a BACK order it is the *minimum* odds the
    owner will accept; for a LAY order it is the *maximum* odds (liability
    ceiling) the owner will accept. See MatchingService for the full
    crossing-condition derivation and match-priority rules.
    """

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_orders_user_idempotency"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    market_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("markets.id"), nullable=False, index=True
    )
    selection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("selections.id"), nullable=False, index=True
    )
    side: Mapped[OrderSide] = mapped_column(
        SqlEnum(OrderSide, native_enum=False, length=10), nullable=False
    )
    price: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    stake_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    matched_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    status: Mapped[OrderStatus] = mapped_column(
        SqlEnum(OrderStatus, native_enum=False, length=20), default=OrderStatus.OPEN, nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(100), nullable=False)
    # Bumped by SQLAlchemy on every UPDATE (Section 22) — every match this
    # order takes part in, as either taker or maker, advances its version.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __mapper_args__ = {"version_id_col": version}

    @property
    def remaining_minor(self) -> int:
        return self.stake_minor - self.matched_minor
