from discord.ext import commands
from discord.utils import get
import asyncio
import datetime
import requests
from cogs.ErrorHandle import ErrorHandle

class Currency(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='c',pass_context=True,invoke_without_command=False)
    async def c(self, ctx):
        pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.send(error)
        print(f'{type(error)}: {error}')

async def setup(bot):
    await bot.add_cog(Currency(bot))
