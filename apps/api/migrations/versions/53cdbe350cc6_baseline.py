"""baseline

Revision ID: 53cdbe350cc6
Revises:
Create Date: 2026-10-25 23:17:37.368158

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "53cdbe350cc6"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
