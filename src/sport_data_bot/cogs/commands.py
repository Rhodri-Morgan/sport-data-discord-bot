"""Commands cog — DMs the invoking user a list of available bot commands."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from sport_data_bot.bot import SportDataBot

log = logging.getLogger(__name__)


COMMANDS_HELP: list[tuple[str, str]] = [
    ("/commands", "Show this list of available commands."),
    ("/sport", "Pick a sport, then drill into events and markets."),
    ("/motorsport", "Shortcut: jump straight into Motor Sport events."),
    ("/rugby", "Shortcut: jump straight into Rugby Union events."),
    ("/football", "Shortcut: jump straight into Soccer events."),
]


def _build_help_embed() -> discord.Embed:
    """Build the embed listing every available bot command."""
    embed = discord.Embed(
        title="Sport Data Discord Bot — Commands",
        description="All commands run in a DM with the bot.",
        colour=discord.Colour.purple(),
    )
    for name, description in COMMANDS_HELP:
        embed.add_field(name=name, value=description, inline=False)
    return embed


class CommandsCog(commands.Cog, name="Commands"):
    """Lightweight cog that lists every available bot command."""

    def __init__(self, bot: SportDataBot) -> None:
        self.bot = bot

    @app_commands.command(name="commands", description="List available bot commands")
    @app_commands.allowed_contexts(guilds=False, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def commands_cmd(self, interaction: discord.Interaction) -> None:
        """Reply with the help embed listing every command."""
        await interaction.response.send_message(embed=_build_help_embed())


async def setup(bot: SportDataBot) -> None:
    """Register the commands cog with the bot."""
    await bot.add_cog(CommandsCog(bot))
