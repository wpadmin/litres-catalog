import re
from unidecode import unidecode


def slugify(text: str) -> str:
    text = unidecode(text).lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text[:200]


def normalize_title(title: str) -> str:
    """Нормализация названия для сопоставления аудио и текстовых книг."""
    if not title:
        return ""

    # Убираем подзаголовки
    title = re.sub(r'\s*[:\-–—]\s*(роман|повесть|рассказ|рассказы|сборник|поэма|новелла|эссе|очерк).*$', '', title, flags=re.IGNORECASE)

    # Убираем указания на тип издания
    title = re.sub(r'\s*\((аудиокнига|книга|издание|сборник)\)', '', title, flags=re.IGNORECASE)

    # Убираем "или" и варианты
    title = re.sub(r'\s*,?\s+или\s+', ' ', title, flags=re.IGNORECASE)

    # Убираем лишние пробелы и спецсимволы
    title = re.sub(r'[^\w\s]', ' ', title)
    title = ' '.join(title.split())

    return title.lower().strip()


def extract_publisher_year(description: str) -> tuple[str | None, int | None]:
    """Извлечь издательство и год из описания."""
    if not description:
        return None, None

    publisher = None
    year = None

    # Ищем паттерн "©ООО «Издательство», 2025"
    copyright_match = re.search(r'©.*?[«"]([^»"]+)[»"],?\s*(\d{4})', description)
    if copyright_match:
        publisher = copyright_match.group(1).strip()
        year = int(copyright_match.group(2))

    # Или "Издательство: АСТ, 2025"
    if not publisher:
        pub_match = re.search(r'издательство[:\s]+([^,\n]+),?\s*(\d{4})', description, re.IGNORECASE)
        if pub_match:
            publisher = pub_match.group(1).strip()
            year = int(pub_match.group(2))

    # Ищем просто год в конце описания
    if not year:
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', description[-100:])
        if year_match:
            year = int(year_match.group(1))

    return publisher, year
