import discord
from discord.ext import commands
from asyncio import sleep as slp


class Template(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """This gets executed every time a command from this cog is used, return False to cancel the command. This function is not required."""
        pass

    @commands.group(invoke_without_command=True, name='template')
    async def base(self, ctx: commands.Context):
        """The base command for _"""
        await ctx.send(f'This is the base command. See `{ctx.prefix}help base` for help on other commands.')

    @base.command(name='template')
    async def echo(self, ctx: commands.Context, *, msg: str):
        """A template command (of the base group)."""
        await slp(1)
        await ctx.send(msg)


def setup(bot: commands.Bot):
    bot.add_cog(Template(bot))


def teardown():
    """Code to be executed when the cog unloads. This function is not required."""
    pass
