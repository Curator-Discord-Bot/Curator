import discord
from discord.ext import commands
from bot import Curator
import asyncpg
import matplotlib.pyplot as plt
from io import BytesIO
from typing import Optional, Union

from .utils.checks import owner_or_guild_permissions
from .utils.formats import human_join
from .utils import selecting


idle_rpg_raid_id = 665938966452764682


class Info(commands.Cog):
    def __init__(self, bot: Curator):
        self.bot = bot

    @commands.command()
    async def roles(self, ctx: commands.Context):
        """Get a list of roles in this server and the number of people that have that role"""
        roles = [f'{role.name}: {len(role.members)}' for role in sorted(await ctx.guild.fetch_roles(), reverse=True) if
                 role.name != '@everyone']
        await ctx.send('\n'.join(roles))

    @commands.group(aliases=['chart'], invoke_without_command=True)
    async def pie(self, ctx: commands.context, *roles: Optional[discord.Role]):
        """Make a pie chart of the role distribution in this server.

        Server admins can set the roles that are used for this, by default it tales all roles on the server.
        You can provide roles (by name) to ignore while making the chart.
        """
        if not roles:
            roles = self.bot.server_configs[ctx.guild.id].chartroles
            if not roles:
                return await ctx.invoke(self.pie_all)
        roles = sorted(roles, reverse=True)

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

    @pie.command(name='ignore')
    async def pie_ignore(self, ctx: commands.context, *ignore_roles: discord.Role):
        if not self.bot.server_configs[ctx.guild.id].chartroles:
            return await ctx.invoke(self.pie_all_ignore, *ignore_roles)
        roles = [role for role in self.bot.server_configs[ctx.guild.id].chartroles if role not in ignore_roles]
        await ctx.invoke(self.pie, *roles)

    @pie.group(name='all', invoke_without_command=True)
    async def pie_all(self, ctx: commands.Context):
        roles = [role for role in ctx.guild.roles if role.name != '@everyone']
        await ctx.invoke(self.pie, *roles)

    @pie_all.command(name='ignore')
    async def pie_all_ignore(self, ctx: commands.context, *ignore_roles: discord.Role):
        roles = [role for role in ctx.guild.roles if role.name != '@everyone' and role not in ignore_roles]
        await ctx.invoke(self.pie, *roles)

    @commands.command(aliases=['account'], hidden=True)
    async def lookup(self, ctx: commands.Context, user: discord.User):
        await ctx.send(f'{user}: this account was created at {user.created_at}.',
                       embed=discord.Embed(title='Avatar').set_image(url=user.avatar_url))

    @commands.command()
    async def roleid(self, ctx: commands.Context, role: discord.Role):
        """Get the ID of a role."""
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
        if type(message.channel) != discord.TextChannel:
            return

        if message.guild.id == 468366604313559040 and message.author.id == idle_rpg_raid_id \
                and message.content.endswith('join the raid!'):
            await message.channel.send(f'{message.guild.get_role(695770028397690911).mention}, '
                                       f'grab your weapons and head to battle, for there is a raid!')
            await message.add_reaction('<:diamond_sword:767112271704227850>')

    @commands.command(name='joinedat', aliases=['joindate'])
    async def joined_at(self, ctx: commands.Context, member: Optional[discord.Member]):
        if not member:
            member = ctx.author
        await ctx.send(member.joined_at)

    @owner_or_guild_permissions(manage_guild=True)
    @commands.command(name='welcomemessage', aliases=['wmessage', 'welcomem'])
    async def welcome_message(self, ctx: commands.Context, *, text: str):
        """Set a message to send when a new member joins the server.

        Use {mention} for the mention, {name} for the username, {full name} for the username with #numbers, and {id} for the id of the new member.

        Set the message to "disable" if you wish to disable this feature.
        """
        if text == 'disable':
            text = None
        else:
            text = text.replace('{mention}', '{u.mention}').replace('{name}', '{u.name}').replace('{full name}', '{u.name}#{u.discriminator}').replace('{id}', '{u.id}')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET welcome_message = $1 WHERE guild = $2;'
            await connection.fetchval(query, text, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the welcome message to the database.')
        else:
            self.bot.server_configs[ctx.guild.id].welcome_message = text
            await ctx.send('Welcome message successfully set.')

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        if self.bot.server_configs[guild.id].welcome_message:
            await guild.system_channel.send(self.bot.server_configs[guild.id].welcome_message.format(u=member))


def setup(bot: Curator):
    bot.add_cog(Info(bot))
