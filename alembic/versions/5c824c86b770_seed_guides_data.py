"""seed guides data

Revision ID: 5c824c86b770
Revises: 8a881594c8f8
Create Date: 2025-12-28 10:50:40.490319

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


revision = '5c824c86b770'
down_revision = '8a881594c8f8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Создаём таблицы для работы с данными
    guides_table = sa.table(
        'guides',
        sa.column('slug', sa.String),
        sa.column('title', sa.String),
        sa.column('description', sa.Text),
        sa.column('md_file', sa.String),
        sa.column('views', sa.Integer),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )

    # Вставляем записи подборок
    op.bulk_insert(
        guides_table,
        [
            {
                'slug': 'transerfing-dlya-nachinayuschih',
                'title': 'Трансерфинг для начинающих: с чего начать управлять реальностью',
                'description': 'Полный гид по книгам Вадима Зеланда: с каких ступеней начать, какие ошибки избежать и как Трансерфинг меняет жизнь. Для тех, кто хочет управлять реальностью.',
                'md_file': 'transerfing-dlya-nachinayuschih.md',
                'views': 0,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
            },
            {
                'slug': 'brosit-kurit-allen-carr',
                'title': 'Бросить курить легко: как метод Аллена Карра помог миллионам',
                'description': 'Почему метод Аллена Карра работает там, где сила воли бессильна. Обзор всех книг автора и пошаговый план избавления от никотиновой зависимости.',
                'md_file': 'brosit-kurit-allen-carr.md',
                'views': 0,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
            },
            {
                'slug': 'romantika-s-drakonami',
                'title': 'Романтика с драконами: лучшее любовное фэнтези для женщин',
                'description': 'От Rebecca Yarros до российских авторов: полный гид по романтическому фэнтези с драконами. Сильные героини, опасная любовь и магические миры.',
                'md_file': 'romantika-s-drakonami.md',
                'views': 0,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
            },
            {
                'slug': 'litrpg-popadancy',
                'title': 'Попаданцы в другие миры: топ ЛитРПГ для эскапизма',
                'description': 'Лучшие книги жанра ЛитРПГ и попаданчества: от классики Маханенко до современных хитов. Прокачка персонажей, игровая механика и второй шанс в другом мире.',
                'md_file': 'litrpg-popadancy.md',
                'views': 0,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
            },
            {
                'slug': 'vygoranie-knigi-energiya',
                'title': 'Выгорание? 5 книг, которые вернут энергию и смысл жизни',
                'description': 'От Трансерфинга до Виктора Франкла: книги, которые помогают выйти из выгорания, вернуть энергию и найти смысл. Не мотивация, а реальные инструменты.',
                'md_file': 'vygoranie-knigi-energiya.md',
                'views': 0,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
            },
        ]
    )


def downgrade() -> None:
    # Удаляем все записи подборок
    op.execute("DELETE FROM guide_audiobook")
    op.execute("DELETE FROM guides WHERE slug IN ('transerfing-dlya-nachinayuschih', 'brosit-kurit-allen-carr', 'romantika-s-drakonami', 'litrpg-popadancy', 'vygoranie-knigi-energiya')")
