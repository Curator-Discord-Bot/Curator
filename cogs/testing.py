import discord
from discord.ext import commands
import time
import asyncio
from aio_timers import Timer


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


def setup(bot: commands.Bot):
    bot.add_cog(Learning(bot))
