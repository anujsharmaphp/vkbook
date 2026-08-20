"""simulator: match_states, simulator_events

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "match_states",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.Uuid(as_uuid=True), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("batting_team", sa.String(length=150), nullable=False),
        sa.Column("bowling_team", sa.String(length=150), nullable=False),
        sa.Column("target_runs", sa.Integer(), nullable=False),
        sa.Column("max_overs", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("runs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wickets", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("balls_bowled", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="SCHEDULED"),
        sa.Column("markets_suspended", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("winner_team", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_match_states_event_id", "match_states", ["event_id"], unique=True)

    op.create_table(
        "simulator_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.Uuid(as_uuid=True), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column(
            "payload",
            sa.JSON().with_variant(postgresql.JSONB, "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_simulator_events_event_id", "simulator_events", ["event_id"])


def downgrade() -> None:
    op.drop_table("simulator_events")
    op.drop_index("ix_match_states_event_id", table_name="match_states")
    op.drop_table("match_states")
