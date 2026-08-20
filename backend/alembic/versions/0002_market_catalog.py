"""market catalog: sports, competitions, events, market_types, markets, selections

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sports",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sports_code", "sports", ["code"], unique=True)

    op.create_table(
        "competitions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("sport_id", sa.Uuid(as_uuid=True), sa.ForeignKey("sports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_competitions_sport_id", "competitions", ["sport_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "competition_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("competitions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="SCHEDULED"),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_events_competition_id", "events", ["competition_id"])

    op.create_table(
        "market_types",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column(
            "settlement_rule",
            sa.JSON().with_variant(postgresql.JSONB, "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_market_types_code", "market_types", ["code"], unique=True)

    op.create_table(
        "markets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("event_id", sa.Uuid(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("market_type_id", sa.Uuid(as_uuid=True), sa.ForeignKey("market_types.id"), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_markets_event_id", "markets", ["event_id"])
    op.create_index("ix_markets_market_type_id", "markets", ["market_type_id"])

    op.create_table(
        "selections",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("market_id", sa.Uuid(as_uuid=True), sa.ForeignKey("markets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_selections_market_id", "selections", ["market_id"])


def downgrade() -> None:
    op.drop_table("selections")
    op.drop_index("ix_markets_market_type_id", table_name="markets")
    op.drop_index("ix_markets_event_id", table_name="markets")
    op.drop_table("markets")
    op.drop_index("ix_market_types_code", table_name="market_types")
    op.drop_table("market_types")
    op.drop_index("ix_events_competition_id", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_competitions_sport_id", table_name="competitions")
    op.drop_table("competitions")
    op.drop_index("ix_sports_code", table_name="sports")
    op.drop_table("sports")
