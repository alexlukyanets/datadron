from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict

from core.enums import Environments


class Settings(BaseSettings):
    ENVIRONMENT: Environments = Environments.LOCAL

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file='../.env',
        env_file_encoding='utf-8'
    )


settings: Settings = Settings()
