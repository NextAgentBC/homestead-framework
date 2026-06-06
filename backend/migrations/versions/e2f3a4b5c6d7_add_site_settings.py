"""add site_settings (runtime brand/industry/audience/assistant identity)

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-06-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2f3a4b5c6d7'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "site_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("industry", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("audience", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("region", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("assistant_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("site_settings")
