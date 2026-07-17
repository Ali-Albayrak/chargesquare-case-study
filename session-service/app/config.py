from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://chargesquare:chargesquare@localhost:5432/chargesquare"
    station_service_url: str = "http://localhost:8001"
    port: int = 8002


settings = Settings()
