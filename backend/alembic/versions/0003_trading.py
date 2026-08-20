"""trading: orders, order_matches, bets

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("market_id", sa.Uuid(as_uuid=True), sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("selection_id", sa.Uuid(as_uuid=True), sa.ForeignKey("selections.id"), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("price", sa.Numeric(6, 2), nullable=False),
        sa.Column("stake_minor", sa.BigInteger(), nullable=False),
        sa.Column("matched_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="OPEN"),
        sa.Column("idempotency_key", sa.String(length=100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_orders_user_idempotency"),
    )
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_market_id", "orders", ["market_id"])
    op.create_index("ix_orders_selection_id", "orders", ["selection_id"])

    op.create_table(
        "order_matches",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("taker_order_id", sa.Uuid(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("maker_order_id", sa.Uuid(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("matched_price", sa.Numeric(6, 2), nullable=False),
        sa.Column("matched_size_minor", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_order_matches_taker_order_id", "order_matches", ["taker_order_id"])
    op.create_index("ix_order_matches_maker_order_id", "order_matches", ["maker_order_id"])

    op.create_table(
        "bets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("order_id", sa.Uuid(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("order_match_id", sa.Uuid(as_uuid=True), sa.ForeignKey("order_matches.id"), nullable=False),
        sa.Column("market_id", sa.Uuid(as_uuid=True), sa.ForeignKey("markets.id"), nullable=False),
        sa.Column("selection_id", sa.Uuid(as_uuid=True), sa.ForeignKey("selections.id"), nullable=False),
        sa.Column("side", sa.String(length=10), nullable=False),
        sa.Column("price", sa.Numeric(6, 2), nullable=False),
        sa.Column("stake_minor", sa.BigInteger(), nullable=False),
        sa.Column("liability_minor", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="MATCHED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_bets_user_id", "bets", ["user_id"])
    op.create_index("ix_bets_order_id", "bets", ["order_id"])
    op.create_index("ix_bets_order_match_id", "bets", ["order_match_id"])
    op.create_index("ix_bets_market_id", "bets", ["market_id"])
    op.create_index("ix_bets_selection_id", "bets", ["selection_id"])


def downgrade() -> None:
    op.drop_table("bets")
    op.drop_index("ix_order_matches_maker_order_id", table_name="order_matches")
    op.drop_index("ix_order_matches_taker_order_id", table_name="order_matches")
    op.drop_table("order_matches")
    op.drop_index("ix_orders_selection_id", table_name="orders")
    op.drop_index("ix_orders_market_id", table_name="orders")
    op.drop_index("ix_orders_user_id", table_name="orders")
    op.drop_table("orders")
