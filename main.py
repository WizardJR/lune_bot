import discord
from discord.ext import commands
import asyncio
import json

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!',intents=intents)

f = open('configs.json')
configs = json.load(f)
f.close

cogs = configs['cogs']
token = configs['token']

async def main():
    for item in cogs:
        await bot.load_extension(item)

@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    print(f'Successfully logged in and booted...!')

if __name__ == '__main__':
    asyncio.run(main())
    bot.run(token)