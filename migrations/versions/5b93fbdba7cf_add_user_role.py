"""add user role

Revision ID: 5b93fbdba7cf
Revises: 0e6d82129786
Create Date: 2026-05-03 23:09:38.488303
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "5b93fbdba7cf"
down_revision = "0e6d82129786"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add role column to users table.
    Default role = 'user' for all existing rows.
    """
    # 1) add column with server_default so existing rows can be updated safely
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
    )

    # 2) ensure existing records have role=user
    op.execute("UPDATE users SET role='user' WHERE role IS NULL")

    # 3) remove server default (optional; keeps schema clean)
    op.alter_column("users", "role", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "role")
