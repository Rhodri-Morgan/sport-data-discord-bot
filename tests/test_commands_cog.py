"""Tests for the /commands help cog."""

from __future__ import annotations

import discord

from sport_data_bot.cogs.commands import COMMANDS_HELP, _build_help_embed


def test_help_embed_lists_every_command():
    embed = _build_help_embed()
    assert isinstance(embed, discord.Embed)
    field_names = {field.name for field in embed.fields}
    assert {"/commands", "/sport", "/motorsport", "/rugby", "/football"}.issubset(field_names)


def test_help_embed_field_count_matches_help_table():
    embed = _build_help_embed()
    assert len(embed.fields) == len(COMMANDS_HELP)


def test_help_embed_descriptions_are_non_empty():
    embed = _build_help_embed()
    for field in embed.fields:
        assert field.value, f"Field {field.name} has empty description"


def test_help_embed_has_title_and_description():
    embed = _build_help_embed()
    assert embed.title and "Commands" in embed.title
    assert embed.description
