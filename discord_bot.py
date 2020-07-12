import json
import math
import os
import re
import time
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

# This will need to be added to in the future for new sports
sport_channels = {'Motor Sport' : credentials['motorsport-channel']}
recent_commands = {}
data_messages = {sport_channels['Motor Sport'] : []}


@bot.command()
async def commands(ctx):
    ''' Sends caller a private message with a list of commands '''
    header_str = 'Use ! to begin a command. Commands must all be in lowercase.\n' \
               + 'Use -- to begin a flag after a command. Flags must have no spaces.\n' \
               + '!commands - Displays a list of available commands/flags for the bot.\n' 

    aside_str = 'Please note: After finishing command after 5 seconds non-critical messages will be deleted.'

    motorsport_command_str = '!motorsport - Menu driven system for viewing event and market data.\n' \
                           + '      --price_data=[SP_AVAILABLE, SP_TRADED, EX_BEST_OFFERS, EX_ALL_OFFERS, EX_TRADED]\n' \
                           + '          e.g !motorsport --price_data=SP_AVAILABLE\n'
    motorsport_str = '!motorsport_status - Prints available events and sub-event markets.\n' \
                   + motorsport_command_str
    
    commands_str = '```{0}\n{1}```\n```{2}```'.format(header_str, aside_str, motorsport_str)

    if ctx.channel.id in sport_channels.values():
        await ctx.author.send(commands_str)


@bot.command()
async def motorsport_status(ctx):
    ''' Process Motor Sport status request '''
    await status(ctx, 'Motor Sport')
    await cleanup_messages(ctx, 'Motor Sport')


async def status(ctx, sport):
    ''' Prints available markets for a given sport for the user to view '''
    channel_id = sport_channels[sport]
    channel = bot.get_channel(channel_id)
    if ctx.channel.id != channel_id:
        return

    async with ctx.typing():
        status_str = ''
        events =  betfair.get_events(sport)
        if len(events) == 0:
            await channel.send('`Currently there are no open {0} events.`'.format(sport))
            return

        for event in events:
            markets = betfair.get_event_markets(event.event.id)
            status_sub_str = '{0}\n\n'.format(event.event.name)
            for market in markets:
                status_sub_str = '{0}{1}\n'.format(status_sub_str, market.market_name)
            status_str = '{0}```{1}```\n'.format(status_str, status_sub_str)

        message = await channel.send(status_str)
        data_messages[channel.id].append(message.id)
    

@bot.command()
async def refresh(ctx):
    ''' Refreshes last data request command with output of live data '''
    if ctx.author not in recent_commands:
        await ctx.author.send('`You have not made a valid data request yet. See !commands for information.`')
        return
   
    sport, event_name, market_name, market_id, price_data = recent_commands[ctx.author]
    channel_id = sport_channels[sport]
    channel = bot.get_channel(channel_id)
    if ctx.channel.id != channel_id:
        return

    async with ctx.typing(): 
        market_book = betfair.get_market_book(market_id, price_data)
        market_runners_names = betfair.get_runners_names(market_id)
        protabilities_dict = betfair.calculate_runners_probability(market_book.runners, market_runners_names)
        await display_data(ctx.author, channel, sport, protabilities_dict, event_name, market_name)

    await cleanup_messages(ctx, sport)


async def menu_selection(user, channel, options):
    ''' Loop for user to enter menu selection ''' 
    def check(message):
        return message.author == user and message.channel.id == channel.id

    while True:
        response = await bot.wait_for('message', check=check)
        if response.content.strip().lower() == 'exit':
            return None
        elif re.search('^[0-9]+$', response.content) and int(response.content) > 0 and int(response.content) <= len(options):
            return int(response.content)
        else:
            print(response.content)
            await channel.send('`Error please make another selection or type \'exit\'.`')


async def user_select_event(user, channel, sport, events):
    ''' Allows user to select option from a list of available events for a sport '''
    if len(events) == 0:
        await channel.send('`Currently there are no open {0} events.`'.format(sport))
        return None

    events_str = 'Available {0} events: \n'.format(sport)
    for cnt, event in enumerate(events, start=1):
        events_str = '{0}{1} - {2}\n'.format(events_str, str(cnt), event.event.name)
    events_str = '```{0}\nPlease enter an option below.```'.format(events_str)
    await channel.send(events_str)

    response = await menu_selection(user, channel, events)

    if response is None:
        return None
    else:
        return events[response-1]


async def user_select_market(user, channel, event, markets):
    ''' Allows user to select option from a list of available markets for an event '''
    if len(markets) == 0:
        await channel.send('`Currently there are no open markets for {0}.`'.format(event.name))
        return

    event_str = 'Available markets for {0}: \n'.format(event.name)
    for cnt, market in enumerate(markets, start=1):
        event_str = '{0}{1} - {2}\n'.format(event_str, str(cnt), market.market_name)
    event_str = '```{0}\nPlease enter an option below.```'.format(event_str)
    await channel.send(event_str)

    response = await menu_selection(user, channel, markets)

    if response is None:
        return None
    else:
        return markets[response-1]


async def display_data(user, channel, sport, protabilities_dict, event_name, market_name):
    ''' Displays data as precentages for event and market '''
    if all(math.isnan(value) for value in protabilities_dict.values()):
        await channel.send('`Currently there is no valid data for {0} - {1}.`'.format(event_name, market_name))
        return

    probabilities_str = 'Event - {0}\nMarket - {1}\nProcessed Datetime - {2}\nRequested User - {3}\n\n'.format(event_name, 
                                                                                                                  market_name, 
                                                                                                                  datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                                                                                                                  user.display_name)
    for key, value in protabilities_dict.items():
        if not math.isnan(value):
            probabilities_str = '{0}{1} - {2}%\n'.format(probabilities_str, key, value)
    probabilities_str = '```{0}```'.format(probabilities_str)

    message = await channel.send(probabilities_str)
    data_messages[channel.id].append(message.id)


async def process_price_data_flag(channel, flag):
    ''' Processes the user price_data flag for validity and returns price data string '''
    price_data = ['--price_data=SP_AVAILABLE', 
                  '--price_data=SP_TRADED',
                  '--price_data=EX_BEST_OFFERS',
                  '--price_data=EX_ALL_OFFERS',
                  '--price_data=EX_TRADED']

    if flag == 'EX_BEST_OFFERS':
        return flag
    elif flag in price_data:
        return flag.strip('--prince_data=')
    elif flag.startswith('--price_data='):
        await channel.send('`Invalid prince_data selection. Defaulted to EX_BEST_OFFERS. See !commands for more information`')
    else:
        await channel.send('`Unrecognised flag. Defaulted to EX_BEST_OFFERS. See !commands for more information`')
    return 'EX_BEST_OFFERS'


async def cleanup_messages(ctx, sport):
    ''' Waits 5 seconds for user to read any notifications then delete all unnecessary messages '''
    time.sleep(5) 
    channel = bot.get_channel(sport_channels[sport])
    async for message in channel.history(limit=None):
        if message.id not in data_messages[channel.id]:
            await message.delete()


async def sport(ctx, flag, sport):
    ''' Provides functionality to select and view data breakdown for an event market '''
    channel_id = sport_channels[sport]
    channel = bot.get_channel(channel_id)
    if ctx.channel.id != channel_id:
        return

    async with ctx.typing():
        events = betfair.get_events(sport)
        event = await user_select_event(ctx.author, channel, sport, events)
        if event is None:
            return

        event_markets = betfair.get_event_markets(event.event.id)
        event_market = await user_select_market(ctx.author, channel, event.event, event_markets)
        if event_market is None:
            return
        
        price_data = await process_price_data_flag(channel, flag)
        market_book = betfair.get_market_book(event_market.market_id, price_data)
        market_runners_names = betfair.get_runners_names(event_market.market_id)
        protabilities_dict = betfair.calculate_runners_probability(market_book.runners, market_runners_names)
        await display_data(ctx.author, channel, sport, protabilities_dict, event.event.name, event_market.market_name)
        recent_commands[ctx.author] = (sport, event.event.name, event_market.market_name, event_market.market_id, price_data)


@bot.command()
async def motorsport(ctx, flag : str = 'EX_BEST_OFFERS'):
    ''' Process Motor Sport request '''
    sport_str = 'Motor Sport'
    await sport(ctx, flag, sport_str)
    await cleanup_messages(ctx, sport_str)


@bot.event
async def on_ready():
    '''Spools up services/background tasks for discord bot'''
    print('Discord bot: ONLINE')


bot.run(credentials['token'])
