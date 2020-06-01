import discord
from discord.ext import commands

import emoji


class Debug(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(hidden=True)
    async def print(self, ctx: commands.Context, *, text):
        """
        Print some text
        """
        print(text)
        await ctx.send('Check the Python printer output for your results.')

    @commands.command(hidden=True)
    async def printsendchars(self, ctx: commands.Context, *, text):
        """
        Print every character (useful for weird things like keycap numbers)
        """
        for char in text:
            print(char)
            await ctx.send(char if char != ' ' else '[space]')
        await ctx.send('Also check the Python printer output for your results.')

    @commands.command(hidden=True)
    async def printdemoji(self, ctx: commands.Context, emo):
        print(emoji.demojize(emo))
        await ctx.send('Check the Python printer output for your results')

    @commands.command(hidden=True)
    async def printsc(self, ctx: commands.Context):
        """
        Print the current server configurations for every server
        """
        print(self.bot.server_configs)
        await ctx.send('Check the Python printer output for your results')


def setup(bot: commands.Bot):
    bot.add_cog(Debug(bot))
