"""Общий экземпляр шаблонов для всего приложения."""
from fastapi.templating import Jinja2Templates
from datetime import datetime

templates = Jinja2Templates(directory="templates")
templates.env.globals["now"] = datetime.now
