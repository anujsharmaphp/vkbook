import enum
import uuid
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, Uuid
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.order import OrderSide


class BetStatus(str, enum.Enum):
    MATCHED = "MATCHED"
    SETTLED = "SETTLED"
    VOID = "VOID"


class Bet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One side of a single match fill — the user-facing unit of exposure
    shown on "My Bets". Every OrderMatch produces exactly two Bet rows: one
    BACK bet (for the back order's owner) and one LAY bet (for the lay
    order's owner), both at the matched price and size. Settlement (Step 9)
    transitions status MATCHED -> SETTLED/VOID and posts wallet ledger
    entries; nothing here touches the wallet yet (Step 5).
    """

    __tablename__ = "bets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    order_match_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("order_matches.id"), nullable=False, index=True
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
    liability_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[BetStatus] = mapped_column(
        SqlEnum(BetStatus, native_enum=False, length=20), default=BetStatus.MATCHED, nullable=False
    )
