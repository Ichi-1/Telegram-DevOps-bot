from datetime import datetime
from enum import Enum
from typing import Mapping, Sequence

from telebot import TeleBot
from telebot.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from app.messages import (
    canceled_deployment,
    failed_deployment,
    format_alert_message,
    start_deployment,
    success_deployment,
)
from app.settings import STORAGE, settings
from app.utils import get_running_apps

bot = TeleBot(token=settings.BOT_TOKEN, parse_mode="HTML")


@bot.message_handler(commands=["help"])
def check_running_apps(message) -> None:
    """Показать доступность инфраструктурных сервисов.

    *Запущенные сервисы определяются в настройках приложения константой RUNNING_APPS
    """
    bot.send_message(settings.CHAT_ID, get_running_apps())


@bot.callback_query_handler(lambda q: q.data == "accept_alert")
def accept_alert(callback: CallbackQuery) -> None:
    """Ответ на alert."""

    bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=callback.message.id,
        text=(
            f"{callback.message.text}\n"
            f"\n@{callback.from_user.username} не прошёл мимо и сейчас разберется с этим алертом!"
        )
    )
    bot.answer_callback_query(callback.id)


def notify_alert(alerts: Sequence[Mapping]) -> None:
    """Уведомить об alert и предложить варианты ответа.

    Время когда alert был доставлен - записываем в хранилище.
    В будущем с помощью него рассчитаем время отклика.
    """
    for alert in alerts:

        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("🔕 Silence!", url=alert["silenceURL"]),
            # InlineKeyboardButton("Отреагировать", callback_data="accept_alert")
        )
        bot.send_message(
            settings.CHAT_ID,
            format_alert_message(alert),
            reply_markup=keyboard,
        )


class GitlabEvents:
    """Обработка деплоймент событий из Gitlab."""

    class DeploymentStatus(str, Enum):
        SUCCESS = "success"
        RUNNING = "running"
        CANCELED = "canceled"
        FAILED = "failed"

    def notify_deployment_status(self, event: dict) -> None:
        """Отправка уведомлений о статусе CI pipeline.

        При статусе running - записываем время начала сборки в storage
        При статусе success - рассчитываем время сборки, после уведомления - удаляем k,v из storage
        При статусе failed - простое уведомление
        При статусе canceled - уведомление+удалить время начала сборки из хранилища
        """
        event_id: str = f"{event['deployment_id']}"

        if event["status"] == self.DeploymentStatus.RUNNING:
            bot.send_message(settings.CHAT_ID, start_deployment(event))
            STORAGE.set(event_id, datetime.now().timestamp())

        if event["status"] == self.DeploymentStatus.SUCCESS:
            bot.send_message(settings.CHAT_ID, success_deployment(event))
            STORAGE.rem(event_id)

        if event["status"] == self.DeploymentStatus.FAILED:
            bot.send_message(settings.CHAT_ID, failed_deployment(event))

        if event["status"] == self.DeploymentStatus.CANCELED:
            bot.send_message(settings.CHAT_ID, canceled_deployment(event))
            STORAGE.rem(event_id)
