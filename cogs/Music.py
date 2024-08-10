from discord.ext import commands
from discord.utils import get
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
import asyncio
import datetime
from cogs.ErrorHandle import ErrorHandle
import requests

class Music(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

        self.musicQueue = {}
        self.voiceChannels = {}

        self.YTDL_OPTIONS = {
            'format': 'bestaudio', 
            'noplaylist': True,
            'youtube_include_dash_manifest': False,
        }
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
            'options': '-vn'
        }
        self.SEARCH_API = 'https://www.youtube.com/oembed?format=json&url='

    @commands.group(name='m',pass_context=True,invoke_without_command=False)
    async def m(self, ctx):
        pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.send(error)
        print(f'{type(error)}: {error}')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if not member.id == self.bot.user.id:
            return

        if after.channel is None:
            text_channel = self.voiceChannels.pop(before.channel.id)
            if text_channel:
                await text_channel.send("Disconnected due to inactivity")

        elif before.channel is None:
            voice = after.channel.guild.voice_client
            time = 0
            while True:
                await asyncio.sleep(1)
                time = time + 1
                if voice.is_playing() and not voice.is_paused():
                    time = 0
                if after.channel.guild.id in self.musicQueue:
                    if not voice.is_playing() and self.musicQueue[after.channel.guild.id] != []:
                        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
                            try:
                                info = ydl.extract_info(self.musicQueue[after.channel.guild.id].pop(), download=False)
                            except:
                                raise ErrorHandle.MusicError(after.channel.guild, 'Error: Video not found or removed')
                            URL = info['url']
                            voice.play(FFmpegPCMAudio(URL, **self.FFMPEG_OPTIONS))
                            voice.is_playing()
                            await self.voiceChannels[after.channel.id].send(f'Now playing: {info['title']} Duration: {str(datetime.timedelta(seconds=int(info['duration'])))}')
                if time == 120:
                    await voice.disconnect()
                if not voice.is_connected():
                    break

    @m.command()
    async def join(self, ctx):
        await self.check_voice_state(ctx)
        await self.join_voice(ctx)

    @m.command()
    async def leave(self, ctx):
        await self.check_voice_state(ctx)
        await self.leave_voice(ctx)

    @m.command(brief='!m play [url] to play from YT\n !m play [keywords] to search YT')
    async def play(self, ctx, *args):
        if not self.is_connected(ctx):
            await self.join(ctx)

        if len(args) == 1:
            await self.check_youtube_link(ctx, args[0])
            await self.playURL(ctx,args[0])
        else:
            await ctx.send('Now searching, please wait...')
            with YoutubeDL(self.YTDL_OPTIONS) as ydl:
                resList = ydl.extract_info(f'ytsearch5:{' '.join(args)}', download=False)['entries']
                await ctx.send('Please select from the following in 20s:')
                for idx, item in enumerate(resList):
                    await ctx.send(f'{idx+1}.{item['title']} Duration: {str(datetime.timedelta(seconds=int(item['duration'])))}')

            def check(m):
                if m.channel == ctx.channel:
                    return m.content and m.channel

            try:
                msg = await self.bot.wait_for("message", check=check, timeout = 20)
            except:
                raise ErrorHandle.MusicError(ctx.guild, 'The choices have timed out')
            if int(msg.content) in range(1,5):
                await self.play(ctx, resList[int(msg.content)-1]['webpage_url'])

    @m.command()
    async def pause(self, ctx):
        await self.check_voice_state(ctx)
        await self.check_is_connected(ctx)
        voice = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
            await ctx.send('Paused')
        else:
            await ctx.send('Not currently playing anything')

    @m.command()
    async def resume(self, ctx):
        await self.check_voice_state(ctx)
        await self.check_is_connected(ctx)
        voice = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice.is_paused():
            voice.resume()
            await ctx.send('Resumed')
        elif voice.is_playing():
            await ctx.send('Already playing')
        else:
            await ctx.send('Not currently playing anything')

    @m.command()
    async def skip(self, ctx):
        await self.check_voice_state(ctx)
        await self.check_is_connected(ctx)
        voice = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing() or voice.is_paused():
            voice.stop()
            await ctx.send('Skipped')
        else:
            await ctx.send('Not currently playing anything')

    @m.command()
    async def stop(self, ctx):
        await self.check_voice_state(ctx)
        await self.check_is_connected(ctx)
        voice = get(ctx.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing() or voice.is_paused():
            voice.stop()
            if ctx.guild.id in self.musicQueue:
                self.musicQueue[ctx.guild.id] = []
            await ctx.send('Stopped')
        else:
            await ctx.send('Not currently playing anything')

    #Helpers
    async def join_voice(self, ctx):
        channel = ctx.author.voice.channel
        self.voiceChannels[channel.id] = ctx
        await channel.connect()

    async def leave_voice(self, ctx):
        await ctx.voice_client.disconnect()

    async def check_voice_state(self, ctx, *args):
        if ctx.author.voice is None:
            raise ErrorHandle.MusicError(ctx.guild, 'Error: You need to be in a voice channel to use this command')

    async def check_is_connected(self, ctx):
        if not self.is_connected(ctx):
            raise ErrorHandle.MusicError(ctx.guild, 'Error: Lune is not in a voice channel')
        
    async def check_youtube_link(self, ctx, url):
        r = requests.get(self.SEARCH_API + url)
        if r.status_code == 400:
            raise ErrorHandle.MusicError(ctx.guild, 'Error: Not a valid Youtube link')

    def is_connected(self, ctx):
        voice_client = get(ctx.bot.voice_clients, guild=ctx.guild)
        return voice_client and voice_client.is_connected()

    async def playURL(self, ctx, url):
        voice = get(ctx.bot.voice_clients, guild=ctx.guild)
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except:
                raise ErrorHandle.MusicError(ctx.guild, 'Error: Video not found or removed')

        if voice.is_playing():
            if ctx.guild.id not in self.musicQueue:
                self.musicQueue[ctx.guild.id] = []
            self.musicQueue[ctx.guild.id].append(url)
            await ctx.send(f'{info['title']} Duration: {str(datetime.timedelta(seconds=int(info['duration'])))} has been added to queue')
        else:
            URL = info['url']
            voice.play(FFmpegPCMAudio(URL, **self.FFMPEG_OPTIONS))
            voice.is_playing()
            await ctx.send(f'Now playing: {info['title']} Duration: {str(datetime.timedelta(seconds=int(info['duration'])))}')

async def setup(bot):
    await bot.add_cog(Music(bot))
