import discord
from discord.ext import commands

import emoji


class Debug(commands.Cog):
    """Admin-only debug commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.id in [261156531989512192, 314792415733088260] or await self.bot.is_owner(ctx.author)

    @commands.command(hidden=True)
    async def print(self, ctx: commands.Context, *, text):
        """Print some text in Python."""
        print(text)
        await ctx.send('Check the Python printer output for your results.')

    @commands.command(hidden=True)
    async def printsendchars(self, ctx: commands.Context, *, text):
        """Print every character in Python and send them in chat.

         This is useful for weird things like keycap numbers.
         """
        for char in text:
            print(char)
            await ctx.send(char if char != ' ' else '[space]')
        await ctx.send('Also check the Python printer output for your results.')

    @commands.command(hidden=True)
    async def printdemoji(self, ctx: commands.Context, emo):
        """Print the demojized version of an emoji in Python."""
        print(emoji.demojize(emo))
        await ctx.send('Check the Python printer output for your results')

    @commands.command(hidden=True)
    async def printsc(self, ctx: commands.Context):
        """Print the current server configurations for every server."""
        # print(self.bot.server_configs)
        print({f'{self.bot.get_guild(key).name} ({key})': {'logchannel': f'{value["logchannel"].name} ({value["logchannel"].id})' if value["logchannel"] else None,
                                                           'chartroles': [f'{role.name} ({role.id})' for role in value['chartroles']]}
               for (key, value) in self.bot.server_configs.items()})
        await ctx.send('Check the Python printer output for your results')

    @commands.command(hidden=True)
    async def mentions(self, ctx: commands.Context):
        await ctx.send(str([member.name for member in ctx.message.mentions]))


def setup(bot: commands.Bot):
    bot.add_cog(Debug(bot))
