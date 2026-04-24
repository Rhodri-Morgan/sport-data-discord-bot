"""Core bot class — Discord bot exposing BetFair prediction-market data in DMs."""

from __future__ import annotations

import asyncio
import logging
import math
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.enums import ChannelType
from discord.ext import commands

from sport_data_bot import aws_s3, betfair_api, graph_producer

log = logging.getLogger(__name__)

CERTIFICATIONS_DIR = Path(os.getcwd()) / "certifications"
TEMP_IMAGES_DIR = Path(os.getcwd()) / "temp_images"


class SportDataBot(commands.Bot):
    """Discord bot that serves BetFair market probability data via DM commands."""

    def __init__(self) -> None:
        """Initialize the bot with DM-friendly intents."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.dm_messages = True
        super().__init__(command_prefix="!", intents=intents)

        self.aws_s3: aws_s3.AmazonS3 | None = None
        self.betfair: betfair_api.BetFairAPI | None = None
        self.graph = graph_producer.GraphProducer()
        self.images_cnt = 0

    async def setup_hook(self) -> None:
        """Prepare working directories, external clients, and command cog."""
        if TEMP_IMAGES_DIR.exists():
            shutil.rmtree(TEMP_IMAGES_DIR)
        TEMP_IMAGES_DIR.mkdir()

        self.aws_s3 = aws_s3.AmazonS3(str(CERTIFICATIONS_DIR))
        self.betfair = betfair_api.BetFairAPI(str(CERTIFICATIONS_DIR))

        await self.add_cog(SportCommands(self))

    async def on_ready(self) -> None:
        """Log startup and set bot presence once connected."""
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Sport BetFair API"))
        log.info("Discord Bot on_ready()")


class SportCommands(commands.Cog):
    """Prefix-command cog containing all user-facing DM commands."""

    def __init__(self, bot: SportDataBot) -> None:
        self.bot = bot

    @commands.command(name="commands")
    async def list_commands(self, ctx: commands.Context) -> None:
        """List available commands."""
        log.info("%s - commands() - %s", datetime.now(timezone.utc), ctx.author)

        if ctx.channel.type != ChannelType.private:
            return

        help_text = (
            "Use ! to begin a command.\nCommands must all be in lowercase.\nYou can type 'exit' to end a query.\n\n"
            "!commands - Displays a list of available commands for the bot.\n"
            "!clear - Deletes all bot generated messages (not users messages).\n\n"
            "!sport - Menu for choosing sport and then navigating all events.\n"
            "!motorsport - Menu for navigating motorsport events.\n"
            "!rugby - Menu for navigating rugby union events.\n"
            "!football - Menu for navigating football events."
        )

        async for message in ctx.author.history(limit=None):
            if message.pinned:
                await message.delete()

        message = await ctx.author.send("```{0}```".format(help_text))
        await message.pin()

    @commands.command(name="clear")
    async def clear(self, ctx: commands.Context) -> None:
        """Delete the bot's own messages in the current DM history."""
        log.info("%s - clear() - %s", datetime.now(timezone.utc), ctx.author)

        async for message in ctx.author.history(limit=None):
            if self.bot.user is not None and message.author.id == self.bot.user.id:
                await message.delete()

    @commands.command(name="sport")
    async def sport(self, ctx: commands.Context) -> None:
        """Interactive sport/event/market selector."""
        if ctx.channel.type != ChannelType.private:
            return
        assert self.bot.betfair is not None
        sport = await self._user_select_sport(ctx.author, self.bot.betfair.get_event_types())
        if sport is not None:
            await self._process_sport(ctx, sport)

    @commands.command(name="motorsport")
    async def motorsport(self, ctx: commands.Context) -> None:
        """Shortcut: process Motor Sport."""
        await self._process_sport(ctx, "Motor Sport")

    @commands.command(name="rugby")
    async def rugby(self, ctx: commands.Context) -> None:
        """Shortcut: process Rugby Union."""
        await self._process_sport(ctx, "Rugby Union")

    @commands.command(name="football")
    async def football(self, ctx: commands.Context) -> None:
        """Shortcut: process Soccer."""
        await self._process_sport(ctx, "Soccer")

    async def _process_sport(self, ctx: commands.Context, sport: str) -> None:
        """Select an event and market for a sport, then display probabilities."""
        if ctx.channel.type != ChannelType.private:
            return

        assert self.bot.betfair is not None
        log.info("%s - sport() request %s - %s", datetime.now(timezone.utc), sport, ctx.author)
        async with ctx.typing():
            events = self.bot.betfair.get_events(sport)
            event = await self._user_select_event(ctx.author, sport, events)
            if event is None:
                return

            event_markets = self.bot.betfair.get_event_markets(event.event.id)
            event_market = await self._user_select_market(ctx.author, event.event, event_markets)
            if event_market is None:
                return

            market_book = self.bot.betfair.get_market_book(event_market.market_id)
            market_runners_names = self.bot.betfair.get_runners_names(event_market.market_id)
            probabilities_dict = self.bot.betfair.calculate_runners_probability(market_book.runners, market_runners_names)
            await self._display_data(ctx.author, sport, probabilities_dict, event.event.name, event_market.market_name)

    async def _message_length_check(self, user: discord.User, original_str: str, appended_str: str) -> str:
        """Flush to Discord if appending would exceed the 2000-char limit; return the next buffer."""
        if len(original_str) + len(appended_str) + len("``````") >= 2000:
            await user.send("```{0}```".format(original_str))
            return appended_str
        return "{0}{1}".format(original_str, appended_str)

    async def _save_graph(self, plt) -> str:
        """Save a matplotlib figure to a temp file and return the path."""
        path = TEMP_IMAGES_DIR / "image{0}.png".format(self.bot.images_cnt)
        plt.savefig(path, facecolor="#36393f")
        self.bot.images_cnt += 1
        return str(path)

    async def _menu_selection(self, user: discord.User, options: list) -> int | None:
        """Prompt the user to pick an option number and validate the reply."""

        def check(message: discord.Message) -> bool:
            return message.author == user and message.channel.type == ChannelType.private

        while True:
            try:
                response = await self.bot.wait_for("message", timeout=120.0, check=check)
            except asyncio.TimeoutError:
                await user.send("`Error data request has timed out. Please try again.`")
                return None

            content = response.content.strip().lower()
            if content == "exit":
                return None
            if re.search("^[0-9]+$", response.content) and 0 < int(response.content) <= len(options):
                return int(response.content)
            await user.send("`Error please make another selection or type 'exit'.`")

    async def _user_select_sport(self, user: discord.User, sports: list) -> str | None:
        """Prompt the user to pick a sport from the available list."""
        if not sports:
            await user.send("`Currently there are no open sports with open events.`")
            return None

        sports_str = "Available sports: \n"
        for cnt, sport in enumerate(sports, start=1):
            sports_str = await self._message_length_check(user, sports_str, "{0} - {1}\n".format(cnt, sport.event_type.name.strip()))

        sports_str = await self._message_length_check(user, sports_str, "\nPlease enter an option below.")
        if sports_str:
            await user.send("```{0}```".format(sports_str))

        response = await self._menu_selection(user, sports)
        if response is None:
            return None
        return sports[response - 1].event_type.name

    async def _user_select_event(self, user: discord.User, sport: str, events: list):
        """Prompt the user to pick an event for a sport."""
        if not events:
            await user.send("`Currently there are no open {0} events.`".format(sport))
            return None

        events_str = "Available {0} events: \n".format(sport)
        for cnt, event in enumerate(events, start=1):
            events_str = await self._message_length_check(user, events_str, "{0} - {1}\n".format(cnt, event.event.name.strip()))

        events_str = await self._message_length_check(user, events_str, "\nPlease enter an option below.")
        if events_str:
            await user.send("```{0}```".format(events_str))

        response = await self._menu_selection(user, events)
        if response is None:
            return None
        return events[response - 1]

    async def _user_select_market(self, user: discord.User, event, markets: list):
        """Prompt the user to pick a market for an event."""
        if not markets:
            await user.send("`Currently there are no open markets for {0}.`".format(event.name))
            return None

        event_str = "Available markets for {0}: \n".format(event.name)
        for cnt, market in enumerate(markets, start=1):
            event_str = await self._message_length_check(user, event_str, "{0} - {1}\n".format(cnt, market.market_name.strip()))

        event_str = await self._message_length_check(user, event_str, "\nPlease enter an option below.")
        if event_str:
            await user.send("```{0}```".format(event_str))

        response = await self._menu_selection(user, markets)
        if response is None:
            return None
        return markets[response - 1]

    async def _display_data(self, user: discord.User, sport: str, probabilities_dict: dict, event_name: str, market_name: str) -> None:
        """Send probability text plus barplot/piechart images to the caller."""
        if all(math.isnan(value) for value in probabilities_dict.values()):
            await user.send("`Currently there is no valid data for {0} - {1}.`".format(event_name, market_name))
            return

        current_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        probabilities_str = (
            "Event - {0}\nMarket - {1}\nProcessed Datetime(UTC) - {2}\nRequested User - {3}\n\n".format(
                event_name, market_name, current_datetime, user.display_name
            )
        )
        for key, value in probabilities_dict.items():
            probabilities_str = await self._message_length_check(user, probabilities_str, "{0} - {1}%\n".format(key, value))

        probabilities_str = "{0}\nMarket Efficiency = {1}%".format(probabilities_str, sum(probabilities_dict.values()))
        probabilities_str = "```{0}```".format(probabilities_str)

        display_images: list[discord.File] = []

        barplot = self.bot.graph.barplot(event_name, market_name, current_datetime, probabilities_dict)
        piechart = self.bot.graph.piechart(event_name, market_name, current_datetime, probabilities_dict)
        if barplot is not None:
            barplot_path = await self._save_graph(barplot)
            display_images.append(discord.File(barplot_path))
            os.remove(barplot_path)
        if piechart is not None:
            piechart_path = await self._save_graph(piechart)
            display_images.append(discord.File(piechart_path))
            os.remove(piechart_path)

        await user.send(probabilities_str, files=display_images)


__all__ = ["SportDataBot"]
