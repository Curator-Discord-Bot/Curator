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
        roles = [f'{role.name}: {len(role.members)}' for role in await ctx.guild.fetch_roles() if role.name != '@everyone']
        await ctx.send('\n'.join(roles))

    @commands.command()
    async def pie(self, ctx: commands.context, infinity: Optional[str], traveller: Optional[str]):
        if infinity == 'iie':
            if ctx.guild.id == '468366604313559040':
                labels = ['Traveler', 'Citizen', 'Squire', 'Knight', "Lord", 'Hero', 'Legend']
                sizes = []
                colors = []
                members = []
                for role in labels:
                    count = 0
                    for member in role.members:
                        if member.id in members:
                            continue
                        members.append(member.id)
                        count += 1
                    sizes.append(count)
                    colors.append(str(role.color))
            else:
                ctx.send('This isn\'t the official Inifnity Item Editor Discord server.')
        #   I could also combine this if and else to get less code lines, it will take more computing power tho
        else:
            roles = [role for role in await ctx.guild.fetch_roles() if role.name != '@everyone']
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
