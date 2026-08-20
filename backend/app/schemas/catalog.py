from __future__ import annotations

import typing
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

if typing.TYPE_CHECKING:
    from app.models.event import Event
    from app.models.market import Market


class SportCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)


class SportRead(BaseModel):
    id: uuid.UUID
    code: str
    name: str

    model_config = {"from_attributes": True}


class CompetitionCreate(BaseModel):
    sport_id: uuid.UUID
    name: str = Field(min_length=1, max_length=150)


class CompetitionRead(BaseModel):
    id: uuid.UUID
    sport_id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class EventCreate(BaseModel):
    competition_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    start_time: datetime


class EventRead(BaseModel):
    id: uuid.UUID
    competition_id: uuid.UUID
    name: str
    status: str
    start_time: datetime

    @classmethod
    def from_model(cls, event: Event) -> EventRead:
        return cls(
            id=event.id,
            competition_id=event.competition_id,
            name=event.name,
            status=event.status.value,
            start_time=event.start_time,
        )


class MarketTypeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    settlement_rule: dict[str, Any] = Field(default_factory=dict)


class MarketTypeRead(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    settlement_rule: dict[str, Any]

    model_config = {"from_attributes": True}


class SelectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    display_order: int = 0


class SelectionRead(BaseModel):
    id: uuid.UUID
    market_id: uuid.UUID
    name: str
    display_order: int

    model_config = {"from_attributes": True}


class MarketCreate(BaseModel):
    event_id: uuid.UUID
    market_type_id: uuid.UUID
    name: str = Field(min_length=1, max_length=150)
    selections: list[SelectionCreate] = Field(min_length=1)


class MarketRead(BaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    market_type_id: uuid.UUID
    name: str
    status: str
    version: int
    selections: list[SelectionRead]

    @classmethod
    def from_model(cls, market: Market) -> MarketRead:
        return cls(
            id=market.id,
            event_id=market.event_id,
            market_type_id=market.market_type_id,
            name=market.name,
            status=market.status.value,
            version=market.version,
            selections=[SelectionRead.model_validate(s) for s in market.selections],
        )


class EventDetailRead(BaseModel):
    id: uuid.UUID
    competition_id: uuid.UUID
    name: str
    status: str
    start_time: datetime
    markets: list[MarketRead]

    @classmethod
    def from_model(cls, event: Event, markets: list[Market]) -> EventDetailRead:
        return cls(
            id=event.id,
            competition_id=event.competition_id,
            name=event.name,
            status=event.status.value,
            start_time=event.start_time,
            markets=[MarketRead.from_model(m) for m in markets],
        )
