import discord
from discord.ext import commands
import asyncpg
from typing import Optional
from .utils import db, formats


class Serverconfigs(db.Table):
    guild = db.Column(db.Integer(big=True), primary_key=True)
    logchannel = db.Column(db.Integer(big=True))
    chartroles = db.Column(db.Array(sql_type=db.Integer(big=True)), default='{}')
    ticketcategory = db.Column(db.Integer(big=True))


class Sadmin(commands.Cog):
    """Commands to set the settings and configurations for this server. Only usable by people with "Manage Server" permissions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ('manage_guild', True) in ctx.author.guild_permissions or ctx.author.id in self.bot.admins:
            return True
        else:
            if not (ctx.message.content == f'{ctx.prefix}help' or ctx.message.content.startswith(f'{ctx.prefix}help ')):
                await ctx.send('Only people with "Manage Server" permissions can use commands from this category.')
            return False

    @commands.group(aliases=['logging', 'logs', 'log'], invoke_without_command=True)
    async def logchannel(self, ctx: commands.Context):
        """Commands for the logging channel.

        This channel will be used to log deleted messages and used commands.
        """
        current_channel = self.bot.server_configs[ctx.guild.id]['logchannel']
        if current_channel:
            await ctx.send(f'The current logging channel is {current_channel.mention}, '
                           f'use `{ctx.prefix}logchannel set <channel>` to change it, '
                           f'or `{ctx.prefix}logchannel remove` to stop logging.')
        else:
            await ctx.send(
                f'You currently don\'t have a logging channel, use `{ctx.prefix}logchannel set <channel>` to set one.')

    @logchannel.command(name='set', aliases=['choose', 'select'])
    async def set_log(self, ctx: commands.Context, new_channel: discord.TextChannel):
        """Set the logging channel.

        Mention the channel you want to set logging to.
        """
        current_channel = self.bot.server_configs[ctx.guild.id]['logchannel']
        if current_channel:
            prompt_text = f'This will change the logging channel from {current_channel.mention}' \
                          f' to {new_channel.mention}, are you sure?'
            confirm = await ctx.prompt(prompt_text, reacquire=False)
            if not confirm:
                return await ctx.send('Cancelled.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET logchannel = $1 WHERE guild = $2'
            await connection.fetchval(query, new_channel.id, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the logging channel to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['logchannel'] = new_channel
            await ctx.send('Logging channel successfully set.')

    @logchannel.command(name='remove', aliases=['delete', 'stop', 'disable'])
    async def remove_log(self, ctx: commands.Context):
        """Stop logging."""
        current_channel = self.bot.server_configs[ctx.guild.id]['logchannel']
        if not current_channel:
            return await ctx.send(
                f'You currently don\'t have a logging channel, use `{ctx.prefix}logchannel set <channel>` to set one.')

        prompt_text = f'This will remove {current_channel.mention} as logging channel and thus stop' \
                      f' logging, are you sure? You can always set a logging channel again with' \
                      f' `{ctx.prefix}logchannel set <channel>`.'
        confirm = await ctx.prompt(prompt_text, reacquire=False)
        if not confirm:
            return await ctx.send('Cancelled.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET logchannel = NULL WHERE guild = $1'
            await connection.fetchval(query, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while removing the logging channel from the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['logchannel'] = None
            await ctx.send('Logging channel successfully removed.')

    @commands.group(aliases=['croles'], invoke_without_command=True)
    async def chartroles(self, ctx: commands.Context):
        """Commands for the list of roles to be used in information charts."""
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        if len(current_roles) >= 1:
            await ctx.send(f'The current roles to be used in information charts are '
                           f'{formats.human_join([f"**{role.name}**" for role in current_roles], final="and")}'
                           f' use `{ctx.prefix}help chartroles` for information on how to change them.')

        else:
            await ctx.send(f'You currently don\'t have any roles set to be used in information charts,'
                           f' use `{ctx.prefix}chartroles set <role_ids>` to set some.')

    @chartroles.command('set', aliases=['choose', 'select'])
    async def set_croles(self, ctx: commands.Context, *role_ids: int):
        """Set a list of roles to be used in information charts.

        Provide the role IDs as arguments.
        """
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        new_roles = [ctx.guild.get_role(role_id) for role_id in role_ids]
        if None in new_roles:
            return await ctx.send(f'*{role_ids[new_roles.index(None)]}* is invalid.')

        if len(current_roles) >= 1:
            prompt_text = f'This will change the roles from {formats.human_join([f"**{role.name}**" for role in current_roles], final="and")}' \
                          f' to {formats.human_join([f"**{role.name}**" for role in new_roles], final="and")}, are you sure?'
            confirm = await ctx.prompt(prompt_text, reacquire=False)
            if not confirm:
                return await ctx.send('Cancelled.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET chartroles = $1 WHERE guild = $2;'
            await connection.fetchval(query, role_ids, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the new roles to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['chartroles'] = sorted(new_roles, reverse=True)
            await ctx.send(f'Role{"s" if len(new_roles) > 1 else ""} '
                           f'{formats.human_join([f"**{role.name}**" for role in new_roles], final="and")} successfully set.')

    @chartroles.command(name='add')
    async def add_croles(self, ctx: commands.Context, *role_ids: int):
        """Add roles to the list to be used in information charts.

        Provide the role IDs as arguments.
        """
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        new_roles = [ctx.guild.get_role(role_id) for role_id in role_ids if ctx.guild.get_role(role_id) not in current_roles]
        if None in new_roles or len(new_roles) == 0:
            return await ctx.send(f'*{role_ids[new_roles.index(None)]}* is invalid.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET chartroles = array_cat(chartroles, $1) WHERE guild = $2;'
            await connection.fetchval(query, role_ids, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the new roles to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['chartroles'] += new_roles
            self.bot.server_configs[ctx.guild.id]['chartroles'].sort(reverse=True)
            await ctx.send(f'Role{"s" if len(new_roles) > 1 else ""} '
                           f'{formats.human_join([f"**{role.name}**" for role in new_roles], final="and")} successfully added.')

    @chartroles.command(name='remove', aliases=['delete'])
    async def remove_croles(self, ctx: commands.Context, *role_ids: Optional[int]):
        """Remove roles from the list to be used in information charts.

        Provide the role IDs as arguments.
        """
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        to_delete = [ctx.guild.get_role(role_id) for role_id in role_ids if ctx.guild.get_role(role_id) in current_roles]
        if len(to_delete) == 0:
            return await ctx.send('You gave no valid role IDs to remove.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET chartroles = array_remove(chartroles, $1) WHERE guild = $2;'
            for role_id in [role.id for role in to_delete]:
                await connection.fetchval(query, role_id, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the new roles to the database. This might have messed up the list,'
                           f' so use `{ctx.prefix}chartroles` to check the current list.')
        else:
            self.bot.server_configs[ctx.guild.id]['chartroles'] = [role for role in current_roles if role not in to_delete]
            await ctx.send(f'Role{"s" if len(to_delete) > 1 else ""} '
                           f'{formats.human_join([f"**{role.name}**" for role in to_delete], final="and")} successfully removed.')

    @chartroles.command(name='clear')
    async def clear_croles(self, ctx: commands.Context):
        """Clear the entire list of roles to be used in information charts."""
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        if len(current_roles) == 0:
            return await ctx.send('There are no roles to delete.')

        prompt_text = f'This will remove all roles from the list, are you sure?'
        confirm = await ctx.prompt(prompt_text, reacquire=False)
        if not confirm:
            return await ctx.send('Cancelled.')
        try:
            connection: asyncpg.pool = self.bot.pool
            query = "UPDATE serverconfigs SET chartroles = '{}' WHERE guild = $1;"
            await connection.fetchval(query, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the new roles to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['chartroles'] = []
            await ctx.send(f'Role{"s" if len(current_roles) > 1 else ""} '
                           f'{formats.human_join([f"**{role.name}**" for role in current_roles], final="and")} successfully removed.')

    @commands.group(aliases=['ticketcat', 'tcat', 'supporttickets', 'sticket', 'stc'], invoke_without_command=True)
    async def ticketcategory(self, ctx: commands.Context):
        """Commands for the support tickets.

        Members can open support tickets to privately talk with staff. Channels of closed tickets will not be immediately deleted.
        """
        current_category = self.bot.server_configs[ctx.guild.id]['ticket_category']
        if current_category:
            await ctx.send(f'The current support ticket category is **{current_category}**, '
                           f'use `{ctx.prefix}ticketcategory set <category_id>` to change it, '
                           f'or `{ctx.prefix}ticketcategory remove` to disable support tickets on this server.')
        else:
            await ctx.send(f'You currently don\'t have support tickets enabled, use `{ctx.prefix}ticketcategory '
                           f'set <category_id>` to set a category and enable the ticket system.')

    @ticketcategory.command(name='set', aliases=['choose', 'select'])
    async def set_tcat(self, ctx: commands.Context, new_category_id: int):
        """Set the logging channel.
2
        Provide the id of the category you want to set for support tickets.
        """
        current_category = self.bot.server_configs[ctx.guild.id]['ticket_category']
        new_category = self.bot.get_channel(new_category_id)
        print(new_category)
        if not new_category:
            return await ctx.send('Please provide a valid category ID.')

        if current_category:
            prompt_text = f'This will change the support ticket category from **{current_category}** to **{new_category}**,' \
                          f' are you sure?'
            confirm = await ctx.prompt(prompt_text, reacquire=False)
            if not confirm:
                return await ctx.send('Cancelled.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET ticketcategory = $1 WHERE guild = $2'
            await connection.fetchval(query, new_category.id, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the support ticket category to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['ticket_category'] = new_category
            await ctx.send('Support ticket category successfully set.')

    @ticketcategory.command(name='remove', aliases=['delete', 'stop', 'disable'])
    async def remove_tcat(self, ctx: commands.Context):
        """Disable support tickets."""
        current_category = self.bot.server_configs[ctx.guild.id]['ticket_category']
        if not current_category:
            return await ctx.send(f'You currently don\'t have support tickets enabled, use `{ctx.prefix}ticketcategory '
                                  f'set <category_id>` to set a category and enable the ticket system.')

        prompt_text = f'This will remove **{current_category}** as support ticket category and thus disable the' \
                      f' ticket system, are you sure? You can always set a category again with' \
                      f' `{ctx.prefix}ticketcategory set <channel_id>`.'
        confirm = await ctx.prompt(prompt_text, reacquire=False)
        if not confirm:
            return await ctx.send('Cancelled.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET ticketcategory = NULL WHERE guild = $1'
            await connection.fetchval(query, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while removing the support ticket category from the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['ticket_category'] = None
            await ctx.send('Support ticket category successfully removed.')


def setup(bot: commands.Bot):
    bot.add_cog(Sadmin(bot))
