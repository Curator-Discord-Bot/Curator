import discord
from discord.ext import commands
import time
import asyncio
from aio_timers import Timer
from typing import Union
import emoji


class Learning(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
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
    async def role(self, ctx: commands.Context, role: discord.Role):
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


def setup(bot: commands.Bot):
    bot.add_cog(Learning(bot))
