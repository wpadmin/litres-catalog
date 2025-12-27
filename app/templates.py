"""Общий экземпляр шаблонов для всего приложения."""
from fastapi.templating import Jinja2Templates
from datetime import datetime


def format_price(value):
    """Форматирует цену без лишних нулей после точки."""
    if isinstance(value, (int, float)):
        if value == int(value):
            return f"{int(value)}"
        return f"{value:.2f}".rstrip('0').rstrip('.')
    return str(value)


templates = Jinja2Templates(directory="templates")
templates.env.globals["now"] = datetime.now
templates.env.filters["price"] = format_price
