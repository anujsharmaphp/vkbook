import uuid

from sqlalchemy import BigInteger, ForeignKey, Integer, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Wallet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user's paper-money wallet. `balance_minor`/`reserved_minor` are a
    materialized cache of LedgerEntry rows (the ledger is the source of
    truth) — see docs/architecture.md Section G. `available_minor` =
    balance - reserved is what "Available to Bet" shows in the UI.
    """

    __tablename__ = "wallets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    balance_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    reserved_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __mapper_args__ = {"version_id_col": version}

    @property
    def available_minor(self) -> int:
        return self.balance_minor - self.reserved_minor
