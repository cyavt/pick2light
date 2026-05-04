"""
MQTT Bridge settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MQTT
    MQTT_BROKER: str = "emqx"
    MQTT_PORT: int = 1883

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # Internal service URLs
    CORE_API_URL: str = "http://core-api:8002"
    WS_SERVICE_URL: str = "http://ws-service:8003"

    class Config:
        env_file = ".env"


settings = Settings()
