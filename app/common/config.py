from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "aws-ecs-internal-service-monitor"
    app_version: str = "0.1.0"
    allow_private_targets: bool = Field(default=False, alias="ALLOW_PRIVATE_TARGETS")

    model_config = SettingsConfigDict(env_file=None, extra="ignore")


settings = Settings()
