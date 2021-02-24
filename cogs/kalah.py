import discord
from discord.ext import commands
from bot import Curator


class Kalaha():
    pass


class Kalah(commands.Cog):
    def __init__(self, bot: Curator):
        self.bot = bot

    @commands.group(invoke_without_command=True, aliases=['kalaha', 'mancala'])
    async def kalah(self, ctx: commands.Context):
        """The base command for kalah games"""
        await ctx.send(f'This is the base command. See `{ctx.prefix}help kalah` for help on other commands.')

    @kalah.command()
    async def start(self, ctx: commands.Context, *, msg: str):
        """A template command."""
        await ctx.send(msg)


def setup(bot: Curator):
    bot.add_cog(Kalah(bot))
