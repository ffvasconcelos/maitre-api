"""add positive table number constraint

Revision ID: c7a48e392fd1
Revises: b9e01347187a
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c7a48e392fd1"
down_revision: str | Sequence[str] | None = "b9e01347187a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint("check_table_number_gt_0", "tables", "number > 0")


def downgrade() -> None:
    op.drop_constraint("check_table_number_gt_0", "tables", type_="check")
