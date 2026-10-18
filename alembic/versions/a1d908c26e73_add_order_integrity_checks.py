"""add order integrity checks

Revision ID: a1d908c26e73
Revises: f03f4d0e936f
Create Date: 2026-10-18 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1d908c26e73"
down_revision: str | Sequence[str] | None = "f03f4d0e936f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "check_quantity_gt_0", "order_items", "quantity > 0"
    )
    op.create_check_constraint(
        "check_capacity_number_gt_0", "tables", "capacity > 0"
    )


def downgrade() -> None:
    op.drop_constraint("check_capacity_number_gt_0", "tables", type_="check")
    op.drop_constraint("check_quantity_gt_0", "order_items", type_="check")