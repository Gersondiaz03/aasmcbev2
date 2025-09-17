import os
from dotenv import load_dotenv
from pathlib import Path
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

# Make sure we load from the correct .env file location
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    database_url: PostgresDsn = Field(default=..., validation_alias="DATABASE_URL")
    secret_key: str = Field(default=..., validation_alias="SECRET_KEY")
    algorithm: str = Field(default=..., validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )


settings = Settings()
