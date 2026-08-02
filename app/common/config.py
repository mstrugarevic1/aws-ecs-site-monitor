from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "aws-ecs-site-monitor"
    app_version: str = "0.1.0"
    allow_private_targets: bool = Field(default=False, alias="ALLOW_PRIVATE_TARGETS")
    aws_region: str | None = Field(default=None, alias="AWS_REGION")
    monitors_table: str | None = Field(default=None, alias="MONITORS_TABLE")
    check_results_table: str | None = Field(default=None, alias="CHECK_RESULTS_TABLE")
    queue_url: str | None = Field(default=None, alias="QUEUE_URL")
    alerts_topic_arn: str | None = Field(default=None, alias="ALERTS_TOPIC_ARN")
    result_ttl_days: int = Field(default=30, alias="RESULT_TTL_DAYS")

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    @property
    def aws_runtime_enabled(self) -> bool:
        return all(
            [
                self.aws_region,
                self.monitors_table,
                self.check_results_table,
                self.queue_url,
                self.alerts_topic_arn,
            ]
        )


settings = Settings()
