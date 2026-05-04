"""
Application settings for core-api.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ptl:secret@postgres:5432/ptl_db"

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # Internal service URLs
    MQTT_BRIDGE_URL: str = "http://mqtt-bridge:8004"
    WS_SERVICE_URL: str = "http://ws-service:8003"

    class Config:
        env_file = ".env"


settings = Settings()
