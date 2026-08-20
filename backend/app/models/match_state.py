import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Uuid
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MatchSimStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class MatchState(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Live state for a simulated single-innings limit-overs chase — the
    simplified match model the simulator plays out. One row per Event.
    `batting_team`/`bowling_team` are matched against Selection.name (not
    selection ids) so the same simulator drives every market on the event
    that shares those two selection names, however many exist.
    """

    __tablename__ = "match_states"

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("events.id"), nullable=False, unique=True, index=True
    )
    batting_team: Mapped[str] = mapped_column(String(150), nullable=False)
    bowling_team: Mapped[str] = mapped_column(String(150), nullable=False)
    target_runs: Mapped[int] = mapped_column(Integer, nullable=False)
    max_overs: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wickets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    balls_bowled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[MatchSimStatus] = mapped_column(
        SqlEnum(MatchSimStatus, native_enum=False, length=20),
        default=MatchSimStatus.SCHEDULED,
        nullable=False,
    )
    markets_suspended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    winner_team: Mapped[str | None] = mapped_column(String(150), nullable=True)

    @property
    def overs_display(self) -> str:
        return f"{self.balls_bowled // 6}.{self.balls_bowled % 6}"

    @property
    def balls_remaining(self) -> int:
        return max(self.max_overs * 6 - self.balls_bowled, 0)

    @property
    def wickets_remaining(self) -> int:
        return max(10 - self.wickets, 0)

    @property
    def runs_needed(self) -> int:
        return max(self.target_runs - self.runs, 0)
