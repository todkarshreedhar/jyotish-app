"""push tokens for the mobile app

Revision ID: b1c4e2f0a9d3
Revises: 7af686d6e748
Create Date: 2026-10-28 18:40:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b1c4e2f0a9d3"
down_revision: str | Sequence[str] | None = "7af686d6e748"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "push_tokens",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token", sa.String(length=200), nullable=False),
        sa.Column("platform", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_push_tokens_user_id"), "push_tokens", ["user_id"], unique=False)
    op.add_column("alert_prefs", sa.Column("push_enabled", sa.Boolean(), server_default="true", nullable=False))


def downgrade() -> None:
    op.drop_column("alert_prefs", "push_enabled")
    op.drop_index(op.f("ix_push_tokens_user_id"), table_name="push_tokens")
    op.drop_table("push_tokens")
