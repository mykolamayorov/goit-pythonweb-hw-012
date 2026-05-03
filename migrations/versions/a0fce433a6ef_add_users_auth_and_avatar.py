"""add users auth and avatar

Revision ID: a0fce433a6ef
Revises: 042b9dc530d1
Create Date: 2026-05-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a0fce433a6ef"
down_revision = "042b9dc530d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 2) Make migration safe if contacts already had rows:
    # create a dummy user and assign NULL contacts.user_id to it.
    # (This prevents failure when adding NOT NULL user_id.)
    op.execute(
        "INSERT INTO users (email, hashed_password, is_verified) "
        "VALUES ('migration@local', '!', false) "
        "ON CONFLICT (email) DO NOTHING"
    )

    # 3) Add user_id column to contacts (initially nullable)
    op.add_column("contacts", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_contacts_user_id", "contacts", ["user_id"], unique=False)
    op.create_foreign_key(
        "contacts_user_id_fkey",
        "contacts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 4) Backfill user_id for existing contacts (if any)
    op.execute(
        "UPDATE contacts "
        "SET user_id = (SELECT id FROM users WHERE email='migration@local' LIMIT 1) "
        "WHERE user_id IS NULL"
    )

    # 5) Now enforce NOT NULL
    op.alter_column("contacts", "user_id", nullable=False)


def downgrade() -> None:
    # Reverse order
    op.alter_column("contacts", "user_id", nullable=True)
    op.drop_constraint("contacts_user_id_fkey", "contacts", type_="foreignkey")
    op.drop_index("ix_contacts_user_id", table_name="contacts")
    op.drop_column("contacts", "user_id")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")