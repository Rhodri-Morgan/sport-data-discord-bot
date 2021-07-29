import asyncio
import json
import math
import os
import re
import shutil
import time
from datetime import datetime, timedelta

import discord
import yagmail
from discord.enums import ChannelType
from discord.ext import commands
from discord.ext.tasks import loop

import betfair_api
import dropbox_api
import graph_producer


bot = commands.Bot(command_prefix='!')
betfair = betfair_api.BetFairAPI()
graph = graph_producer.GraphProducer()
dropbox = dropbox_api.DropBoxAPI()

with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
    credentials = json.loads(f.read())
    google_credentials = credentials['google']
    discord_credentials = credentials['discord']

user_commands = os.path.join(os.getcwd(), 'user_commands.json')
temp_images = os.path.join(os.getcwd(), 'temp_images')
images_cnt = 0


@bot.command()
async def commands(ctx):
    ''' Lists available commands '''
    print('{0} - {1} - commands()'.format(datetime.utcnow(), ctx.author))

    if ctx.channel.type != ChannelType.private:
        return

    commands = 'Use ! to begin a command.\nCommands must all be in lowercase.\nYou can type \'exit\' to end a query.\n\n' + \
               '!commands - Displays a list of available commands for the bot.\n' + \
               '!contact - Form for contacting the creator of the bot with any questions or queries.\n'+ \
               '!bug - Reporting bugs to the bot creator for diagnosis.\n'+ \
               '!clear - Deletes all bot generated messages (not users messages).\n\n'+ \
               '!my_data - Display data for user that is stored (via Dropbox) and utilised.\n'+ \
               '!delete_data - Delete stored user data.\n\n'+ \
               '!sport - Menu for choosing sport and then navigating all events.\n'+ \
               '!motorsport - Menu for navigating motorsport events.\n'+ \
               '!rugby - Menu for navigating rugby union events.\n'+ \
               '!football - Menu for navigating football events.\n'+ \
               '!refresh - Reruns last data request command to retrieve most recent data utilising originally selected criteria (sport, event, market).'
            
    async for message in ctx.author.history(limit=None):
        if message.pinned:
            await message.delete()

    message = await ctx.author.send('```{0}```'.format(commands))
    await message.pin()


@bot.command()
async def my_data(ctx):
    ''' Command for user to view their stored data '''
    print('{0} - {1} - my_data()'.format(datetime.utcnow(), ctx.author))

    command_data = await get_user_command(ctx.author.id)

    if not ctx.channel.type == ChannelType.private:
        return
    elif command_data is None:
        await ctx.author.send('`{0}/{1} - I currently have no data stored for this account.`'.format(ctx.author.name, ctx.author.id))
    else:
        command_data = {ctx.author.id: command_data}
        data_str = '{0}/{1} - I am currently storing this data via Dropbox:\n'.format(ctx.author.name, ctx.author.id)
        data_str = '```{0}``````{1}```'.format(data_str, json.dumps(command_data, indent=4, sort_keys=True))
        data_str = '{0}```To delete this data please use !delete_data.```'.format(data_str)
        await ctx.author.send(data_str)


@bot.command()
async def delete_data(ctx):
    ''' Command for user to delete their stored data '''
    print('{0} - {1} - delete_data()'.format(datetime.utcnow(), ctx.author))

    command_data = await get_user_command(ctx.author.id)

    if not ctx.channel.type == ChannelType.private:
        return
    elif command_data is None:
        await ctx.author.send('`{0}/{1} - I currently have no data stored for this account.`'.format(ctx.author.name, ctx.author.id))
    else:
        command_data = {ctx.author.id: command_data}
        data_str = '{0}/{1} - I am currently storing this data via Dropbox:\n'.format(ctx.author.name, ctx.author.id)
        data_str = '```{0}``````{1}```'.format(data_str, json.dumps(command_data, indent=4, sort_keys=True))
        data_str = '{0}```Would you like to delete this data y/n?```'.format(data_str)
        await ctx.author.send(data_str)

        def check(message):
            return message.author == ctx.author and message.channel.type == ChannelType.private

        while True:
            try:
                response = await bot.wait_for('message', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.author.send('`Error deletion request has timed out. Please try again.`')
                return None
            
            if response.content.strip().lower() == 'y':
                await delete_user_command(ctx.author.id)
                await ctx.author.send('`{0}/{1} data has been deleted. Please note if you use this bot again in the future it will start logging data.`'.format(ctx.author.name, ctx.author.id))
                break
            elif response.content.strip().lower() == 'n' or response.content.strip().lower() == 'exit':
                await ctx.author.send('`{0}/{1} data has not been deleted.`'.format(ctx.author.name, ctx.author.id))
                break
            else:
                await user.send('`Error please make another selection or type \'exit\'.`')
                break


@bot.command()
async def contact(ctx):
    ''' Sends email to dedicated email address for managing request/queries '''
    print('{0} - {1} - contact()'.format(datetime.utcnow(), ctx.author))

    if not ctx.channel.type == ChannelType.private:
        return

    await ctx.author.send('`Please enter message below (if attaching images please use mediator such as imgur). This form will timeout in 60 seconds.`')

    def check(message):
        return message.author == ctx.author and message.channel.type == ChannelType.private
    try:
        response = await bot.wait_for('message', timeout=120.0, check=check)
    except asyncio.TimeoutError:
        await ctx.author.send('`Error contact form has timed out. Please try again.`')
        return
    
    current_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    user = str(ctx.author) + '/' + str(ctx.author.id)
    yag.send(to=google_credentials['email'], subject='Query ' + current_datetime + ' ' + user, contents=[user, response.content])
    await ctx.author.send('`Your query been sent to the author.`')


@bot.command()
async def bug(ctx):
    ''' Sends email to dedicated email address for managing bugs '''
    print('{0} - {1} - bug()'.format(datetime.utcnow(), ctx.author))

    if not ctx.channel.type == ChannelType.private:
        return

    await ctx.author.send('`Please enter bug details below (if attaching images please use mediator such as imgur). This report will timeout in 60 seconds.`')

    def check(message):
        return message.author == ctx.author and message.channel.type == ChannelType.private
    try:
        response = await bot.wait_for('message', timeout=120.0, check=check)
    except asyncio.TimeoutError:
        await ctx.author.send('`Error bug report has timed out. Please try again.`')
        return
    
    current_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    user = str(ctx.author) + '/' + str(ctx.author.id)
    yag.send(to=google_credentials['email'], subject='Bug Report ' + current_datetime + ' ' + user, contents=[user,response.content])
    await ctx.author.send('`Thank you for your report. It has been sent to the author.`')


@bot.command()
async def clear(ctx):
    ''' Clears all messages made by the bot (user will need to manually delete their own messages) '''
    print('{0} - {1} - clear()'.format(datetime.utcnow(), ctx.author))

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
    plt.savefig(os.path.join(temp_images, 'image{0}.png'.format(images_cnt)), facecolor='#36393f')
    images_cnt += 1
    return os.path.join(temp_images, 'image{0}.png'.format(images_cnt-1))


async def save_user_command(user_id, sport, event_name, market_name, market_id):
    ''' Saves users last command '''
    appended_data = {user_id : {'sport':sport, 'event_name':event_name, 'market_name':market_name, 'market_id':market_id}}
    with open(user_commands) as f:
        existing_data = json.load(f)
    merged_data = {**existing_data, **appended_data}
    with open(user_commands, 'w') as f:
        json.dump(merged_data, f)


async def delete_user_command(user_id):
    ''' Deletes users last command data'''
    with open(user_commands) as f:
        data = json.load(f)
    data.pop(str(user_id))
    with open(user_commands, 'w') as f:
        json.dump(data, f)
    dropbox.upload_file(user_commands, '/user_commands.json')


async def get_user_command(user_id):
    ''' Gets stored users last command '''
    with open(user_commands) as f:
        data = json.load(f)
        if str(user_id) not in data.keys():
            return None
        else:
            return data[str(user_id)]


async def menu_selection(user, options):
    ''' Loop for user to enter menu selection ''' 
    def check(message):
        return message.author == user and message.channel.type == ChannelType.private

    while True:
        try:
            response = await bot.wait_for('message', timeout=120.0, check=check)
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


async def display_data(user, sport, probabilities_dict, event_name, market_name):
    ''' Displays data as precentages for event and market '''
    if all(math.isnan(value) for value in probabilities_dict.values()):
        await user.send('`Currently there is no valid data for {0} - {1}.`'.format(event_name, market_name))
        return

    current_datetime = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    probabilities_str = 'Event - {0}\nMarket - {1}\nProcessed Datetime(UTC) - {2}\nRequested User - {3}\n\n'.format(event_name, 
                                                                                                                    market_name, 
                                                                                                                    current_datetime,
                                                                                                                    user.display_name)
    for key, value in probabilities_dict.items():
        temp_probabilities_str =  '{0} - {1}%\n'.format(key, value)
        probabilities_str = await message_length_check(user, probabilities_str, temp_probabilities_str)

    probabilities_str = '{0}\nMarket Efficiency = {1}%'.format(probabilities_str, sum(probabilities_dict.values()))
    probabilities_str = '```{0}```'.format(probabilities_str)

    display_images = []

    barplot = graph.barplot(event_name, market_name, current_datetime, probabilities_dict)
    piechart = graph.piechart(event_name, market_name, current_datetime, probabilities_dict)
    if barplot is not None:
        display_images.append(discord.File(await save_graph(barplot)))
    if piechart is not None:
        display_images.append(discord.File(await save_graph(piechart)))
    
    await user.send(probabilities_str, files=display_images)


async def process_sport(ctx, sport):
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
        
        market_book = betfair.get_market_book(event_market.market_id)
        market_runners_names = betfair.get_runners_names(event_market.market_id)        
        probabilities_dict = betfair.calculate_runners_probability(market_book.runners, market_runners_names)
        await display_data(ctx.author, sport, probabilities_dict, event.event.name, event_market.market_name)
        await save_user_command(ctx.author.id, sport, event.event.name, event_market.market_name, event_market.market_id)


@bot.command()
async def refresh(ctx):
    ''' Refreshes last data request command with output of live data '''
    print('{0} - {1} - refresh()'.format(datetime.utcnow(), ctx.author))

    command_data = await get_user_command(ctx.author.id)

    if not ctx.channel.type == ChannelType.private:
        return
    elif command_data is None:
        await ctx.author.send('`You have not made a valid data request yet.`')

    async with ctx.typing(): 
        market_book = betfair.get_market_book(command_data['market_id'])
        market_runners_names = betfair.get_runners_names(command_data['market_id'])
        probabilities_dict = betfair.calculate_runners_probability(market_book.runners, market_runners_names)
        await display_data(ctx.author, command_data['sport'], probabilities_dict, command_data['event_name'], command_data['market_name'])


@bot.command()
async def sport(ctx):
    '''' Process user designated sport request '''
    print('{0} - {1} - sport()'.format(datetime.utcnow(), ctx.author))
    if ctx.channel.type == ChannelType.private:
        sport = await user_select_sport(ctx.author, betfair.get_event_types())
        if sport != None:
            await process_sport(ctx, sport)


@bot.command()
async def motorsport(ctx):
    ''' Process Motor Sport request '''
    print('{0} - {1} - motorsport()'.format(datetime.utcnow(), ctx.author))
    await process_sport(ctx, 'Motor Sport')


@bot.command()
async def rugby(ctx):
    ''' Process Rugby Union request '''
    print('{0} - {1} - rugby()'.format(datetime.utcnow(), ctx.author))
    await process_sport(ctx, 'Rugby Union')


@bot.command()
async def football(ctx):
    ''' Process Soccer request '''
    print('{0} - {1} - football()'.format(datetime.utcnow(), ctx.author))
    await process_sport(ctx, 'Soccer')


@loop(minutes=5)
async def upload_user_commands():
    ''' Upload user_commands to dropbox '''
    print('{0} - upload_user_commands()'.format(datetime.utcnow()))
    dropbox.upload_file(user_commands, '/user_commands.json')


@bot.event
async def on_ready():
    '''Cleans file base and spools up services/background tasks for discord bot'''    
    if os.path.exists(temp_images):
        shutil.rmtree(temp_images)
    os.mkdir(temp_images)

    if os.path.exists(user_commands):
        os.remove(user_commands)
    dropbox.download_file(None, '/user_commands.json')

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='Sport BetFair API'))
    upload_user_commands.start()
    print('{0} - Discord Bot on_ready()'.format(datetime.utcnow()))


yag = yagmail.SMTP(user=google_credentials['email'], password=google_credentials['password'])
bot.run(discord_credentials['token'])
