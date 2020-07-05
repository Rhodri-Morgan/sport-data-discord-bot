import json
import os
import shutil
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord.ext.tasks import loop

import f1_betting_collector
from f1_data_logger import *


bot = commands.Bot(command_prefix='!')

f1_betting_collector = f1_betting_collector.F1BettingCollector()

datalogger_datetime = datetime(datetime.utcnow().year, datetime.utcnow().month, datetime.utcnow().day, 00, 00)

with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
    credentials = json.loads(f.read())['discord']


@loop(seconds=1)
async def f1_data_logger():
    ''' Saves and logs data at 0000 UTC '''
    if datetime.utcnow().replace(second=0, microsecond=0) == datalogger_datetime:
        print('RUNNING: f1_data_logger()')
        print(datetime.utcnow())
        f1_outright_winners = f1_betting_collector.get_championship_outright_winner_probabilities()
        print(f1_outright_winners)
        save_world_constructors_champion_data({datetime.utcnow().strftime('%Y-%m-%d'): f1_outright_winners['Winner - Constructors Championship']})
        save_world_drivers_champion_data({datetime.utcnow().strftime('%Y-%m-%d'): f1_outright_winners['Winner - Drivers Championship']})    
        datalogger_datetime = datalogger_datetime + timedelta(days=1)
        print('COMPLETED: f1_data_logger()')


@bot.command()
async def f1_status(ctx):
    ''' Prints available markets for the user to view '''
    print('RUNNING: f1_status()')
    channel = bot.get_channel(credentials['f1-channel'])
    async with ctx.typing():
        motorsport_events =  f1_betting_collector.motorsport_events
        motorsport_events_description = ''
        for event in motorsport_events:
            motorsport_events_description = motorsport_events_description + event.event.name + '\n'
        
        outright_name, outright_str = f1_betting_collector.get_championship_outright_winner_str()
        next_race_name, next_race_str = f1_betting_collector.get_next_race_str()

        e = discord.Embed(title='Motorsport Events', description=motorsport_events_description, color=0xFFFF00)
        e.add_field(name=outright_name, value=outright_str, inline=False)
        e.add_field(name=next_race_name, value=next_race_str, inline=False)
    await channel.send(embed=e)
    print('COMPLETED: f1_status()')


@bot.event
async def on_ready():
    '''Spools up services/background tasks for discord bot'''
    print('Discord bot: ONLINE')
    f1_data_logger.start()
    

bot.run(credentials['token'])
