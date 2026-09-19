"""Migration 1751803244038

Revision ID: 5fbfdb80ebcb
Revises: f1cd86dcbd1b
Create Date: 2025-07-06 16:01:59.962533

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5fbfdb80ebcb'
down_revision = 'f1cd86dcbd1b'
branch_labels = None
depends_on = None


def upgrade():
    # No changes needed for is_covered since it's still Boolean
    pass


def downgrade():
    # No changes to undo
    pass
