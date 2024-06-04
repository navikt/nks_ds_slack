#!/usr/bin/env python3

"""
Håndter innstillinger fra miljøvariabler eller 'dotenv' filer
"""

from pydantic import AliasChoices, Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore[misc]
    """Innstillinger for NKS DS Slack bot"""

    model_config = SettingsConfigDict(
        env_prefix="nks_ds_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: SecretStr = Field(
        validation_alias=AliasChoices("nks_ds_bot_token", "slack_bot_token")
    )
    """Slack bot token"""

    app_token: SecretStr = Field(
        validation_alias=AliasChoices("nks_ds_app_token", "slack_app_token")
    )
    """Slack app token"""

    id: str = "A075RP88EV8"
    """Slack app id til boten"""

    endpoint: HttpUrl
    """Endepunkt for NKS DS API"""

    answer_timeout: float = 60.0
    """Tidsbegrensning, i sekunder, på hvor lenge vi venter på et svar fra modellen før vi gir opp"""
