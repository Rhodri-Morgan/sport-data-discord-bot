import json
import os
import re
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
        f1_outright_winners = f1_betting_collector.get_championship_outright_winner_probabilities()
        save_world_constructors_champion_data({datetime.utcnow().strftime('%Y-%m-%d'): f1_outright_winners['Winner - Constructors Championship']})
        save_world_drivers_champion_data({datetime.utcnow().strftime('%Y-%m-%d'): f1_outright_winners['Winner - Drivers Championship']})    
        datalogger_datetime = datalogger_datetime + timedelta(days=1)
        print('COMPLETED: f1_data_logger()')


@bot.command()
async def commands(ctx):
    print('RUNNING: commands()')
    channel = bot.get_channel(credentials['f1-channel'])
    # Prints commands


@bot.command()
async def motorsport_status(ctx):
    ''' Prints available markets for the user to view '''
    print('RUNNING: motorsport_status()')
    channel = bot.get_channel(credentials['f1-channel'])
    async with ctx.typing():
        motorsport_events =  f1_betting_collector.motorsport_events
        motorsport_events_description = ''
        for event in motorsport_events:
            motorsport_events_description = motorsport_events_description + event.event.name + '\n'
        e = discord.Embed(title='Motorsport Events', description=motorsport_events_description, color=0xFFFF00)

        outright = f1_betting_collector.get_championship_outright_winner_str()
        next_race = f1_betting_collector.get_next_race_str()
        events_markets = [outright, next_race]
        for event in events_markets:
            if event[0] is not None and event[1] is not None:
                 e.add_field(name=event[0], value=event[1], inline=False)

    await channel.send(embed=e)
    print('COMPLETED: motorsport_status()')


async def menu_selection(channel):
    ''' Loop for user to enter menu selection ''' 
    while True:
        response = await bot.wait_for('message')
        if response.content.strip().lower() == 'exit':
            return None
        elif re.search('^[0-9]+$', response.content) and int(response.content) > 0 and int(response.content) <= len(markets):
            return int(response.content)
        else:
            await channel.send('`Error please make another selection or type \'exit\'.`')


async def user_select_event(channel, sport_str, events):
    ''' Allows user to select option from a list of available events for a sport '''
    if len(events) == 0:
        await channel.send('`Currently there are no open {0} events.`'.format(sport_str))
        return None

    events_str = 'Available {0} events: \n'.format(sport_str)
    for cnt, event in enumerate(events, start=1):
        events_str = '{0}{1} - {2}\n'.format(events_str, str(cnt), event.event.name)
    events_str = '```{0}\nPlease enter an option below.```'.format(events_str)
    await channel.send(events_str)

    response = await menu_selection(channel)

    if response is None:
        return None
    else:
        return events[response-1]


async def user_select_market(channel, event, markets):
    ''' Allows user to select option from a list of available markets for an event '''
    if len(markets) == 0:
        await channel.send('`Currently there are no open markets for {0}.`'.format(event.name))
        return

    event_str = 'Available markets for {0}: \n'.format(event.name)
    for cnt, market in enumerate(markets, start=1):
        event_str = '{0}{1} - {2}\n'.format(event_str, str(cnt), market.market_name)
    event_str = '```{0}\nPlease enter an option below.```'.format(event_str)
    await channel.send(event_str)

    response = await menu_selection(channel)

    if response is None:
        return None
    else:
        return markets[response-1]


@bot.command()
async def motorsport(ctx):
    ''' Provides functionality to view data breakdown for an event and market '''
    print('RUNNING: motor_sport()')
    async with ctx.typing():
        motorsport_channel = bot.get_channel(credentials['f1-channel'])
        motorsport_events =  f1_betting_collector.motorsport_events
        motorsport_event = await user_select_event(motorsport_channel, 'motor sport', motorsport_events)
        if motorsport_event is None:
            return

        motorsport_event_markets = f1_betting_collector.get_event_markets(motorsport_event.event.id)
        motorsport_event_market = await user_select_market(motorsport_channel, motorsport_event.event, motorsport_event_markets)
        if motorsport_event_market is None:
            return

        print(motorsport_event_market)
    print('COMPLETED: motor_sport()')


@bot.event
async def on_ready():
    '''Spools up services/background tasks for discord bot'''
    print('Discord bot: ONLINE')
    f1_data_logger.start()


bot.run(credentials['token'])
