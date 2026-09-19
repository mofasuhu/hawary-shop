"""Migration 1751807396341

Revision ID: cc5b1053de5e
Revises: e58dce425491
Create Date: 2025-07-06 17:11:00.048203

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc5b1053de5e'
down_revision = 'e58dce425491'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('governorate_delivery_fee') as batch_op:
        batch_op.alter_column(
            'is_covered',
            existing_type=sa.VARCHAR(length=20),
            type_=sa.Boolean(),
            existing_nullable=False,
            postgresql_using="CASE is_covered WHEN 'covered' THEN TRUE ELSE FALSE END"
        )


def downgrade():
    with op.batch_alter_table('governorate_delivery_fee') as batch_op:
        batch_op.alter_column(
            'is_covered',
            existing_type=sa.Boolean(),
            type_=sa.VARCHAR(length=20),
            existing_nullable=False,
            postgresql_using="CASE WHEN is_covered THEN 'covered' ELSE 'not_covered' END"
        )
