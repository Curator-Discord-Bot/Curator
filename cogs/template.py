import discord
from discord.ext import commands


class Template(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.counting = None
        self.count_channel = None

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send('Hello, ' + ctx.author.mention + '!')


def setup(bot: commands.Bot):
    bot.add_cog(Template(bot))
