import json
import math
import os
import re
import shutil
from datetime import datetime, timedelta

import betfair_api
import discord
from discord.ext import commands
from discord.ext.tasks import loop

bot = commands.Bot(command_prefix='!')

betfair = betfair_api.BetFairAPI()

with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
    credentials = json.loads(f.read())['discord']


@bot.command()
async def commands(ctx):
    ''' Sends caller a private message with a list of commands '''
    print('RUNNING: commands()')
    header_str = 'Use ! to begin a command. Commands must all be in lowercase.\n' \
               + '!commands - Displays a list of available commands for the bot.\n' 
    motorsport_str = '!motorsport_status - Prints available events and sub-event markets.\n' \
                   + '!motorsport - Menu driven system for viewing event and market data.\n'
    commands_str = '```{0}```\n```{1}```'.format(header_str, motorsport_str)
    await ctx.author.send(commands_str)
    print('COMPLETED: commands()')


async def menu_selection(channel, options):
    ''' Loop for user to enter menu selection ''' 
    while True:
        response = await bot.wait_for('message')
        if response.content.strip().lower() == 'exit':
            return None
        elif re.search('^[0-9]+$', response.content) and int(response.content) > 0 and int(response.content) <= len(options):
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

    response = await menu_selection(channel, events)

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

    response = await menu_selection(channel, markets)

    if response is None:
        return None
    else:
        return markets[response-1]


async def display_data(channel, protabilities_dict, event_name, market_name):
    ''' Displays data as precentages for event and market '''
    if all(math.isnan(value) for value in protabilities_dict.values()):
        await channel.send('`Currently there is no valid data for {0} - {1}.`'.format(event_name, market_name))
        return

    probabilities_str = 'event = {0}, market = {1}, processed_datetime = {2}\n\n'.format(event_name, market_name, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
    for key, value in protabilities_dict.items():
        if not math.isnan(value):
            probabilities_str = '{0}{1} - {2}%\n'.format(probabilities_str, key, value)
    probabilities_str = '```{0}```'.format(probabilities_str)

    await channel.send(probabilities_str)


async def status(channel, sport_str):
    ''' Prints available markets for a given sport for the user to view '''
    status_str = ''
    events =  betfair.get_events(sport_str)
    for event in events:
        markets = betfair.get_event_markets(event.event.id)
        status_sub_str = '{0}\n\n'.format(event.event.name)
        for market in markets:
            status_sub_str = '{0}{1}\n'.format(status_sub_str, market.market_name)
        status_str = '{0}```{1}```\n'.format(status_str, status_sub_str)
    await channel.send(status_str)


@bot.command()
async def motorsport_status(ctx):
    ''' Prints available markets for motor sport for the user to view '''
    print('RUNNING: motorsport_status()')
    async with ctx.typing():
        motorsport_channel = bot.get_channel(credentials['motorsport-channel'])
        await status(motorsport_channel, 'Motor Sport')
    print('COMPLETED: motorsport_status()')


@bot.command()
async def motorsport(ctx):
    ''' Provides functionality to view data breakdown for an event and market '''
    print('RUNNING: motor_sport()')
    async with ctx.typing():
        motorsport_channel = bot.get_channel(credentials['motorsport-channel'])
        motorsport_events =  betfair.get_events('Motor Sport')
        motorsport_event = await user_select_event(motorsport_channel, 'motor sport', motorsport_events)
        if motorsport_event is None:
            return

        motorsport_event_markets = betfair.get_event_markets(motorsport_event.event.id)
        motorsport_event_market = await user_select_market(motorsport_channel, motorsport_event.event, motorsport_event_markets)
        if motorsport_event_market is None:
            return

        motorsport_market_book = betfair.get_market_book(motorsport_event_market.market_id, 'EX_BEST_OFFERS')
        motorsport_market_runners_names = betfair.get_runners_names(motorsport_event_market.market_id)
        motorsport_protabilities_dict = betfair.calculate_runners_probability(motorsport_market_book.runners, motorsport_market_runners_names)
        await display_data(motorsport_channel, motorsport_protabilities_dict, motorsport_event.event.name, motorsport_event_market.market_name)
    print('COMPLETED: motor_sport()')


@bot.event
async def on_ready():
    '''Spools up services/background tasks for discord bot'''
    print('Discord bot: ONLINE')


bot.run(credentials['token'])
