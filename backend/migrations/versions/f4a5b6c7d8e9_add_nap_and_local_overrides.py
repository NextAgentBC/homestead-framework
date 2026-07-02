"""add NAP columns to site_settings + page local_business_overrides

Revision ID: f4a5b6c7d8e9
Revises: e2f3a4b5c6d7
Create Date: 2026-07-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f4a5b6c7d8e9'
down_revision = 'e2f3a4b5c6d7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('site_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('legal_name', sa.String(length=255), nullable=False, server_default=""))
        batch_op.add_column(sa.Column('phone', sa.String(length=255), nullable=False, server_default=""))
        batch_op.add_column(sa.Column('email', sa.String(length=255), nullable=False, server_default=""))
        batch_op.add_column(sa.Column('address_street', sa.String(length=255), nullable=False, server_default=""))
        batch_op.add_column(sa.Column('address_city', sa.String(length=255), nullable=False, server_default=""))
        batch_op.add_column(sa.Column('address_region', sa.String(length=255), nullable=False, server_default=""))
        batch_op.add_column(sa.Column('address_postal_code', sa.String(length=255), nullable=False, server_default=""))
        batch_op.add_column(sa.Column('address_country', sa.String(length=255), nullable=False, server_default=""))
        batch_op.add_column(sa.Column('latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('longitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('business_hours', sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
        batch_op.add_column(sa.Column('service_areas', sa.JSON(), nullable=False, server_default=sa.text("'[]'")))

    with op.batch_alter_table('page', schema=None) as batch_op:
        batch_op.add_column(sa.Column('local_business_overrides', sa.JSON(), nullable=False, server_default=sa.text("'{}'")))


def downgrade():
    with op.batch_alter_table('page', schema=None) as batch_op:
        batch_op.drop_column('local_business_overrides')

    with op.batch_alter_table('site_settings', schema=None) as batch_op:
        batch_op.drop_column('service_areas')
        batch_op.drop_column('business_hours')
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')
        batch_op.drop_column('address_country')
        batch_op.drop_column('address_postal_code')
        batch_op.drop_column('address_region')
        batch_op.drop_column('address_city')
        batch_op.drop_column('address_street')
        batch_op.drop_column('email')
        batch_op.drop_column('phone')
        batch_op.drop_column('legal_name')
