from datetime import datetime
from typing import Mapping

from app.utils import calculate_timedelta


def start_deployment(event: Mapping) -> str:
    """Формирует сообщение о начале деплоя на основании данных из event.

    :param event: Словарь с данными о деплойменте
    :return: Сообщение для ТГ
    """
    return (
        "⚙️ Запущена сборка проекта:\n"
        f"<a href='{event['deployable_url']}'>{event['project']['name']}</a>\n\n"
        f"🌳: {event['ref']}\n"
        f"👨🏼‍💻: {event['user']['name']}\n\n"
        f"✍️ Last commit:\n <code>{event['commit_title']}</code>\n\n"
        f"⌛️ Окружение <b>{event['environment']}</b> скоро будет доступно"
    )


def success_deployment(event: Mapping) -> str:
    """Формирует сообщение о завершени деплоймента.

    :param event: Словарь с данными о деплойменте
    :return: Сообщение для ТГ
    """
    event_id: str = str(event['deployment_id'])
    deployment_time: datetime = calculate_timedelta(event_id)
    availability: str = f"Окружение <b>{event['environment']}</b> доступно по ссылке:\n"

    return (
        f" ✅ Сборка проекта завершена: {event['project']['name']}\n\n"
        f"⌛️ Время сборки: {deployment_time.strftime('%M:%S')}\n\n"
        f"{availability}"
        f"<b>{event['environment_external_url']}</b>\n\n"
        f"Отчет о сборке:\n{event['deployable_url']}"
    )


def failed_deployment(event: Mapping) -> str:
    """Формирует сообщение, если деплоймент закончился с ошибкой.

    :param event: Словарь с данными о деплойменте
    :return: Сообщение для ТГ
    """
    project_name = event['project']['name']

    return (
        f"🔥 Oops!\n\n"
        f"Ошибка при сборке проекта: {project_name}\n\n"
        f"Отчет о сборке\n{event['deployable_url']}"
    )


def canceled_deployment(event: Mapping) -> str:
    """Сообщение об отмене деплоймента.

    :param event: Словарь с данными о деплойменте
    :return: Сообщение для ТГ
    """
    project_name = event['project']['name']
    gitlab_user = event['user']['name']

    return (
        f"🤔 Сборка проекта {project_name} остановлена\n\n"
        f"👨🏼‍💻: {gitlab_user}"
    )


def format_alert_message(alert: Mapping) -> str:
    """Форматирование алерта из графаны"""

    alert_name = str(alert['labels']['alertname'])
    node_exporter_instance = str(alert['labels']['instance'])
    summary = str(alert['annotations']['summary'])

    return (
        f"🔥 Alert firing: {alert_name}\n"
        f"<code>source={node_exporter_instance}</code>\n\n"
        f"{summary}"
    )
