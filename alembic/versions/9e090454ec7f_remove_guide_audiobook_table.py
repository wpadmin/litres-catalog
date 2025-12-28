"""remove guide_audiobook table

Revision ID: 9e090454ec7f
Revises: 5c824c86b770
Create Date: 2025-12-28 11:05:55.125730

"""
from alembic import op
import sqlalchemy as sa


revision = '9e090454ec7f'
down_revision = '5c824c86b770'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('guide_audiobook')


def downgrade() -> None:
    op.create_table(
        'guide_audiobook',
        sa.Column('guide_id', sa.Integer(), nullable=False),
        sa.Column('audiobook_id', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['audiobook_id'], ['audiobooks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['guide_id'], ['guides.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('guide_id', 'audiobook_id')
    )
