import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class LedgerEntryType(str, enum.Enum):
    INITIAL_GRANT = "INITIAL_GRANT"
    EXPOSURE_HOLD = "EXPOSURE_HOLD"
    EXPOSURE_RELEASE = "EXPOSURE_RELEASE"
    SETTLEMENT_WIN = "SETTLEMENT_WIN"
    SETTLEMENT_LOSS = "SETTLEMENT_LOSS"
    SETTLEMENT_VOID = "SETTLEMENT_VOID"


class LedgerEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Immutable, append-only record of every wallet mutation. Both
    balance_delta and reserved_delta may be non-zero on one entry (a
    settlement, added in Step 9, realizes profit/loss *and* releases the
    matching exposure hold in a single atomic entry). Uniquely keyed by
    idempotency_key so a retried operation can never double-apply.
    """

    __tablename__ = "ledger_entries"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_ledger_entries_idempotency_key"),
    )

    wallet_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("wallets.id"), nullable=False, index=True
    )
    ref_order_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("orders.id"), nullable=True, index=True
    )
    ref_bet_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("bets.id"), nullable=True, index=True
    )
    entry_type: Mapped[LedgerEntryType] = mapped_column(
        SqlEnum(LedgerEntryType, native_enum=False, length=20), nullable=False
    )
    balance_delta_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    reserved_delta_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    balance_after_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reserved_after_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(150), nullable=False)
