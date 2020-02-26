import discord
from discord.ext import commands


class Learning(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def hi(self, ctx: commands.Context):
        await ctx.send('Hello, ' + ctx.author.mention + '!')

    @commands.command()
    async def oi(self, ctx: commands.Context):
        await ctx.send('G\'day, ' + ctx.author.name + '!')

    @commands.command()
    async def add(self, ctx: commands.Context, first: int, second: int, name: int):
        await ctx.send(str(first) + ' + ' + str(second) + ' + ' + str(name) + ' = ' + str(first + second + name))

def setup(bot: commands.Bot):
    bot.add_cog(Learning(bot))
