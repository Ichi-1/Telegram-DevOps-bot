import uvicorn
from loguru import logger

from app.bot import bot
from app.server import app
from app.settings import settings

if __name__ == "__main__":

    bot.remove_webhook()
    bot.set_webhook(f"{settings.HOST}/{settings.BOT_TOKEN}/")
    logger.success("Webhook set up")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8086,
        forwarded_allow_ips="*",
    )
