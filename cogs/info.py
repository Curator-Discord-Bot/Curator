import discord
from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def roles(self, ctx: commands.Context):
        roles = [f'{role.name}: {len(role.members)}' for role in await ctx.guild.fetch_roles()]
        await ctx.send('\n'.join(roles))


def setup(bot: commands.Bot):
    bot.add_cog(Info(bot))
