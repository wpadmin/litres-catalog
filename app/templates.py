"""Общий экземпляр шаблонов для всего приложения."""
from fastapi.templating import Jinja2Templates
from datetime import datetime


def format_price(value):
    """Форматирует цену всегда с двумя знаками после запятой."""
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return str(value)


templates = Jinja2Templates(directory="templates")
templates.env.globals["now"] = datetime.now
templates.env.filters["price"] = format_price
