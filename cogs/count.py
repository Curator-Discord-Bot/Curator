import datetime

import discord
from discord.ext import commands
import json
from os import path
from typing import Optional
import emoji

number_aliases = dict([
    (':keycap_0:', '0'),
    (':keycap_1:', '1'),
    (':keycap_2:', '2'),
    (':keycap_3:', '3'),
    (':keycap_4:', '4'),
    (':keycap_5:', '5'),
    (':keycap_6:', '6'),
    (':keycap_7:', '7'),
    (':keycap_8:', '8'),
    (':keycap_9:', '9'),
    (':keycap_10:', '10'),
    (':OK_hand:', '69'),
    (':hundred_points:', '100')
])


def parsed(number: str) -> str:
    s = emoji.demojize(number)
    for key in number_aliases.keys():
        s = s.replace(key, number_aliases[key])
    return s


def is_number(number: str, to_check: str) -> bool:
    return parsed(to_check) == number


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

    def attempt_count(self, counter: discord.User, count: str) -> bool:
        if self.is_next(count):
            self.last_count = datetime.datetime.utcnow()
            self.last_counter = counter.id
            self.count += 1
            if counter.id not in self.contributors.keys():
                self.contributors[counter.id] = 1
            else:
                self.contributors[counter.id] += 1
            return True
        return False

    def is_next(self, message: str):
        return is_number(str(self.count + 1), message.split()[0])


class Count(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.counting = None
        self.count_channel = None

    def is_count_channel(self, channel: discord.TextChannel):
        if self.count_channel is None:
            with open(path.join(path.dirname(path.dirname(path.abspath(__file__))), 'settings.json')) as config_file:
                data = json.load(config_file)
                guild = self.bot.get_guild(681912993621344361)
                self.count_channel = guild.get_channel(data['count_channel'])

        return channel != self.count_channel

    async def check_channel(self, channel: discord.TextChannel, message=True) -> bool:
        if self.is_count_channel(channel):
            if message:
                await channel.send(f'Count commands are intended for {self.count_channel.mention}.')
            return False
        return True

    async def check_count(self, message: discord.Message):
        print('Checking count')
        if not self.is_count_channel(message.channel) or self.counting is None:
            print(self.is_count_channel(message.channel), self.counting)
            return

        if not self.counting.attempt_count(message.author, message.content.split()[0]):
            c: Counting = self.counting
            message.channel.send('You failed, and you have ruined the count for the ' + str(len(
                c.contributors.keys)) + ' counters...\nThe count reached ' + str(c.count) + '.')
            print('Attempt failed')
        else:
            print('Attempt succeeded')

    @commands.group(invoke_without_command=True)
    async def count(self, ctx: commands.Context, count: Optional[str]):
        if not await self.check_channel(ctx.channel):
            return
        elif count is not None:
            if self.counting is None:
                await ctx.send(f'There is no ongoing count at the moment. See {ctx.prefix}help count')
            else:
                if self.counting.attempt_count(ctx.author, count):
                    await ctx.send('Count ' + count + ' accepted.')
                else:
                    await ctx.send('Count ' + count + ' rejected.')
        else:
            await ctx.send(f'You need to supply a subcommand. Try {ctx.prefix}help count')

    @count.command()
    async def start(self, ctx: commands.Context):
        await ctx.send('Count has been started. Good luck!')
        self.counting = Counting(ctx.author)

    @count.command()
    async def data(self, ctx: commands.Context):
        await ctx.send(self.counting.__dict__)

    @count.command()
    async def parse(self, ctx: commands.Context, number: str):
        parse = parsed(number)
        await ctx.send(parse)

    @count.command()
    async def source(self, ctx: commands.Context):
        file = discord.File(__file__, filename="count.py")
        await ctx.send(file=file)


def setup(bot: commands.Bot):
    bot.add_cog(Count(bot))
