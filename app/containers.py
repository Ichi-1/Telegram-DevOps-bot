from enum import Enum

import requests

from app.settings import settings


class ContainerStates(str, Enum):
    """Перечисление возможных состояний контейнеров."""

    EXITED = "exited"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"


class PortainerAPI:
    """Обертка для работы с Portainer API."""

    def __init__(self, portainer_endpoint: str, verify_ssl: bool = True) -> None:
        self._portainer_url = portainer_endpoint + "api/"
        self._verify_ssl = verify_ssl

        self._login(settings.PORTAINER_USER, settings.PORTAINER_PASSWORD)

    def get_container_list(self, environment_id: int) -> list[dict]:
        """Получение списка контейнеров в окружении.

        :param environment_id: id окружения portainer
        :return: json
        """
        response = requests.get(
            self._portainer_url + f"endpoints/{environment_id}/docker/containers/json?all=true",
            headers={"Authorization": f"Bearer {self._token}"},
            verify=self._verify_ssl,
            timeout=60,
        )
        return response.json()

    def _login(self, username: str, password: str):
        """Авторизация и получение refresh токена."""
        response = requests.post(
            self._portainer_url + "auth",
            json={"Username": username, "Password": password},
            verify=self._verify_ssl,
            timeout=60,
        )
        j = response.json()
        self._token = j.get("jwt")


def get_docker_api_client() -> PortainerAPI:
    """Получить клиент для работы с API докера на основе Portainer"""
    return PortainerAPI(portainer_endpoint=settings.PORTAINER_URL)


def set_container_state(container_state: str) -> str | None:
    """Установить визуальный статус контейнера в сообщении."""
    if container_state == ContainerStates.EXITED:
        return "🛑"

    if container_state == ContainerStates.PAUSED:
        return "⏸"

    if container_state == ContainerStates.RESTARTING:
        return "🔄"

    return "⁉️"
