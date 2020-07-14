import json
import math
import os
import re
import time
import shutil
from datetime import datetime, timedelta

import betfair_api
import discord
import asyncio
from discord.ext import commands
from discord.ext.tasks import loop
from discord.enums import ChannelType


bot = commands.Bot(command_prefix='!')
betfair = betfair_api.BetFairAPI()

with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
    credentials = json.loads(f.read())['discord']

default_price_data = 'EX_BEST_OFFERS'
recent_commands = {}


@bot.command()
async def commands(ctx):
    ''' Sends caller a private message with a list of commands '''
    if ctx.channel.type != ChannelType.private:
        return

    header = 'Use ! to begin a command. Commands must all be in lowercase.\n' \
           + 'Use -- to begin a flag after a command. Flags must have no spaces.\n' \
           + '!commands - Displays a list of available commands/flags for the bot.\n' 

    aside = 'Please note: After finishing command after 5 seconds non-critical messages will be deleted.'

    general = '!refresh - Reruns last data request command to retrieve most recent data utilising originally selected criteria (event, market, price_data, ...).'

    motorsport_command = '!motorsport - Menu driven system for viewing event and market data.\n' \
                       + '              --price_data=[SP_AVAILABLE, SP_TRADED, EX_BEST_OFFERS, EX_ALL_OFFERS, EX_TRADED]\n'.format() \
                       + '              e.g !motorsport --price_data=SP_AVAILABLE\n'.format()
    motorsport = 'Please ensure all motorsport commands are in the motorsport-data channel.\n\n' \
               + '!motorsport_status - Prints available events and sub-event markets.\n' \
               + motorsport_command
    
    commands = '```{0}\n{1}```\n```{2}```\n```{3}```'.format(header, aside, general, motorsport)

    async for message in ctx.author.history(limit=None):
        if message.pinned:
            await message.delete()

    message = await ctx.author.send(commands)
    await message.pin()


@bot.command()
async def motorsport_status(ctx):
    ''' Process Motor Sport status request '''
    await status(ctx, 'Motor Sport')


async def status(ctx, sport):
    ''' Sends caller a private message of all available markets for a given sport for the user to view '''
    if not ctx.channel.type == ChannelType.private:
        return

    async with ctx.typing():
        status_str = ''
        events =  betfair.get_events(sport)
        if len(events) == 0:
            await ctx.author.send('`Currently there are no open {0} events.`'.format(sport))
            return

        for event in events:
            markets = betfair.get_event_markets(event.event.id)
            status_sub_str = '{0}\n\n'.format(event.event.name)
            for market in markets:
                status_sub_str = '{0}{1}\n'.format(status_sub_str, market.market_name)
            status_str = '{0}```{1}```\n'.format(status_str, status_sub_str)

        await ctx.author.send(status_str)


@bot.command()
async def refresh(ctx):
    ''' Refreshes last data request command with output of live data '''
    if ctx.author not in recent_commands:
        message = await ctx.author.send('`You have not made a valid data request yet. See !commands for information.`')
        time.sleep(10)
        await message.delete()
        return
   
    sport, event_name, market_name, market_id, price_data = recent_commands[ctx.author]
    if not ctx.channel.type == ChannelType.private:
        return

    async with ctx.typing(): 
        market_book = betfair.get_market_book(market_id, price_data)
        market_runners_names = betfair.get_runners_names(market_id)
        protabilities_dict = betfair.calculate_runners_probability(market_book.runners, market_runners_names)
        await display_data(ctx.author, sport, protabilities_dict, event_name, market_name, price_data)


async def message_length_check(user, original_str, appended_str):
    ''' Helper to ensure messages to discord are not over the 2000 character limit '''
    if len(original_str) + len(appended_str) + len('``````') >= 2000:
        await user.send('```{0}```'.format(original_str))
        return appended_str
    else:
        return '{0}{1}'.format(original_str, appended_str)


async def menu_selection(user, options):
    ''' Loop for user to enter menu selection ''' 
    def check(message):
        return message.author == user and message.channel.type == ChannelType.private

    while True:
        try:
            response = await bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await user.send('`Error data request has timed out. Please try again.`')
            return None

        if response.content.strip().lower() == 'exit':
            return None
        elif re.search('^[0-9]+$', response.content) and int(response.content) > 0 and int(response.content) <= len(options):
            return int(response.content)
        else:
            await user.send('`Error please make another selection or type \'exit\'.`')


async def user_select_event(user, sport, events):
    ''' Allows user to select option from a list of available events for a sport '''
    if len(events) == 0:
        await user.send('`Currently there are no open {0} events.`'.format(sport))
        return None

    events_str = 'Available {0} events: \n'.format(sport)
    for cnt, event in enumerate(events, start=1):
        temp_events_str = '{0} - {1}\n'.format(str(cnt), event.event.name)
        events_str = await message_length_check(user, events_str, temp_events_str)
    
    events_str = await message_length_check(user, events_str, '\nPlease enter an option below.')
    if len(events_str) != 0:
        await user.send('```{0}```'.format(events_str))

    response = await menu_selection(user, events)

    if response is None:
        return None
    else:
        return events[response-1]


async def user_select_market(user, event, markets):
    ''' Allows user to select option from a list of available markets for an event '''
    if len(markets) == 0:
        await user.send('`Currently there are no open markets for {0}.`'.format(event.name))
        return

    event_str = 'Available markets for {0}: \n'.format(event.name)
    for cnt, market in enumerate(markets, start=1):
        temp_event_str = '{0} - {1}\n'.format(str(cnt), market.market_name)
        event_str = await message_length_check(user, event_str, temp_event_str)
    
    event_str = await message_length_check(user, event_str, '\nPlease enter an option below.')
    if len(event_str) != 0:
        await user.send('```{0}```'.format(event_str))

    response = await menu_selection(user, markets)

    if response is None:
        return None
    else:
        return markets[response-1]


async def display_data(user, sport, protabilities_dict, event_name, market_name, price_data):
    ''' Displays data as precentages for event and market '''
    if all(math.isnan(value) for value in protabilities_dict.values()):
        await user.send('`Currently there is no valid data for {0} - {1} ({2}).`'.format(event_name, market_name, price_data))
        return

    current_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    probabilities_str = 'Event - {0}\nMarket - {1}\nPrice Data - {2}\nProcessed Datetime(UTC) - {3}\nRequested User - {4}\n\n'.format(event_name, 
                                                                                                                                      market_name,
                                                                                                                                      price_data, 
                                                                                                                                      current_datetime,
                                                                                                                                      user.display_name)
    for key, value in protabilities_dict.items():
        if not math.isnan(value):
            probabilities_str = '{0}{1} - {2}%\n'.format(probabilities_str, key, value)
    probabilities_str = '```{0}```'.format(probabilities_str)

    await user.send(probabilities_str)


async def process_price_data_flag(user, flag):
    ''' Processes the user price_data flag for validity and returns price data string '''
    price_data = ['--price_data=SP_AVAILABLE', 
                  '--price_data=SP_TRADED',
                  '--price_data=EX_BEST_OFFERS',
                  '--price_data=EX_ALL_OFFERS',
                  '--price_data=EX_TRADED']

    if flag == default_price_data:
        return flag
    elif flag in price_data:
        return flag.strip('--prince_data=')
    elif flag.startswith('--price_data='):
        await user.send('`Invalid price_data selection. Defaulted to {0}. See !commands for more information`'.format(default_price_data))
    else:
        await user.send('`Unrecognised flag. Defaulted to {0}. See !commands for more information`'.format(default_price_data))
    return default_price_data


@bot.command()
async def clear(ctx):
    ''' Clears all messages made by the bot (user will need to manually delete their own messages) '''
    async for message in ctx.author.history(limit=None):
        if message.author.id == bot.user.id:
            await message.delete()


async def sport(ctx, flag, sport):
    ''' Provides functionality to select and view data breakdown for an event market '''
    if not ctx.channel.type == ChannelType.private:
        return

    async with ctx.typing():
        events = betfair.get_events(sport)
        event = await user_select_event(ctx.author, sport, events)
        if event is None:
            return

        event_markets = betfair.get_event_markets(event.event.id)
        event_market = await user_select_market(ctx.author, event.event, event_markets)
        if event_market is None:
            return
        
        price_data = await process_price_data_flag(ctx.author, flag)
        market_book = betfair.get_market_book(event_market.market_id, price_data)
        market_runners_names = betfair.get_runners_names(event_market.market_id)        
        protabilities_dict = betfair.calculate_runners_probability(market_book.runners, market_runners_names)
        await display_data(ctx.author, sport, protabilities_dict, event.event.name, event_market.market_name, price_data)
        recent_commands[ctx.author] = (sport, event.event.name, event_market.market_name, event_market.market_id, price_data)


@bot.command()
async def motorsport(ctx, flag : str = default_price_data):
    ''' Process Motor Sport request '''
    await sport(ctx, flag, 'Motor Sport')


@bot.event
async def on_ready():
    '''Spools up services/background tasks for discord bot'''
    print('Discord bot: ONLINE')


bot.run(credentials['token'])
