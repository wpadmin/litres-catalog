from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    database_url: str
    database_pool_size: int = 5
    database_max_overflow: int = 10

    secret_key: str

    site_name: str = "Большой Ух"
    site_url: str = "https://bigear.ru"
    site_description: str = "Аудиокниги – слушать онлайн или скачать в mp3 на Большой Ух"

    debug: bool = False
    redis_url: str = "redis://localhost:6379/0"

settings = Settings()