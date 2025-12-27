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
- PostgreSQL + SQLAlchemy + Redis
- Jinja2
- Tailwind CSS v4 + Alpine.js

## Запуск локально

```bash
# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt

# Настроить .env (скопировать .env.example)
cp .env.example .env

# Применить миграции
alembic upgrade head

# Запустить Redis (если используется кеш)
redis-server

# Импорт данных (в порядке выполнения)
python scripts/import_audiobooks.py
python scripts/import_textbooks.py
python scripts/link_books.py

# Запустить сервер
uvicorn app.main:app --reload
```
