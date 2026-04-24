"""Core bot class with cog loading and BetFair client setup."""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

import discord
from discord.ext import commands

from sport_data_bot import aws_s3, betfair_api, graph_producer

log = logging.getLogger(__name__)

CERTIFICATIONS_DIR = Path(os.getcwd()) / "certifications"
TEMP_IMAGES_DIR = Path(os.getcwd()) / "temp_images"
COGS_DIR = Path(__file__).parent / "cogs"


class SportDataBot(commands.Bot):
    """Discord bot that auto-loads all cogs in the project package."""

    def __init__(self) -> None:
        """Initialize the bot with default intents."""
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        self.aws_s3: aws_s3.AmazonS3 | None = None
        self.betfair: betfair_api.BetFairAPI | None = None
        self.graph = graph_producer.GraphProducer()
        self.images_cnt = 0

    async def setup_hook(self) -> None:
        """Prepare working dirs, external clients, load cogs, sync slash commands globally."""
        if TEMP_IMAGES_DIR.exists():
            shutil.rmtree(TEMP_IMAGES_DIR)
        TEMP_IMAGES_DIR.mkdir()

        self.aws_s3 = aws_s3.AmazonS3(str(CERTIFICATIONS_DIR))
        self.betfair = betfair_api.BetFairAPI(str(CERTIFICATIONS_DIR))

        self.tree.on_error = self._on_tree_error  # type: ignore[assignment]

        for cog_file in COGS_DIR.glob("*.py"):
            if cog_file.name.startswith("_"):
                continue
            ext = f"sport_data_bot.cogs.{cog_file.stem}"
            await self.load_extension(ext)
            log.info("Loaded extension: %s", ext)

        await self.tree.sync()
        log.info("Synced slash commands globally")

    async def _on_tree_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        """Log slash-command failures and send a fallback error response."""
        original = getattr(error, "original", error)
        if isinstance(original, discord.NotFound) and original.code == 10062:
            log.warning("Interaction expired for /%s (user likely retried)", interaction.command)
            return
        log.exception("Slash command error in /%s", interaction.command, exc_info=error)
        try:
            if interaction.response.is_done():
                await interaction.followup.send("Something went wrong. Please try again.", ephemeral=True)
            else:
                await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
        except discord.HTTPException:
            pass

    async def on_ready(self) -> None:
        """Log startup and set bot presence once connected."""
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="BetFair API"))
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id if self.user else "?")

    async def on_error(self, event_method: str, *args, **kwargs) -> None:
        """Log uncaught Discord event handler exceptions."""
        log.exception("Unhandled exception in %s", event_method)


__all__ = ["SportDataBot", "TEMP_IMAGES_DIR"]
