import dotenv
import pickledb
from pydantic import BaseSettings, HttpUrl


class Settings(BaseSettings):
    """Глобальные константы и переменные окружения."""

    DEBUG: bool = True

    BOT_TOKEN: str
    CHAT_ID: int
    HOST: HttpUrl

    PORTAINER_URL: str
    PORTAINER_USER: str
    PORTAINER_PASSWORD: str

    GITLAB_URL: str
    VAULT_URL: str
    GRAFANA_URL: str
    SONAR_URL: str

    def get_storage(self) -> pickledb.PickleDB:
        """Получить локальное key-value хранилище"""
        return pickledb.load("local.db", auto_dump=True)

    @property
    def running_apps(self) -> dict[str, str]:
        """Получить ссылки на инстансы приложений"""
        return {
            "GitLab": self.GITLAB_URL,
            "Portainer": self.PORTAINER_URL,
            "Vault": self.VAULT_URL,
            "Grafana": self.GRAFANA_URL,
            "Sonar": self.SONAR_URL
        }

settings = Settings()  # type: ignore
dotenv.load_dotenv()

STORAGE = settings.get_storage()
