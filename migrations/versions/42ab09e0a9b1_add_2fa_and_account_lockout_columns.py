"""Add 2FA and Account Lockout columns

Revision ID: 42ab09e0a9b1
Revises: 2b1397188a14
Create Date: 2026-05-02 17:26:27.553592

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '42ab09e0a9b1'
down_revision = '2b1397188a14'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('totp_secret', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('failed_login_attempts', sa.Integer(), nullable=True, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('locked_until', postgresql.TIMESTAMP(timezone=True), nullable=True))

def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('locked_until')
        batch_op.drop_column('failed_login_attempts')
        batch_op.drop_column('totp_secret')
