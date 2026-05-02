"""Initial migration: create check_results table.

Revision ID: a1b2c3d4e5f6
Revises: None
Create Date: 2026-05-01 00:00:00.000000

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the check_results table."""
    op.create_table(
        "check_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_name", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("response_time_ms", sa.Float(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("checked_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_check_results_service_name"),
        "check_results",
        ["service_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_check_results_checked_at"),
        "check_results",
        ["checked_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the check_results table."""
    op.drop_index(op.f("ix_check_results_checked_at"), table_name="check_results")
    op.drop_index(op.f("ix_check_results_service_name"), table_name="check_results")
    op.drop_table("check_results")
