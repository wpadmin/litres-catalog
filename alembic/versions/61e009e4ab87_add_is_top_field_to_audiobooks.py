"""add is_top field to audiobooks

Revision ID: 61e009e4ab87
Revises: 8c06490c0126
Create Date: 2025-12-27 21:14:01.467292

"""
from alembic import op
import sqlalchemy as sa


revision = '61e009e4ab87'
down_revision = '8c06490c0126'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('audiobooks', sa.Column('is_top', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('ix_audiobooks_is_top', 'audiobooks', ['is_top'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_audiobooks_is_top', table_name='audiobooks')
    op.drop_column('audiobooks', 'is_top')
