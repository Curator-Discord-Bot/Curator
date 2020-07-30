import discord
from discord.ext import commands
from asyncio import sleep as slp


class Template(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, name='template')
    async def base(self, ctx: commands.Context):
        """The base command for _"""
        await ctx.send(f'This is the base command. See `{ctx.prefix}help base` for help on other commands.')

    @base.command(name='template')
    async def echo(self, ctx: commands.Context, *, msg: str):
        """A template command."""
        await slp(1)
        await ctx.send(msg)


def setup(bot: commands.Bot):
    bot.add_cog(Template(bot))


def teardown():
    """Code to be executed when the cog unloads. This function is not required."""
    pass
