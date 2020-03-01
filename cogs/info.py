import discord
from discord.ext import commands
import matplotlib.pyplot as plt


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
        members = []
        c = {
            'type': 'pie',
            'data': {
                'labels': [role.name for role in roles],
                'datasets': [{
                    'data': []
                }]
            }
        }
        for role in roles:
            count = 0
            for member in role.members:
                if member.id in members:
                    continue
                members.append(member.id)
                count += 1
            c['data']['datasets'][0]['data'].append(count)
        print(c)
        plt.figure()
        labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
        sizes = [15, 30, 45, 10]
        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        plt.show()


def setup(bot: commands.Bot):
    bot.add_cog(Info(bot))
