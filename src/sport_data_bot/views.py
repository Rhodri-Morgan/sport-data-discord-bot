"""Interactive views for the sport → event → market selection flow."""

from __future__ import annotations

import logging
import math
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable

import discord

if TYPE_CHECKING:
    from sport_data_bot.bot import SportDataBot

log = logging.getLogger(__name__)

PAGE_SIZE = 25
VIEW_TIMEOUT_SECONDS = 300
DARK_THEME = "#36393f"


def _format_event_label(event_result: Any) -> str:
    """Build a Discord-safe label for an event option (max 100 chars)."""
    name = event_result.event.name.strip()
    open_date = getattr(event_result.event, "open_date", None)
    if isinstance(open_date, datetime):
        prefix = open_date.strftime("%d %b %H:%M")
        label = f"{prefix} — {name}"
    else:
        label = name
    return label[:100]


def _event_open_date(event_result: Any) -> datetime:
    """Return the event open date or a far-future fallback for sorting."""
    open_date = getattr(event_result.event, "open_date", None)
    if isinstance(open_date, datetime):
        if open_date.tzinfo is None:
            return open_date.replace(tzinfo=timezone.utc)
        return open_date
    return datetime.max.replace(tzinfo=timezone.utc)


class _OwnedView(discord.ui.View):
    """Base view restricted to the original invoking user."""

    def __init__(self, owner_id: int) -> None:
        super().__init__(timeout=VIEW_TIMEOUT_SECONDS)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Block any user other than the original requester."""
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "Only the requester can use these controls. Run the command yourself to start a new flow.",
                ephemeral=True,
            )
            return False
        return True


class SportSelectView(_OwnedView):
    """First step — pick a sport from the available BetFair event types."""

    def __init__(
        self,
        bot: SportDataBot,
        owner_id: int,
        sports: list[Any],
    ) -> None:
        super().__init__(owner_id)
        self.bot = bot

        options = [discord.SelectOption(label=s.event_type.name.strip()[:100], value=s.event_type.name.strip()) for s in sports[:PAGE_SIZE]]
        self.select = discord.ui.Select(placeholder="Choose a sport…", options=options, min_values=1, max_values=1)
        self.select.callback = self._on_pick  # type: ignore[assignment]
        self.add_item(self.select)

    async def _on_pick(self, interaction: discord.Interaction) -> None:
        sport = self.select.values[0]
        await advance_to_event(interaction, self.bot, sport, owner_id=self.owner_id)


class EventSelectView(_OwnedView):
    """Second step — pick an event for the chosen sport, paginated by 25."""

    def __init__(
        self,
        bot: SportDataBot,
        owner_id: int,
        sport: str,
        events: list[Any],
        page: int = 0,
    ) -> None:
        super().__init__(owner_id)
        self.bot = bot
        self.sport = sport
        self.events = events
        self.page = page
        self.total_pages = max(1, math.ceil(len(events) / PAGE_SIZE))

        self._build_components()

    def _build_components(self) -> None:
        self.clear_items()

        start = self.page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_events = self.events[start:end]

        options = [discord.SelectOption(label=_format_event_label(e), value=str(idx)) for idx, e in enumerate(page_events, start=start)]
        self.select = discord.ui.Select(
            placeholder=f"Choose an event ({start + 1}–{start + len(page_events)} of {len(self.events)})",
            options=options or [discord.SelectOption(label="No events", value="-1")],
            disabled=not options,
            min_values=1,
            max_values=1,
        )
        self.select.callback = self._on_pick  # type: ignore[assignment]
        self.add_item(self.select)

        prev_btn = discord.ui.Button(label="← Previous", style=discord.ButtonStyle.secondary, disabled=self.page == 0, row=1)
        prev_btn.callback = self._on_prev  # type: ignore[assignment]
        self.add_item(prev_btn)

        page_btn = discord.ui.Button(
            label=f"Page {self.page + 1}/{self.total_pages}",
            style=discord.ButtonStyle.secondary,
            disabled=True,
            row=1,
        )
        self.add_item(page_btn)

        next_btn = discord.ui.Button(
            label="Next →",
            style=discord.ButtonStyle.secondary,
            disabled=self.page >= self.total_pages - 1,
            row=1,
        )
        next_btn.callback = self._on_next  # type: ignore[assignment]
        self.add_item(next_btn)

    async def _on_prev(self, interaction: discord.Interaction) -> None:
        self.page = max(0, self.page - 1)
        self._build_components()
        await interaction.response.edit_message(embed=self._embed(), view=self)

    async def _on_next(self, interaction: discord.Interaction) -> None:
        self.page = min(self.total_pages - 1, self.page + 1)
        self._build_components()
        await interaction.response.edit_message(embed=self._embed(), view=self)

    async def _on_pick(self, interaction: discord.Interaction) -> None:
        idx = int(self.select.values[0])
        if idx < 0 or idx >= len(self.events):
            return
        event_result = self.events[idx]
        await advance_to_market(interaction, self.bot, self.sport, event_result, owner_id=self.owner_id)

    def _embed(self) -> discord.Embed:
        return discord.Embed(
            title=f"{self.sport} — Events",
            description=(
                f"Select an event below. Events are sorted by start date.\n"
                f"Showing page {self.page + 1} of {self.total_pages} ({len(self.events)} total)."
            ),
            colour=discord.Colour.blue(),
        )


class MarketSelectView(_OwnedView):
    """Third step — pick a market for the chosen event."""

    def __init__(
        self,
        bot: SportDataBot,
        owner_id: int,
        sport: str,
        event_result: Any,
        markets: list[Any],
        page: int = 0,
    ) -> None:
        super().__init__(owner_id)
        self.bot = bot
        self.sport = sport
        self.event_result = event_result
        self.markets = markets
        self.page = page
        self.total_pages = max(1, math.ceil(len(markets) / PAGE_SIZE))

        self._build_components()

    def _build_components(self) -> None:
        self.clear_items()

        start = self.page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_markets = self.markets[start:end]

        options = [discord.SelectOption(label=m.market_name.strip()[:100], value=str(idx)) for idx, m in enumerate(page_markets, start=start)]
        self.select = discord.ui.Select(
            placeholder=f"Choose a market ({start + 1}–{start + len(page_markets)} of {len(self.markets)})",
            options=options or [discord.SelectOption(label="No markets", value="-1")],
            disabled=not options,
            min_values=1,
            max_values=1,
        )
        self.select.callback = self._on_pick  # type: ignore[assignment]
        self.add_item(self.select)

        if self.total_pages > 1:
            prev_btn = discord.ui.Button(label="← Previous", style=discord.ButtonStyle.secondary, disabled=self.page == 0, row=1)
            prev_btn.callback = self._on_prev  # type: ignore[assignment]
            self.add_item(prev_btn)

            page_btn = discord.ui.Button(
                label=f"Page {self.page + 1}/{self.total_pages}",
                style=discord.ButtonStyle.secondary,
                disabled=True,
                row=1,
            )
            self.add_item(page_btn)

            next_btn = discord.ui.Button(
                label="Next →",
                style=discord.ButtonStyle.secondary,
                disabled=self.page >= self.total_pages - 1,
                row=1,
            )
            next_btn.callback = self._on_next  # type: ignore[assignment]
            self.add_item(next_btn)

    async def _on_prev(self, interaction: discord.Interaction) -> None:
        self.page = max(0, self.page - 1)
        self._build_components()
        await interaction.response.edit_message(embed=self._embed(), view=self)

    async def _on_next(self, interaction: discord.Interaction) -> None:
        self.page = min(self.total_pages - 1, self.page + 1)
        self._build_components()
        await interaction.response.edit_message(embed=self._embed(), view=self)

    async def _on_pick(self, interaction: discord.Interaction) -> None:
        idx = int(self.select.values[0])
        if idx < 0 or idx >= len(self.markets):
            return
        market = self.markets[idx]
        await render_market_results(interaction, self.bot, self.sport, self.event_result, market)

    def _embed(self) -> discord.Embed:
        return discord.Embed(
            title=f"{self.event_result.event.name} — Markets",
            description=f"{self.sport} • Select a market to see runner probabilities.",
            colour=discord.Colour.blue(),
        )


async def advance_to_event(
    interaction: discord.Interaction,
    bot: SportDataBot,
    sport: str,
    owner_id: int,
) -> None:
    """Fetch events for ``sport``, sort by start date, render the event selector."""
    assert bot.betfair is not None
    if not interaction.response.is_done():
        await interaction.response.defer()

    events = await _run_blocking(bot, lambda: bot.betfair.get_events(sport))  # type: ignore[union-attr]
    events = sorted(events, key=_event_open_date)

    if not events:
        await _safe_edit(
            interaction,
            embed=discord.Embed(
                title=f"{sport} — Events",
                description=f"There are no open {sport} events right now.",
                colour=discord.Colour.orange(),
            ),
            view=None,
        )
        return

    view = EventSelectView(bot, owner_id=owner_id, sport=sport, events=events)
    await _safe_edit(interaction, embed=view._embed(), view=view)


async def advance_to_market(
    interaction: discord.Interaction,
    bot: SportDataBot,
    sport: str,
    event_result: Any,
    owner_id: int,
) -> None:
    """Fetch markets for the chosen event and render the market selector."""
    assert bot.betfair is not None
    if not interaction.response.is_done():
        await interaction.response.defer()

    markets = await _run_blocking(bot, lambda: bot.betfair.get_event_markets(event_result.event.id))  # type: ignore[union-attr]

    if not markets:
        await _safe_edit(
            interaction,
            embed=discord.Embed(
                title=f"{event_result.event.name} — Markets",
                description="No open markets are available for this event.",
                colour=discord.Colour.orange(),
            ),
            view=None,
        )
        return

    view = MarketSelectView(bot, owner_id=owner_id, sport=sport, event_result=event_result, markets=markets)
    await _safe_edit(interaction, embed=view._embed(), view=view)


async def render_market_results(
    interaction: discord.Interaction,
    bot: SportDataBot,
    sport: str,
    event_result: Any,
    market: Any,
) -> None:
    """Pull market book data, build probability text + charts, send the final message."""
    assert bot.betfair is not None
    if not interaction.response.is_done():
        await interaction.response.defer()

    market_book = await _run_blocking(bot, lambda: bot.betfair.get_market_book(market.market_id))  # type: ignore[union-attr]
    runners_names = await _run_blocking(bot, lambda: bot.betfair.get_runners_names(market.market_id))  # type: ignore[union-attr]
    probabilities = bot.betfair.calculate_runners_probability(market_book.runners, runners_names)

    if not probabilities or all(math.isnan(v) for v in probabilities.values()):
        await _safe_edit(
            interaction,
            embed=discord.Embed(
                title=f"{event_result.event.name} — {market.market_name}",
                description="No tradeable prices currently available for this market.",
                colour=discord.Colour.orange(),
            ),
            view=None,
        )
        return

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    efficiency = round(sum(probabilities.values()), 2)

    runner_lines = "\n".join(f"{name} — {pct}%" for name, pct in probabilities.items())
    embed = discord.Embed(
        title=f"{event_result.event.name} — {market.market_name}",
        description=f"```\n{runner_lines}\n```",
        colour=discord.Colour.green() if efficiency <= 105 else discord.Colour.red(),
    )
    embed.add_field(name="Sport", value=sport, inline=True)
    embed.add_field(name="Market Efficiency", value=f"{efficiency}%", inline=True)
    embed.add_field(name="Generated", value=now_str, inline=True)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")

    files: list[discord.File] = []
    image_paths: list[str] = []
    barplot = bot.graph.barplot(event_result.event.name, market.market_name, now_str, probabilities)
    piechart = bot.graph.piechart(event_result.event.name, market.market_name, now_str, probabilities)

    from sport_data_bot.bot import TEMP_IMAGES_DIR

    if barplot is not None:
        path = TEMP_IMAGES_DIR / f"image{bot.images_cnt}.png"
        barplot.savefig(path, facecolor=DARK_THEME)
        bot.images_cnt += 1
        files.append(discord.File(str(path), filename="bar.png"))
        image_paths.append(str(path))

    if piechart is not None:
        path = TEMP_IMAGES_DIR / f"image{bot.images_cnt}.png"
        piechart.savefig(path, facecolor=DARK_THEME)
        bot.images_cnt += 1
        files.append(discord.File(str(path), filename="pie.png"))
        image_paths.append(str(path))

    try:
        await _safe_edit(interaction, embed=embed, view=None, attachments=files)
    finally:
        for path in image_paths:
            try:
                os.remove(path)
            except OSError:
                pass


async def _safe_edit(
    interaction: discord.Interaction,
    *,
    embed: discord.Embed,
    view: discord.ui.View | None,
    attachments: list[discord.File] | None = None,
) -> None:
    """Edit the original interaction message, deferring first if needed."""
    if not interaction.response.is_done():
        await interaction.response.defer()
    kwargs: dict[str, Any] = {"embed": embed, "view": view}
    if attachments is not None:
        kwargs["attachments"] = attachments
    await interaction.edit_original_response(**kwargs)


async def _run_blocking(bot: SportDataBot, func: Callable[[], Any]) -> Any:
    """Run a synchronous BetFair call in a thread executor."""
    return await bot.loop.run_in_executor(None, func)


__all__ = [
    "SportSelectView",
    "EventSelectView",
    "MarketSelectView",
    "advance_to_event",
    "advance_to_market",
    "render_market_results",
]
