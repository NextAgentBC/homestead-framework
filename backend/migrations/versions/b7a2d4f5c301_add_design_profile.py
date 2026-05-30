"""add design profile

Revision ID: b7a2d4f5c301
Revises: 695db24c1404
Create Date: 2026-05-30 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b7a2d4f5c301"
down_revision = "695db24c1404"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "design_profile",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("personality", sa.Text(), nullable=False),
        sa.Column("competitor_urls", sa.JSON(), nullable=False),
        sa.Column("tokens", sa.JSON(), nullable=False),
        sa.Column("voice", sa.JSON(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_design_profile_status"), "design_profile", ["status"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_design_profile_status"), table_name="design_profile")
    op.drop_table("design_profile")

