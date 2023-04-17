from datetime import timedelta

from fastapi import FastAPI, status, Depends
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from loguru import logger
from telebot import types
from telebot.apihelper import ApiTelegramException

from app.bot import (
    GitlabEvents,
    bot,
    notify_alert,
)
from app.containers import (
    ContainerStates,
    get_docker_api_client,
    set_container_state,
)
from app.settings import settings
from app.utils import handler_exceptions, is_working_time


app = FastAPI(
    docs_url="/docs" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/webhooks/gitlab/deployment/")
def webhook_gitlab_deployment(event: dict, gitlab: GitlabEvents = Depends(GitlabEvents)) -> None:
    """Обработка deployment событий по webhook из GitLab.

    Посылает уведомления на различные статусы запущенного deployment процесса.
    """
    if event["status"] not in gitlab.DeploymentStatus.__members__.values():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "event status not supported")

    try:
        gitlab.notify_deployment_status(event)
    except (TypeError, KeyError, ValueError) as err:
        raise HTTPException(status.HTTP_409_CONFLICT, f"{err}") from err


@app.post("/webhooks/alerts/")
def webhook_grafana(alert: dict) -> None:
    """Обработка alerts из Grafana."""
    print(alert)
    
    try:
        notify_alert(alert["alerts"])
    except ApiTelegramException as err:
        logger.error(f"{err}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=err.description)


@app.post(f"/{settings.BOT_TOKEN}/")
def process_webhook(update: dict) -> None:
    """Обработка действий в чате телеграм-ботом."""

    if update:
        update = types.Update.de_json(update)  # type: ignore
        bot.process_new_updates([update])  # type: ignore


@app.on_event("startup")
@repeat_every(seconds=timedelta(hours=4).total_seconds(), raise_exceptions=True)
@handler_exceptions
def container_health_check() -> None:
    """Healthcheck контейнеров каждые 2 часа с 8 до 17 в будние дни.

    Не выполнять health check если сейчас не рабочее время.
    Рабочий день большинства сотрудников отдела разработки: начинается с 8-9 до 17-18 по МСК
    """
    logger.info("Health-check time!")
    if is_working_time():

        unwanted_behavior: list[str] = []
        container_list: list[dict] = get_docker_api_client()\
            .get_container_list(environment_id=2)

        for container in container_list:
            current_state: str = container["State"]
            emoji: str | None = set_container_state(current_state)

            if current_state != ContainerStates.RUNNING:
                unwanted_behavior.append(
                    f"{emoji} {container['Names'][0].strip('/')}: <b>{container['State']}</b>\n"
                )

        if unwanted_behavior:
            bot.send_message(
                settings.CHAT_ID,
                text=(
                    "🤨 Эта парочка контейнеров ведет себя подозрительно: \n\n"
                    + "".join(unwanted_behavior)
                ),
            )
