# Книжный дом «Большой Ух» — Каталог книг

Каталог аудиокниг с партнерской программой ЛитРес.

## Структура

```
app/
├── routes/         # Эндпоинты
├── services/       # Бизнес-логика
├── models.py       # SQLAlchemy модели
├── config.py       # Настройки
└── main.py         # Точка входа

templates/          # Jinja2 шаблоны
static/css/         # Стили (Tailwind CSS v4)
scripts/            # Скрипты импорта
alembic/            # Миграции БД
```

## Tech Stack

- FastAPI + Uvicorn
- PostgreSQL + SQLAlchemy
- Jinja2
- Tailwind CSS v4 + Alpine.js
