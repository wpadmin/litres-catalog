"""add performance indexes

Revision ID: 8c06490c0126
Revises: 34ca66154a7b
Create Date: 2025-12-27 20:42:51.561234

"""
from alembic import op
import sqlalchemy as sa


revision = '8c06490c0126'
down_revision = '34ca66154a7b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_audiobooks_created_at', 'audiobooks', ['created_at'], unique=False)
    op.create_index('ix_audiobook_author_author_id', 'audiobook_author', ['author_id'], unique=False)
    op.create_index('ix_audiobook_author_audiobook_id', 'audiobook_author', ['audiobook_id'], unique=False)
    op.create_index('ix_audiobook_genre_audiobook_id', 'audiobook_genre', ['audiobook_id'], unique=False)
    op.create_index('ix_audiobook_genre_genre_id', 'audiobook_genre', ['genre_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_audiobook_genre_genre_id', table_name='audiobook_genre')
    op.drop_index('ix_audiobook_genre_audiobook_id', table_name='audiobook_genre')
    op.drop_index('ix_audiobook_author_audiobook_id', table_name='audiobook_author')
    op.drop_index('ix_audiobook_author_author_id', table_name='audiobook_author')
    op.drop_index('ix_audiobooks_created_at', table_name='audiobooks')
