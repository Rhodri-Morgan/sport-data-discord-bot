"""Smoke test: package can be imported without side-effects at the config boundary."""

from __future__ import annotations

import importlib
import os

import pytest


def test_health_module_imports() -> None:
    """Health module has no env dependencies; it must import cleanly."""
    mod = importlib.import_module("sport_data_bot.health")
    assert hasattr(mod, "start_health_server")


def test_bot_module_imports_without_runtime_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Module-level imports must not require real secrets — config is read on `from_env`."""
    required_env = (
        "DISCORD_BOT_TOKEN",
        "BETFAIR_USERNAME",
        "BETFAIR_PASSWORD",
        "BETFAIR_LIVE_APP_KEY",
        "AWS_BUCKET_NAME",
    )
    for key in required_env:
        monkeypatch.setenv(key, "dummy")

    import sys

    sys.modules.pop("sport_data_bot.config", None)
    sys.modules.pop("sport_data_bot.bot", None)
    mod = importlib.import_module("sport_data_bot.bot")
    assert hasattr(mod, "SportDataBot")

    # Clean up so other tests / module reloads are not contaminated by this fake config.
    sys.modules.pop("sport_data_bot.bot", None)
    sys.modules.pop("sport_data_bot.config", None)
    for key in required_env:
        os.environ.pop(key, None)
