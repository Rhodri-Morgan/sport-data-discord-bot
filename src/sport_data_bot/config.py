"""Bot configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    discord_bot_token: str
    betfair_username: str
    betfair_password: str
    betfair_live_app_key: str
    aws_bucket_name: str
    aws_region: str

    @classmethod
    def from_env(cls) -> Settings:
        """Construct settings from environment variables.

        AWS credentials are resolved via the default boto3 chain (ECS task role in
        prod, ``~/.aws`` or env vars locally) — no explicit keys required.
        """
        return cls(
            discord_bot_token=os.environ["DISCORD_BOT_TOKEN"].strip("'\""),
            betfair_username=os.environ["BETFAIR_USERNAME"],
            betfair_password=os.environ["BETFAIR_PASSWORD"],
            betfair_live_app_key=os.environ["BETFAIR_LIVE_APP_KEY"],
            aws_bucket_name=os.environ["AWS_BUCKET_NAME"],
            aws_region=os.environ.get("AWS_REGION", "eu-west-1"),
        )


settings = Settings.from_env()
