import discord
from discord.ext import commands
from random import choice


class Silly(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx: commands.Context):
        author: discord.Profile = ctx.author
        await ctx.send(
            choice(('Hey', 'Hello', 'Hi', 'Ey', 'Yo', 'Sup', ':wave:', 'Good to see you', 'Greetings', 'Peace')) + ', ' + choice((ctx.author.name, 'dude', 'buddy', 'mate', choice(('bro', 'brother')), 'man', 'there', 'silly', 'you', 'master', 'traveler', 'fancypants', 'human')) + '!')

    @commands.command()
    async def echo(self, ctx: commands.Context, *, message):
        m: discord.Message = ctx.message
        await m.delete()
        await ctx.send(message)


def setup(bot: commands.Bot):
    bot.add_cog(Silly(bot))
