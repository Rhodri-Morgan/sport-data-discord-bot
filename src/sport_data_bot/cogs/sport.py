"""Sport cog — slash commands for sport/event/market navigation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from sport_data_bot.views import SportSelectView, advance_to_event

if TYPE_CHECKING:
    from sport_data_bot.bot import SportDataBot

log = logging.getLogger(__name__)


async def _run_blocking(bot: SportDataBot, func):
    """Run a synchronous BetFair call in a thread executor."""
    return await bot.loop.run_in_executor(None, func)


class SportCog(commands.Cog, name="Sport"):
    """Slash commands that drive the BetFair sport → event → market flow."""

    def __init__(self, bot: SportDataBot) -> None:
        self.bot = bot

    @app_commands.command(name="sport", description="Pick a sport, then drill into events and markets")
    @app_commands.allowed_contexts(guilds=False, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def sport(self, interaction: discord.Interaction) -> None:
        """Open the sport-picker, listing every event type with open events."""
        await interaction.response.defer()
        assert self.bot.betfair is not None

        sports = await _run_blocking(self.bot, self.bot.betfair.get_event_types)
        if not sports:
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title="Sports",
                    description="No sports are currently open.",
                    colour=discord.Colour.orange(),
                ),
            )
            return

        sports_sorted = sorted(sports, key=lambda s: s.event_type.name.strip().lower())
        view = SportSelectView(self.bot, owner_id=interaction.user.id, sports=sports_sorted)
        embed = discord.Embed(
            title="Sports",
            description=f"Pick a sport from the menu below ({len(sports_sorted)} available).",
            colour=discord.Colour.blue(),
        )
        await interaction.edit_original_response(embed=embed, view=view)

    @app_commands.command(name="motorsport", description="Jump straight to Motor Sport events")
    @app_commands.allowed_contexts(guilds=False, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def motorsport(self, interaction: discord.Interaction) -> None:
        """Skip the sport picker and go straight to Motor Sport events."""
        await self._jump_to_sport(interaction, "Motor Sport")

    @app_commands.command(name="rugby", description="Jump straight to Rugby Union events")
    @app_commands.allowed_contexts(guilds=False, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def rugby(self, interaction: discord.Interaction) -> None:
        """Skip the sport picker and go straight to Rugby Union events."""
        await self._jump_to_sport(interaction, "Rugby Union")

    @app_commands.command(name="football", description="Jump straight to Soccer events")
    @app_commands.allowed_contexts(guilds=False, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    async def football(self, interaction: discord.Interaction) -> None:
        """Skip the sport picker and go straight to Soccer events."""
        await self._jump_to_sport(interaction, "Soccer")

    async def _jump_to_sport(self, interaction: discord.Interaction, sport: str) -> None:
        """Defer the interaction and immediately render the event selector for ``sport``."""
        await interaction.response.defer()
        await advance_to_event(interaction, self.bot, sport, owner_id=interaction.user.id)


async def setup(bot: SportDataBot) -> None:
    """Register the sport cog with the bot."""
    await bot.add_cog(SportCog(bot))
