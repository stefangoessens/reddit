"""Add price_at_mention to mention_events."""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20250211_1245"
down_revision = "20250211_1200"
branch_labels = None
dependent_revisions = None


def upgrade() -> None:
    op.add_column("mention_events", sa.Column("price_at_mention", sa.Numeric(18, 6), nullable=True))


def downgrade() -> None:
    op.drop_column("mention_events", "price_at_mention")
