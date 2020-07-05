import f1_betting_collector
import discord
from discord.ext import commands
from discord.ext.tasks import loop
import json
import regex
import os
import shutil
import time


bot = commands.Bot(command_prefix='!')

with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
    credentials = json.loads(f.read())['discord']


@bot.command()
async def status(ctx):
    ''' Prints available markets for the user to view '''
    channel = bot.get_channel(credentials['f1-channel'])
    async with ctx.typing():
        motorsport_events =  f1_betting_collector.motorsport_events
        motorsport_events_description = ""
        for event in motorsport_events:
            motorsport_events_description = motorsport_events_description + event.event.name + '\n'
        
        outright_name, outright_str = f1_betting_collector.get_championship_outright_winner_str()
        next_race_name, next_race_str = f1_betting_collector.get_next_race_str()

        e = discord.Embed(title="Motorsport Events", description=motorsport_events_description, color=0xFFFF00)
        e.add_field(name=outright_name, value=outright_str, inline=False)
        e.add_field(name=next_race_name, value=next_race_str, inline=False)
    await channel.send(embed=e)


@bot.command()
async def test(ctx):
    channel = bot.get_channel(credentials['f1-channel'])
    await channel.send("testing multiprocessing!")


f1_betting_collector = f1_betting_collector.F1BettingCollector()
bot.run(credentials['token'])