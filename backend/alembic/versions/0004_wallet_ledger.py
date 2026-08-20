"""wallet ledger: wallets, ledger_entries

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-20

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wallets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("balance_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("reserved_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_wallets_user_id", "wallets", ["user_id"], unique=True)

    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("wallet_id", sa.Uuid(as_uuid=True), sa.ForeignKey("wallets.id"), nullable=False),
        sa.Column("ref_order_id", sa.Uuid(as_uuid=True), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("ref_bet_id", sa.Uuid(as_uuid=True), sa.ForeignKey("bets.id"), nullable=True),
        sa.Column("entry_type", sa.String(length=20), nullable=False),
        sa.Column("balance_delta_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("reserved_delta_minor", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("balance_after_minor", sa.BigInteger(), nullable=False),
        sa.Column("reserved_after_minor", sa.BigInteger(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_ledger_entries_idempotency_key"),
    )
    op.create_index("ix_ledger_entries_wallet_id", "ledger_entries", ["wallet_id"])
    op.create_index("ix_ledger_entries_ref_order_id", "ledger_entries", ["ref_order_id"])
    op.create_index("ix_ledger_entries_ref_bet_id", "ledger_entries", ["ref_bet_id"])


def downgrade() -> None:
    op.drop_table("ledger_entries")
    op.drop_index("ix_wallets_user_id", table_name="wallets")
    op.drop_table("wallets")
