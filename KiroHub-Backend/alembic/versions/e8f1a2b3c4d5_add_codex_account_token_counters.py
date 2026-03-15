"""add_codex_account_token_counters

Revision ID: e8f1a2b3c4d5
Revises: d2a4f3b7c9e1
Create Date: 2026-01-22

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8f1a2b3c4d5"
down_revision: Union[str, None] = "d2a4f3b7c9e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "codex_accounts",
        sa.Column("consumed_input_tokens", sa.BigInteger(), server_default="0", nullable=False),
    )
    op.add_column(
        "codex_accounts",
        sa.Column("consumed_output_tokens", sa.BigInteger(), server_default="0", nullable=False),
    )
    op.add_column(
        "codex_accounts",
        sa.Column("consumed_cached_tokens", sa.BigInteger(), server_default="0", nullable=False),
    )
    op.add_column(
        "codex_accounts",
        sa.Column("consumed_total_tokens", sa.BigInteger(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("codex_accounts", "consumed_total_tokens")
    op.drop_column("codex_accounts", "consumed_cached_tokens")
    op.drop_column("codex_accounts", "consumed_output_tokens")
    op.drop_column("codex_accounts", "consumed_input_tokens")

