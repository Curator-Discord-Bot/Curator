import discord
from discord.ext import commands
from bot import Curator
import time
import asyncio
from aio_timers import Timer
from typing import Optional, Union, List
import emoji
from .utils.converter import GuildChanger


class Testing(commands.Cog):
    def __init__(self, bot: Curator):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        return ctx.author.id in self.bot.admins

    @commands.command()
    async def hi(self, ctx: commands.Context):
        await ctx.send('Hello, ' + ctx.author.mention + '!')

    @commands.command()
    async def oi(self, ctx: commands.Context):
        await ctx.send('G\'day, ' + ctx.author.name + '!')

    @commands.command()
    async def add(self, ctx: commands.Context, first: int, second: int, name: int):
        await ctx.send(str(first) + ' + ' + str(second) + ' + ' + str(name) + ' = ' + str(first + second + name))

    @commands.command()
    async def greet(self, ctx: commands.Context):
        await ctx.send('Hey, Ruucas!')

    @commands.command()
    async def user(self, ctx: commands.Context, user: discord.User):
        await ctx.send(user.mention)

    @commands.command()
    async def member(self, ctx: commands.Context, member: discord.Member):
        await ctx.send(member.mention)

    @commands.command()
    async def teste(self, ctx: commands.Context):
        await ctx.send(2 == 2 == 2 != 3)

    @commands.command()
    async def sleep(self, ctx: commands.Context):
        time.sleep(2)
        await ctx.send('Hello world!')
        time.sleep(2)
        await ctx.send('Hey there!')

    @commands.command()
    async def timeout1(self, ctx: commands.Context):
        try:
            await asyncio.wait_for(self.bot.loop.create_future(), 2.0)
        except asyncio.TimeoutError:
            await ctx.send('Hello world!')

    @commands.command()
    async def timeout2(self, ctx: commands.Context):
        async def afunc():
            await ctx.send('Hello world!')
        t = Timer(2, afunc)
        await t.wait()

    @commands.command()
    async def emo(self, ctx: commands.Context, emoji: Union[discord.Emoji, discord.PartialEmoji, str]):
        await ctx.send(emoji)
        print(emoji)

    @commands.command()
    async def getrole(self, ctx: commands.Context, role: discord.Role):
        await ctx.send(role.name + ', ' + str(role.id))
        print(role.name, role.id)

    @commands.command()
    async def waitfortest1(self, ctx: commands.Context):
        await ctx.send('Say: "Test"')

        def check(message):
            return message.content == "Test" and message.channel == ctx.channel and message.author == ctx.author

        msg = await self.bot.wait_for('message', check=check)
        await ctx.send('Message received')

    @commands.command()
    async def waitfortest2(self, ctx: commands.Context):
        msg = await ctx.send('React with :white_check_mark:')

        def check(reaction, user):
            return user == ctx.author and reaction.message == msg and str(reaction.emoji) == '✅'

        await self.bot.wait_for('reaction_add', check=check)
        await ctx.send('Got it')

    @commands.command()
    async def waitforraw(self, ctx: commands.Context):
        msg = await ctx.send('React')

        async def check(payload):
            guild = self.bot.get_guild(payload.guild_id)
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            return message == msg

        payload = await self.bot.wait_for('raw_reaction_add', check=check)
        await ctx.send(payload.emoji.name)
        print(payload.emoji.name)

    @commands.command()
    async def atest(self, ctx: commands.Context, role: discord.Role):
        msg = await ctx.send('Give the go')

        def check(message):
            return message.author == ctx.author and message.content == 'Go'

        await self.bot.wait_for('message', check=check)
        print(role)
        role2 = ctx.guild.get_role(role.id)
        print(role2)
        await ctx.send(role == role2)

    @commands.command()
    async def doublewait(self, ctx: commands.Context):
        msg = await ctx.send('Reply to this message or react with :white_check_mark:, times out in 10 seconds.')
        await msg.add_reaction('✅')
        event = None

        def check1(m):
            if m.author == ctx.author and m.channel == ctx.channel:
                nonlocal event
                event = 'message'
                return True
            else:
                return False

        def check2(r, u):
            if r.message == msg and u == ctx.author and r.emoji == '✅':
                nonlocal event
                event = 'reaction'
                return True
            else:
                return False

        pending_tasks = [self.bot.wait_for('message', check=check1),
                         self.bot.wait_for('reaction_add', check=check2)]
        done_tasks, pending_tasks = await asyncio.wait(pending_tasks, timeout=10, return_when=asyncio.FIRST_COMPLETED)
        print(done_tasks)
        print(pending_tasks)
        for task in pending_tasks:
            task.cancel()
        print(pending_tasks)
        if not event:
            return await ctx.send('Timed out')
        for task in done_tasks:
            result = await task
            print(result)
            if event == 'message':  # message
                message = result
                await ctx.send(message)
            else:  # reaction
                reaction, user = result
                await ctx.send(reaction)
                await ctx.send(user)
        print(done_tasks)
        print(pending_tasks)

        """
        print(done_tasks)
        for task in done_tasks:
            done_task = task
        result = await done_task
        print(result)
        print(pending_tasks)
        await ctx.send('See the python printer.')
        for task in pending_tasks:
            pending_task = task

        pending_task.cancel()
        print(pending_task)
        something_maybe = await pending_task
        print(something_maybe)
        print(pending_task)
        return
        pending_task.cancel()
        print(pending_task.cancelled())
        maybe_something = await pending_task
        print(maybe_something)
        print(pending_task)
        print(pending_tasks)
        """

    @commands.group(aliases=['testg'])
    async def testgroup(self, ctx: commands.Context):
        """This command and the command below are to test how ctx.command works."""
        await ctx.send(ctx.command)

    @testgroup.command(aliases=['ctest'])
    async def contest(self, ctx: commands.Context):
        await ctx.send(ctx.command)

    @testgroup.group()
    async def subgroup(self, ctx: commands.Context):
        """This command is testing something else than the two commands above, this and the command below are to test subcommands of subcommands."""
        await ctx.send(ctx.command)
        await ctx.send('Sub group')

    @subgroup.command()
    async def subsubcommand(self, ctx: commands.Context):
        await ctx.send(ctx.command)
        await ctx.send('Sub Sub command')

    @commands.command()
    async def nonetest(self, ctx: commands.Context, *, argument: Optional[str]):
        print(argument)
        await ctx.send('Check the Python printer output for your results.')

    @commands.command()
    async def CAPITALS(self, ctx: commands.Context):
        """Testing commands with capitals"""
        await ctx.send('Worked')

    @commands.command()
    async def guildtest(self, ctx: commands.Context, guild: Optional[GuildChanger]):
        await ctx.send(f'Guild is **{ctx.guild}**')

    @commands.command(aliases=['gchanneltest', 'gctest'])
    async def guildchanneltest(self, ctx: commands.Context, guild: Optional[GuildChanger], channel: discord.TextChannel):
        await ctx.send(f'Guild is **{ctx.guild}**')
        await ctx.send(f'Channel is **{channel}**')

    @commands.command()
    async def listarg(self, ctx: commands.Context, arg1, arg_list: List[discord.Member], arg3):
        await ctx.send(arg1)
        await ctx.send(arg_list)
        await ctx.send(arg3)


def setup(bot: Curator):
    bot.add_cog(Testing(bot))
