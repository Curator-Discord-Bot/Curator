import discord
from discord.ext import commands
import matplotlib.pyplot as plt
from io import BytesIO


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def roles(self, ctx: commands.Context):
        roles = [f'{role.name}: {len(role.members)}' for role in await ctx.guild.fetch_roles() if role.name != '@everyone']
        await ctx.send('\n'.join(roles))

    @commands.command()
    async def pie(self, ctx: commands.context):
        roles = [role for role in await ctx.guild.fetch_roles() if role.name != '@everyone']
        labels = []
        members = []
        sizes = []
        colors = []
        for role in roles:
            count = 0
            for member in role.members:
                if member.id in members:
                    continue
                members.append(member.id)
                count += 1
            if count > 0:
                labels.append(role.name)
                sizes.append(count)
                colors.append(str(role.color))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
        plt.axis('equal')
        buf = BytesIO()
        plt.savefig(buf, format="png")
        await ctx.send(file=discord.File(buf, 'chart.png'))


def setup(bot: commands.Bot):
    bot.add_cog(Info(bot))
