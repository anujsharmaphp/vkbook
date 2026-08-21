import asyncio
import logging
import uuid

from app.db.session import AsyncSessionFactory
from app.services.simulation_service import SimulationEngine

logger = logging.getLogger("app.simulator")

TICK_INTERVAL_SECONDS = 4.0

_running_tasks: dict[uuid.UUID, asyncio.Task] = {}


async def _run_loop(event_id: uuid.UUID) -> None:
    # natural_completion only flips True when tick() itself reports the
    # match is over. On cancellation (admin pause/stop) this code never runs
    # at all — the CancelledError propagates past it — so a manual stop
    # never triggers an auto-restart, only the match actually finishing does.
    natural_completion = False
    try:
        while True:
            await asyncio.sleep(TICK_INTERVAL_SECONDS)
            finished = True
            async with AsyncSessionFactory() as session:
                try:
                    finished = await SimulationEngine(session).tick(event_id)
                except Exception:
                    logger.exception("simulator tick failed for event %s", event_id)
                    finished = False
            if finished:
                natural_completion = True
                break
    finally:
        _running_tasks.pop(event_id, None)

    if natural_completion:
        asyncio.create_task(_auto_start_next_demo_match())


async def _auto_start_next_demo_match() -> None:
    async with AsyncSessionFactory() as session:
        try:
            state = await SimulationEngine(session).start_next_demo_match()
        except Exception:
            logger.exception("failed to auto-start next demo match")
            return
    if state is not None:
        start_simulation_task(state.event_id)


def start_simulation_task(event_id: uuid.UUID) -> None:
    """No-op if a loop for this event is already running — starting the
    match twice must not spawn a second driver."""
    if event_id in _running_tasks:
        return
    _running_tasks[event_id] = asyncio.create_task(_run_loop(event_id))


def stop_simulation_task(event_id: uuid.UUID) -> None:
    task = _running_tasks.pop(event_id, None)
    if task is not None:
        task.cancel()


def is_running(event_id: uuid.UUID) -> bool:
    return event_id in _running_tasks
