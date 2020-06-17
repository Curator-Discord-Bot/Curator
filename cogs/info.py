import discord
from discord.ext import commands
import matplotlib.pyplot as plt
from io import BytesIO
from typing import Optional


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def roles(self, ctx: commands.Context):
        """Get a list of roles in this server and the number of people that have that role"""
        roles = [f'{role.name}: {len(role.members)}' for role in sorted(await ctx.guild.fetch_roles(), reverse=True) if
                 role.name != '@everyone']
        await ctx.send('\n'.join(roles))

    @commands.command()
    async def pie(self, ctx: commands.context, *ignore_roles: Optional[str]):
        """Make a pie chart of the role distribution in this server.

        Server admins can set the roles that are used for this, by default it tales all roles on the server.
        You can provide roles (by name) to ignore while making the chart.
        """
        roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        if len(roles) == 0:
            roles = sorted([role for role in await ctx.guild.fetch_roles() if role.name != '@everyone'], reverse=True)
        for role in roles:
            if role.name in ignore_roles:
                roles.remove(role)

        labels = []
        sizes = []
        colors = []
        members = []
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
        buf.seek(0)
        plt.close()
        await ctx.send(file=discord.File(buf, 'chart.png'))


def setup(bot: commands.Bot):
    bot.add_cog(Info(bot))
