import functools
from datetime import datetime, time
from typing import Any, Literal

import requests
from loguru import logger

from app.settings import STORAGE, settings


def calculate_timedelta(uuid: str) -> datetime:
    """Рассчитать разницу времени.

    (для времени сборки проекта и для времени отклика на alert)
    """
    start_time: Any | Literal[False] = STORAGE.get(uuid)

    if start_time is False:
        raise ValueError("Can not calculate timedelta: uuid record don't exist yet")
    if not isinstance(start_time, float):
        raise TypeError(f"start_time is not a float - {type(start_time)}")

    return datetime.fromtimestamp(datetime.now().timestamp() - start_time)


def get_running_apps() -> str:
    """Узнать доступность инфраструктурных сервисов в стеке."""
    statuses = []

    for name, url in settings.running_apps.items():
        response = requests.get(url, timeout=60)

        if response.status_code == 200:
            statuses.append(f"{name.capitalize()} 🟢\n{url}\n")
        else:
            statuses.append(f"🛑 {url}\n")

    return f"Доступность сервисов на {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n" + "".join(statuses)


def handler_exceptions(func):
    """Декоратор для обработки исключений."""
    # pylint: disable=inconsistent-return-statements
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any | None:  # type: ignore
        try:
            return func(*args, **kwargs)

        except Exception as err:  # pylint: disable=W
            logger.exception(f"{func.__name__} handler error: {err}")

    return wrapper


def is_working_time() -> bool:
    """Проверка, что сейчас рабочее время."""
    current_hour = int(datetime.now().strftime("%H"))
    return 8 < current_hour < 18
