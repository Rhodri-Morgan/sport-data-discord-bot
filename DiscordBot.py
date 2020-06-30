import discord
from discord.ext import commands
from discord.ext.tasks import loop
import json
import os
import shutil


bot = commands.Bot(command_prefix='!', description='F1 data streaming bot.')

with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
  credentials = json.loads(f.read())['discord']


@loop(seconds=5)
async def post_update():
  '''Posts an update to discord composing of data, images, etc'''
  temp_data = os.path.join(os.getcwd(), 'temp_data')
  if os.path.exists(temp_data):

    print('Pushing update...')
    '''
    Implement functionality to parse and post data within a directory called temp_data
    temp_data may contain:
      csv of race data
      graphs and graphics
      etc
    '''

    channel = bot.get_channel(credentials['f1-channel'])
    shutil.rmtree(temp_data)


@bot.event
async def on_ready():
    '''Spools up services/background tasks for discord bot'''
    post_update.start()


bot.run(credentials['token'])