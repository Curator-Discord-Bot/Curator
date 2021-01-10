import discord
from discord.ext import commands
import asyncpg
import matplotlib.pyplot as plt
from io import BytesIO
from typing import Optional

from bot import owner_or_guild_permissions
from .utils.formats import human_join
from .utils import selecting


idle_rpg_raid_id = 665938966452764682


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
        roles = self.bot.server_configs[ctx.guild.id].chartroles.copy()
        if len(roles) == 0:
            roles = sorted([role for role in await ctx.guild.fetch_roles() if role.name != '@everyone'], reverse=True)
        for role in roles.copy():
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
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        await ctx.send(file=discord.File(buf, 'chart.png'))

    @commands.command(aliases=['account'], hidden=True)
    async def lookup(self, ctx: commands.Context, user: discord.User):
        await ctx.send(f'{user}: this account was created at {user.created_at}.',
                       embed=discord.Embed(title='Avatar').set_image(url=user.avatar_url))

    @commands.command()
    async def roleid(self, ctx: commands.Context, role: discord.Role):
        """Get the ID of a role"""
        await ctx.send(role.id)

    @commands.group(aliases=['croles', 'cr'], invoke_without_command=True)
    @owner_or_guild_permissions(manage_roles=True)
    async def chartroles(self, ctx: commands.Context):
        """Commands for the list of roles to be used in information charts."""
        current_roles = self.bot.server_configs[ctx.guild.id].chartroles
        if current_roles:
            await ctx.send(f'The current roles to be used in information charts are '
                           f'{human_join([f"**{role.name}**" for role in current_roles], final="and")}'
                           f' use `{ctx.prefix}help chartroles` for information on how to change them.')

        else:
            await ctx.send(f'You currently don\'t have any roles set to be used in information charts,'
                           f' use `{ctx.prefix}chartroles set <role_ids>` to set some.')

    @chartroles.command(name='set', aliases=['choose', 'select'])
    @owner_or_guild_permissions(manage_roles=True)
    async def set_croles(self, ctx: commands.Context, *roles: discord.Role):
        """Set a list of roles to be used in information charts.

        Provide the role IDs, mentions or names as arguments.
        Duplicates will be ignored.
        """
        await selecting.set_roles(ctx, self.bot, 'chartroles', list(roles))

    @chartroles.command(name='add', aliases=['include'])
    @owner_or_guild_permissions(manage_roles=True)
    async def add_croles(self, ctx: commands.Context, *new_roles: discord.Role):
        """Add roles to the list to be used in information charts.

        Provide role IDs, mentions or names as arguments.
        Duplicates and roles that are already on the list will be ignored.
        """
        await selecting.add_roles(ctx, self.bot, 'chartroles', list(new_roles))

    @chartroles.command(name='remove', aliases=['delete'])
    @owner_or_guild_permissions(manage_roles=True)
    async def remove_croles(self, ctx: commands.Context, *roles: discord.Role):
        """Remove roles from the list to be used in information charts.

        Provide role IDs, mentions or names as arguments.
        Duplicates and roles that aren't in the list will be ignored.
        """
        await selecting.remove_roles(ctx, self.bot, 'chartroles', list(roles))

    @chartroles.command(name='clear', aliases=['wipe'])
    @owner_or_guild_permissions(manage_roles=True)
    async def clear_croles(self, ctx: commands.Context):
        """Clear the entire list of roles to be used in information charts.

        This means it will default back to using all the roles when you use a command that uses this list.
        """
        await selecting.clear_roles(ctx, self.bot, 'chartroles')

    @commands.command(aliases=['uncoolwords'])
    async def badwords(self, ctx: commands.Context):
        pass

    @commands.group(name='idlerpgraid', aliases=['idleraid', 'rpgraid'])
    async def idlerpg_raid_alert(self, ctx: commands.Context):
        pass

    @idlerpg_raid_alert.command(name='add', aliases=[])
    async def set_idlerpg_raid_alert_role(self, ctx: commands.Context):
        pass

    @idlerpg_raid_alert.command(name='remove', aliases=[])
    async def remove_idlerpg_raid_alert_role(self, ctx: commands.Context):
        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):  # todo To be changed
        if message.guild.id == 468366604313559040 and message.author.id == idle_rpg_raid_id \
                and message.content.endswith('join the raid!'):
            await message.channel.send(f'{message.guild.get_role(695770028397690911).mention}, '
                                       f'grab your weapons and head to battle, for there is a raid!')
            await message.add_reaction('<:diamond_sword:767112271704227850>')


def setup(bot: commands.Bot):
    bot.add_cog(Info(bot))
