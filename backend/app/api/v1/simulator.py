import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.user import User
from app.schemas.simulator import MatchStateRead, SimulatorLogEntryRead
from app.security.dependencies import require_role
from app.services.simulation_runner import start_simulation_task, stop_simulation_task
from app.services.simulation_service import SimulationEngine

router = APIRouter(prefix="/admin/simulator", tags=["admin", "simulator"])

_require_admin = require_role("admin")


@router.post("/events/{event_id}/start", response_model=MatchStateRead)
async def start_match(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> MatchStateRead:
    state = await SimulationEngine(db).start_match(event_id)
    start_simulation_task(event_id)
    return MatchStateRead.from_model(state)


@router.post("/events/{event_id}/pause", response_model=MatchStateRead)
async def pause_match(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> MatchStateRead:
    stop_simulation_task(event_id)
    state = await SimulationEngine(db).pause_match(event_id)
    return MatchStateRead.from_model(state)


@router.post("/events/{event_id}/resume", response_model=MatchStateRead)
async def resume_match(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> MatchStateRead:
    state = await SimulationEngine(db).resume_match(event_id)
    start_simulation_task(event_id)
    return MatchStateRead.from_model(state)


@router.post("/events/{event_id}/finish", response_model=MatchStateRead)
async def finish_match(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> MatchStateRead:
    stop_simulation_task(event_id)
    state = await SimulationEngine(db).finish_match(event_id)
    return MatchStateRead.from_model(state)


@router.post("/events/{event_id}/tick", response_model=MatchStateRead)
async def force_tick(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> MatchStateRead:
    """Manually advance one ball — useful for deterministic demos/tests
    without waiting on the background loop's interval."""
    engine = SimulationEngine(db)
    await engine.tick(event_id)
    state = await engine.get_state(event_id)
    return MatchStateRead.from_model(state)


@router.get("/events/{event_id}/log", response_model=list[SimulatorLogEntryRead])
async def get_log(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(_require_admin),
) -> list[SimulatorLogEntryRead]:
    entries = await SimulationEngine(db).list_log(event_id)
    return [SimulatorLogEntryRead.from_model(e) for e in entries]
