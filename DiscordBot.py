import discord
from discord.ext import commands
import json
import os


bot = commands.Bot(command_prefix='!', description='F1 data streaming bot.')
bot_testing_channel = 1234567890

with open(os.path.join(os.getcwd(), 'credentials.json')) as f:
  credentials = json.loads(f.read())["discord"]


async def raceStart():
    channel = bot.get_channel(bot_testing_channel)
    await channel.send("pong")

bot.run(credentials["token"])