"""add unique open order per table

Revision ID: b9e01347187a
Revises: a1d908c26e73
Create Date: 2026-10-20 14:26:16.699653

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b9e01347187a"
down_revision: str | Sequence[str] | None = "a1d908c26e73"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_open_order_per_table",
        "orders",
        ["table_id"],
        unique=True,
        postgresql_where=sa.text("status = 'OPEN'"),
    )


def downgrade() -> None:
    op.drop_index("uq_open_order_per_table", table_name="orders")
