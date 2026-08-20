from __future__ import annotations

import typing
import uuid
from datetime import datetime

from pydantic import BaseModel

if typing.TYPE_CHECKING:
    from app.models.ledger_entry import LedgerEntry
    from app.models.wallet import Wallet


class WalletRead(BaseModel):
    balance_minor: int
    reserved_minor: int
    available_minor: int

    @classmethod
    def from_model(cls, wallet: Wallet) -> WalletRead:
        return cls(
            balance_minor=wallet.balance_minor,
            reserved_minor=wallet.reserved_minor,
            available_minor=wallet.available_minor,
        )


class LedgerEntryRead(BaseModel):
    id: uuid.UUID
    entry_type: str
    balance_delta_minor: int
    reserved_delta_minor: int
    balance_after_minor: int
    reserved_after_minor: int
    ref_order_id: uuid.UUID | None
    ref_bet_id: uuid.UUID | None
    created_at: datetime

    @classmethod
    def from_model(cls, entry: LedgerEntry) -> LedgerEntryRead:
        return cls(
            id=entry.id,
            entry_type=entry.entry_type.value,
            balance_delta_minor=entry.balance_delta_minor,
            reserved_delta_minor=entry.reserved_delta_minor,
            balance_after_minor=entry.balance_after_minor,
            reserved_after_minor=entry.reserved_after_minor,
            ref_order_id=entry.ref_order_id,
            ref_bet_id=entry.ref_bet_id,
            created_at=entry.created_at,
        )
