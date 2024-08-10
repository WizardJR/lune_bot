from discord.ext import commands

class ErrorHandle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class MusicError(commands.CommandError):
        def __init__(self, server, *args, **kwargs):
            super().__init__(*args, **kwargs)

async def setup(bot):
    await bot.add_cog(ErrorHandle(bot))