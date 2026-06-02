"""add chat_conversation + chat_message (website live chat)

Revision ID: c1d2e3f4a5b6
Revises: a1b2c3d4e5f6
Create Date: 2026-06-02 02:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chat_conversation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("locale", sa.String(length=16), nullable=False),
        sa.Column("visitor_name", sa.String(length=255), nullable=False),
        sa.Column("visitor_email", sa.String(length=255), nullable=False),
        sa.Column("last_message_at", sa.DateTime(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("chat_conversation", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_chat_conversation_session_id"), ["session_id"], unique=True)

    op.create_table(
        "chat_message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["chat_conversation.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("chat_message", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_chat_message_conversation_id"), ["conversation_id"], unique=False)


def downgrade():
    with op.batch_alter_table("chat_message", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_chat_message_conversation_id"))
    op.drop_table("chat_message")

    with op.batch_alter_table("chat_conversation", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_chat_conversation_session_id"))
    op.drop_table("chat_conversation")
