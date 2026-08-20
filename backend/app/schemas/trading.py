from __future__ import annotations

import typing
import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

if typing.TYPE_CHECKING:
    from app.models.bet import Bet
    from app.models.order import Order


class OrderCreate(BaseModel):
    market_id: uuid.UUID
    selection_id: uuid.UUID
    side: Literal["BACK", "LAY"]
    price: Decimal = Field(gt=1, le=1000, decimal_places=2)
    stake_minor: int = Field(gt=0)
    idempotency_key: str = Field(min_length=1, max_length=100)


class OrderRead(BaseModel):
    id: uuid.UUID
    market_id: uuid.UUID
    selection_id: uuid.UUID
    side: str
    price: Decimal
    stake_minor: int
    matched_minor: int
    remaining_minor: int
    status: str

    @classmethod
    def from_model(cls, order: Order) -> OrderRead:
        return cls(
            id=order.id,
            market_id=order.market_id,
            selection_id=order.selection_id,
            side=order.side.value,
            price=order.price,
            stake_minor=order.stake_minor,
            matched_minor=order.matched_minor,
            remaining_minor=order.remaining_minor,
            status=order.status.value,
        )


class BetRead(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    market_id: uuid.UUID
    selection_id: uuid.UUID
    side: str
    price: Decimal
    stake_minor: int
    liability_minor: int
    status: str

    @classmethod
    def from_model(cls, bet: Bet) -> BetRead:
        return cls(
            id=bet.id,
            order_id=bet.order_id,
            market_id=bet.market_id,
            selection_id=bet.selection_id,
            side=bet.side.value,
            price=bet.price,
            stake_minor=bet.stake_minor,
            liability_minor=bet.liability_minor,
            status=bet.status.value,
        )


class OrderBookLevel(BaseModel):
    price: Decimal
    available_size_minor: int


class OrderBookSelection(BaseModel):
    selection_id: uuid.UUID
    back: list[OrderBookLevel]
    lay: list[OrderBookLevel]


class OrderBookRead(BaseModel):
    market_id: uuid.UUID
    selections: list[OrderBookSelection]
