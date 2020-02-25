import datetime

import discord
from discord.ext import commands
import json
from os import path
from typing import Optional


class Counting:
    def __init__(self, initiated_user: discord.User, time_start=datetime.datetime.utcnow()):
        self.initiated_user_id = initiated_user.id
        self.time_start = time_start

        self.count = 0
        self.contributors = {}

        self.last_count = time_start
        self.last_counter = None

        self.timed_out = False
        self.duration = None
        self.ruined_user_id = None

    def attempt_count(self, counter: discord.User, count: str):
        if self.is_next(count):
            self.last_count = datetime.datetime.utcnow()
            self.last_counter = counter
            self.count = self.get_next()
            return True
        return False

    def is_next(self, message: str):
        return message.split()[0] in self.get_next()

    def get_next(self):
        return [str(self.count+1)]


class Count(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.counting = None

        with open(path.join(path.dirname(path.dirname(path.abspath(__file__))), 'settings.json')) as config_file:
            data = json.load(config_file)
            guild = self.bot.get_guild(468366604313559040)
            self.count_channel = guild.get_channel(data['count_channel'])

    async def check_channel(self, ctx: commands.Context):
        if ctx.channel != self.count_channel:
            await ctx.send(f'Count commands are intended for {self.count_channel.mention}.')
            return False
        return True

    @commands.group(pass_context=True)
    async def count(self, ctx: commands.Context, count: Optional[str]):
        if not await self.check_channel(ctx):
            return
        elif ctx.invoked_subcommand is not None:
            return
        elif count is not None:
            if self.counting is None:
                await ctx.send(f'There is no ongoing count at the moment. See {ctx.prefix}help count')
            else:
                self.counting.attempt_count(ctx.author, count)
        else:
            await ctx.send(f'You need to supply a subcommand. Try {ctx.prefix}help count')

    @count.command()
    async def start(self, ctx: commands.Context):
        await ctx.send('Count has been started. Good luck!')
        self.counting = Counting(ctx.author)

    @count.command()
    async def source(self, ctx: commands.Context):
        file = discord.File(__file__, filename="count.py")
        await ctx.send(file=file)


def setup(bot: commands.Bot):
    bot.add_cog(Count(bot))
