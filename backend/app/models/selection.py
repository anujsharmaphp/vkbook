import typing
import uuid

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if typing.TYPE_CHECKING:
    from app.models.market import Market


class Selection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "selections"

    market_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    market: Mapped["Market"] = relationship(back_populates="selections")
