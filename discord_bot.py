import json
import math
import os
import re
import time
import shutil
from datetime import datetime, timedelta

import betfair_api
import graph_producer
import dropbox_api
import discord
import asyncio
import yagmail
from discord.ext import commands
from discord.ext.tasks import loop
from discord.enums import ChannelType


bot = commands.Bot(command_prefix='!')
betfair = betfair_api.BetFairAPI()
graph = graph_producer.GraphProducer()
dropbox = dropbox_api.DropBoxAPI()

with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
    credentials = json.loads(f.read())
    google_credentials = credentials['google']
    discord_credentials = credentials['discord']

default_price_data = 'EX_BEST_OFFERS'
user_commands = os.path.join(os.getcwd(), 'user_commands.json')
images = os.path.join(os.getcwd(), 'temp_images')
images_cnt = 0


@bot.command()
async def commands(ctx):
    ''' Lists available commands '''
    if ctx.channel.type != ChannelType.private:
        return

    commands = 'Use ! to begin a command. Commands must all be in lowercase.\n' + \
               'Use -- to begin a flag after a command. Flags must have no spaces.\n\n' + \
               '!commands - Displays a list of available commands/flags for the bot.\n' + \
               '!bug - Reporting bugs to the bot creator for diagnosis.\n'+ \
               '!clear - Deletes all bot generated messages (not users messages).\n\n'+ \
               '!sport [optional flags] - Menu for choosing sport and then navigating all events.\n'+ \
               '!motorsport [optional flags] - Menu for navigating motorsport events.\n'+ \
               '!rugby [optional flags] - Menu for navigating rugby union events.\n'+ \
               '!football [optional flags] - Menu for navigating football events.\n'+ \
                '!refresh - Reruns last data request command to retrieve most recent data utilising originally selected criteria (event, market, price_data, ...).\n\n'+ \
                '--price data - Filters data according to some criteria, default if not specified = EX_BEST_OFFERS.\n'+ \
                '               SP_AVAILABLE - Amount available for the BSP auction.\n'+ \
                '               SP_TRADED - Amount traded in the BSP auction.\n'+ \
                '               EX_BEST_OFFERS - Only the best prices available for each runner, to requested price depth.\n'+ \
                '               EX_ALL_OFFERS - Trumps EX_BEST_OFFERS if both settings are present.\n' + \
                '               EX_TRADED - Amount traded on the exchange.'
    
    async for message in ctx.author.history(limit=None):
        if message.pinned:
            await message.delete()

    message = await ctx.author.send('```{0}```'.format(commands))
    await message.pin()


@bot.command()
async def bug(ctx):
    ''' Sends email to dedicated email address for managing bugs '''
    if not ctx.channel.type == ChannelType.private:
        return

    await ctx.author.send('`Please enter bug details below (if attaching images please use mediator such as imgur). This report will timeout in 60 seconds.`')

    def check(message):
        return message.author == ctx.author and message.channel.type == ChannelType.private
    try:
        response = await bot.wait_for('message', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        await user.send('`Error bug report has timed out. Please try again.`')
        return
    
    current_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    yag.send(to=google_credentials['email'], subject='Bug Report ' + current_datetime + ' ' + ctx.author, contents=[response.content])
    await ctx.author.send('`Thank you for your report. It has been sent to the author.`')


@bot.command()
async def clear(ctx):
    ''' Clears all messages made by the bot (user will need to manually delete their own messages) '''
    async for message in ctx.author.history(limit=None):
        if message.author.id == bot.user.id:
            await message.delete()


async def message_length_check(user, original_str, appended_str):
    ''' Helper to ensure messages to discord are not over the 2000 character limit '''
    if len(original_str) + len(appended_str) + len('``````') >= 2000:
        await user.send('```{0}```'.format(original_str))
        return appended_str
    else:
        return '{0}{1}'.format(original_str, appended_str)


async def save_graph(plt):
    ''' Saves graph image to temporary location '''
    global images_cnt
    plt.savefig(os.path.join(images, 'image{0}.png'.format(images_cnt)), facecolor="#36393f")
    images_cnt += 1
    return os.path.join(images, 'image{0}.png'.format(images_cnt-1))


async def save_user_command(user, sport, event_name, market_name, market_id, price_data):
    ''' Saves user's last command '''
    appended_data = {str(user) : {'sport':sport, 'event_name':event_name, 'market_name':market_name, 'market_id':market_id, 'price_data':price_data}}
    with open(user_commands) as f:
        existing_data = json.load(f)
    merged_data = {**existing_data, **appended_data}
    with open(user_commands, 'w') as f:
        json.dump(merged_data, f)


async def get_user_command(user):
    ''' Gets stored user's last command '''
    with open(user_commands) as f:
        data = json.load(f)
        if str(user) not in data.keys():
            await user.send('`You have not made a valid data request yet.`')
        else:
            return data[str(user)]


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


async def user_select_sport(user, sports):
    ''' Allows user to select option from a list of available sports '''
    if len(sports) == 0:
        await user.send('`Currently there are no open sports with open events.`')
        return None

    sports_str = 'Available sports: \n'
    for cnt, sport in enumerate(sports, start=1):
        temp_sports_str = '{0} - {1}\n'.format(str(cnt), sport.event_type.name.strip())
        sports_str = await message_length_check(user, sports_str, temp_sports_str)
    
    sports_str = await message_length_check(user, sports_str, '\nPlease enter an option below.')
    if len(sports_str) != 0:
        await user.send('```{0}```'.format(sports_str))

    response = await menu_selection(user, sports)

    if response is None:
        return None
    else:
        return sports[response-1].event_type.name


async def user_select_event(user, sport, events):
    ''' Allows user to select option from a list of available events for a sport '''
    if len(events) == 0:
        await user.send('`Currently there are no open {0} events.`'.format(sport))
        return None

    events_str = 'Available {0} events: \n'.format(sport)
    for cnt, event in enumerate(events, start=1):
        temp_events_str = '{0} - {1}\n'.format(str(cnt), event.event.name.strip())
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
        temp_event_str = '{0} - {1}\n'.format(str(cnt), market.market_name.strip())
        event_str = await message_length_check(user, event_str, temp_event_str)
    
    event_str = await message_length_check(user, event_str, '\nPlease enter an option below.')
    if len(event_str) != 0:
        await user.send('```{0}```'.format(event_str))

    response = await menu_selection(user, markets)

    if response is None:
        return None
    else:
        return markets[response-1]


async def display_data(user, sport, probabilities_dict, event_name, market_name, price_data):
    ''' Displays data as precentages for event and market '''
    if all(math.isnan(value) for value in probabilities_dict.values()):
        await user.send('`Currently there is no valid data for {0} - {1} ({2}).`'.format(event_name, market_name, price_data))
        return

    current_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    probabilities_str = 'Event - {0}\nMarket - {1}\nPrice Data - {2}\nProcessed Datetime(UTC) - {3}\nRequested User - {4}\n\n'.format(event_name, 
                                                                                                                                      market_name,
                                                                                                                                      price_data, 
                                                                                                                                      current_datetime,
                                                                                                                                      user.display_name)
    for key, value in probabilities_dict.items():
        temp_probabilities_str =  '{0} - {1}%\n'.format(key, value)
        probabilities_str = await message_length_check(user, probabilities_str, temp_probabilities_str)

    probabilities_str = '```{0}```'.format(probabilities_str)

    barplot = await save_graph(graph.barplot(event_name, market_name, current_datetime, probabilities_dict))
    await user.send(probabilities_str, file=discord.File(barplot))
    os.remove(barplot)


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


async def process_sport(ctx, flag, sport):
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
        probabilities_dict = betfair.calculate_runners_probability(market_book.runners, market_runners_names)
        await display_data(ctx.author, sport, probabilities_dict, event.event.name, event_market.market_name, price_data)
        await save_user_command(ctx.author, sport, event.event.name, event_market.market_name, event_market.market_id, price_data)


@bot.command()
async def refresh(ctx):
    ''' Refreshes last data request command with output of live data '''
    command_data = await get_user_command(ctx.author)

    if command_data is None or not ctx.channel.type == ChannelType.private:
        return

    async with ctx.typing(): 
        market_book = betfair.get_market_book(command_data['market_id'], command_data['price_data'])
        market_runners_names = betfair.get_runners_names(command_data['market_id'])
        probabilities_dict = betfair.calculate_runners_probability(market_book.runners, market_runners_names)
        await display_data(ctx.author, command_data['sport'], probabilities_dict, command_data['event_name'], command_data['market_name'], command_data['price_data'])


@bot.command()
async def sport(ctx, flag : str = default_price_data):
    '''' Process user designated sport request '''
    if ctx.channel.type == ChannelType.private:
        await process_sport(ctx, flag, await user_select_sport(ctx.author, betfair.get_event_types()))


@bot.command()
async def motorsport(ctx, flag : str = default_price_data):
    ''' Process Motor Sport request '''
    await process_sport(ctx, flag, 'Motor Sport')


@bot.command()
async def rugby(ctx, flag : str = default_price_data):
    ''' Process Rugby Union request '''
    await process_sport(ctx, flag, 'Rugby Union')


@bot.command()
async def football(ctx, flag : str = default_price_data):
    ''' Process Motor Sport request '''
    await process_sport(ctx, flag, 'Soccer')


@loop(hours=1)
async def upload_user_commands():
    dropbox.upload(user_commands, '/user_commands.json')


@bot.event
async def on_ready():
    '''Spools up services/background tasks for discord bot'''
    print('Discord bot: ONLINE')
    if os.path.exists(images):
        shutil.rmtree(images)
    os.mkdir(images)

    if not dropbox.check_path_exists('/user_commands.json'):
        with open(user_commands, 'w') as f:
            empty = {}
            json.dump(empty, f)
    else:
        dropbox.download_file('/user_commands.json')

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='Sport BetFair API'))


yag = yagmail.SMTP(user=google_credentials['email'], password=google_credentials['password'])
bot.run(discord_credentials['token'])
