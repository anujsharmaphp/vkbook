import uuid
from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class OrderMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "order_matches"

    taker_order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    maker_order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("orders.id"), nullable=False, index=True
    )
    matched_price: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    matched_size_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
