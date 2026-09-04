from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Atlas"
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173"

    DATABASE_URL: str = "sqlite:///./atlas.db"

    AIR_API_KEY: str = ""
    AIR_API_BASE_URL: str = ""
    AIR_LLM_MODEL: str = ""
    AIR_EMBEDDING_MODEL: str = ""
    AIR_ASR_MODEL: str = ""

    SIMULATION_CALL_COUNT: int = 200
    SIMULATION_BATCH_SIZE: int = 5
    SIMULATION_DELAY_SECONDS: float = 0.4
    SIMULATION_ON_SCENE_TICKS: int = 15

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def air_enabled(self) -> bool:
        return bool(self.AIR_API_KEY and self.AIR_API_BASE_URL)


@lru_cache
def get_settings() -> Settings:
    return Settings()
