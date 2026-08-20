from __future__ import annotations

import typing
import uuid
from datetime import datetime

from pydantic import BaseModel

if typing.TYPE_CHECKING:
    from app.models.match_state import MatchState
    from app.models.simulator_event import SimulatorEvent


class MatchStateRead(BaseModel):
    event_id: uuid.UUID
    status: str
    batting_team: str
    bowling_team: str
    runs: int
    wickets: int
    overs: str
    max_overs: int
    target_runs: int
    markets_suspended: bool
    winner_team: str | None

    @classmethod
    def from_model(cls, state: MatchState) -> MatchStateRead:
        return cls(
            event_id=state.event_id,
            status=state.status.value,
            batting_team=state.batting_team,
            bowling_team=state.bowling_team,
            runs=state.runs,
            wickets=state.wickets,
            overs=state.overs_display,
            max_overs=state.max_overs,
            target_runs=state.target_runs,
            markets_suspended=state.markets_suspended,
            winner_team=state.winner_team,
        )


class SimulatorLogEntryRead(BaseModel):
    id: uuid.UUID
    event_type: str
    payload: dict
    created_at: datetime

    @classmethod
    def from_model(cls, entry: SimulatorEvent) -> SimulatorLogEntryRead:
        return cls(
            id=entry.id,
            event_type=entry.event_type.value,
            payload=entry.payload,
            created_at=entry.created_at,
        )
