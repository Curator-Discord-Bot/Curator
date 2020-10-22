import discord
from discord.ext import commands
import asyncpg
from typing import Optional, Union
from .utils import db
from .utils.formats import human_join

from bot import owner_or_guild_permissions


class Serverconfigs(db.Table):
    guild = db.Column(db.Integer(big=True), primary_key=True)
    logchannel = db.Column(db.Integer(big=True))
    chartroles = db.Column(db.Array(sql_type=db.Integer(big=True)), default='{}')
    ticketcategory = db.Column(db.Integer(big=True))
    countchannels = db.Column(db.Array(sql_type=db.Integer(big=True)), default='{}')
    self_roles = db.Column(db.Array(sql_type=db.Integer(big=True)), default='{}')


class Sadmin(commands.Cog):
    """Commands to set the settings and configurations for this server. Only usable by people the appropriate permissions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(aliases=['logging', 'logs', 'log'], invoke_without_command=True)
    @owner_or_guild_permissions(manage_channels=True)
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
    @owner_or_guild_permissions(manage_channels=True)
    async def set_log(self, ctx: commands.Context, new_channel: Union[discord.TextChannel, str]):
        """Set the logging channel.

        Mention the channel you want to set logging to.
        "Here" and "this" (not case-sensitive) work to set the channel to the channel where this command is used from.
        """
        if type(new_channel) == str:
            if new_channel.lower() == 'here' or new_channel.lower() == 'this':
                new_channel = ctx.channel
            else:
                return await ctx.send(f'{new_channel} is not a valid channel.')

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
    @owner_or_guild_permissions(manage_channels=True)
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
    @owner_or_guild_permissions(manage_roles=True)
    async def chartroles(self, ctx: commands.Context):
        """Commands for the list of roles to be used in information charts."""
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
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
        roles = list(dict.fromkeys(roles))  # Remove duplicates
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        # new_roles = [ctx.guild.get_role(role_id) for role_id in role_ids]
        # if None in new_roles:
        #     return await ctx.send(f'*{role_ids[new_roles.index(None)]}* is invalid.')

        if current_roles:
            prompt_text = f'This will change the roles from {human_join([f"**{role}**" for role in current_roles], final="and")}' \
                          f' to {human_join([f"**{role}**" for role in roles], final="and")}, are you sure?'
            confirm = await ctx.prompt(prompt_text, reacquire=False)
            if not confirm:
                return await ctx.send('Cancelled.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET chartroles = $1 WHERE guild = $2;'
            await connection.fetchval(query, [role.id for role in roles], ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the new roles to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['chartroles'] = sorted(roles, reverse=True)
            await ctx.send(f'Role{"s" if len(roles) > 1 else ""} '
                           f'{human_join([f"**{role}**" for role in roles], final="and")} successfully set.')

    @chartroles.command(name='add', aliases=['include'])
    @owner_or_guild_permissions(manage_roles=True)
    async def add_croles(self, ctx: commands.Context, *new_roles: discord.Role):
        """Add roles to the list to be used in information charts.

        Provide role IDs, mentions or names as arguments.
        Duplicates and roles that are already on the list will be ignored.
        """
        new_roles = list(dict.fromkeys(new_roles))
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        # new_roles = [ctx.guild.get_role(role_id) for role_id in role_ids if ctx.guild.get_role(role_id) not in current_roles]
        # if None in new_roles or len(new_roles) == 0:
        #     return await ctx.send(f'*{role_ids[new_roles.index(None)]}* is invalid.')
        new_roles = [role for role in new_roles if role not in current_roles]

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET chartroles = array_cat(chartroles, $1) WHERE guild = $2;'
            await connection.fetchval(query, [role.id for role in new_roles], ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the new roles to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['chartroles'] += new_roles
            self.bot.server_configs[ctx.guild.id]['chartroles'].sort(reverse=True)
            await ctx.send(f'Role{"s" if len(new_roles) > 1 else ""} '
                           f'{human_join([f"**{role}**" for role in new_roles], final="and")} successfully added.')

    @chartroles.command(name='remove', aliases=['delete'])
    @owner_or_guild_permissions(manage_roles=True)
    async def remove_croles(self, ctx: commands.Context, *roles: discord.Role):
        """Remove roles from the list to be used in information charts.

        Provide role IDs, mentions or names as arguments.
        Duplicates and roles that aren't in the list will be ignored.
        """
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        to_delete = []
        for role in roles:
            if role in current_roles and role not in to_delete:
                to_delete.append(role)
        if len(to_delete) == 0:
            return await ctx.send('You gave no valid roles to remove.')

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
                           f'{human_join([f"**{role}**" for role in to_delete], final="and")} successfully removed.')

    @chartroles.command(name='clear', aliases=['wipe'])
    @owner_or_guild_permissions(manage_roles=True)
    async def clear_croles(self, ctx: commands.Context):
        """Clear the entire list of roles to be used in information charts.

        This means it will default back to using all the roles when you use a command that uses this list.
        """
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        if len(current_roles) == 0:
            return await ctx.send('There are no roles to delete.')

        prompt_text = 'This will remove all roles from the list, are you sure?'
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
            self.bot.server_configs[ctx.guild.id]['chartroles'].clear()
            await ctx.send(f'Role{"s" if len(current_roles) > 1 else ""} '
                           f'{human_join([f"**{role.name}**" for role in current_roles], final="and")} successfully removed.')

    @commands.group(aliases=['ticketcat', 'tcat', 'supporttickets', 'sticket', 'stc'], invoke_without_command=True)
    @owner_or_guild_permissions(manage_roles=True)
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
    @owner_or_guild_permissions(manage_roles=True)
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
            query = 'UPDATE serverconfigs SET ticketcategory = $1 WHERE guild = $2;'
            await connection.fetchval(query, new_category.id, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the support ticket category to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['ticket_category'] = new_category
            await ctx.send('Support ticket category successfully set.')

    @ticketcategory.command(name='remove', aliases=['delete', 'stop', 'disable'])
    @owner_or_guild_permissions(manage_roles=True)
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
            query = 'UPDATE serverconfigs SET ticketcategory = NULL WHERE guild = $1;'
            await connection.fetchval(query, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while removing the support ticket category from the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['ticket_category'] = None
            await ctx.send('Support ticket category successfully removed.')

    @commands.group(name='selfassign', aliases=['selfroles'], invoke_without_command=True)
    @owner_or_guild_permissions(manage_roles=True)
    async def self_assign(self, ctx: commands.Context):
        """See which roles members can assign to themselves using a command. Use subcommands to change the list."""
        current_roles = self.bot.server_configs[ctx.guild.id]['self_roles']
        await ctx.send(f'Use `{ctx.prefix}help selfassign` to see the available subcommands. ' +
                       ('There are currently no roles available for people to give themselves.'
                        if not current_roles else
                        f'The currently available role{"s are" if len(current_roles) > 1 else " is"} '
                        f'{human_join([f"**{role}**" for role in current_roles], final="and")}.'))

    @self_assign.command(name='set', aliases=['choose', 'select'])
    @owner_or_guild_permissions(manage_roles=True)
    async def set_selfroles(self, ctx: commands.Context, *roles: discord.Role):
        """Set a list of roles that people can give themselves.

        Provide the role IDs, mentions or names as arguments.
        Duplicates will be ignored.
        """
        roles = list(dict.fromkeys(roles))  # Remove duplicates
        current_roles = self.bot.server_configs[ctx.guild.id]['self_roles']
        for role in roles:
            if role >= ctx.author.top_role:
                return await ctx.send(
                    f'**{role}** role is (higher than) your highest role so you cannot make it available.')

        if current_roles:
            prompt_text = f'This will change the roles from {human_join([f"**{role}**" for role in current_roles], final="and")}' \
                          f' to {human_join([f"**{role}**" for role in roles], final="and")}, are you sure?'
            confirm = await ctx.prompt(prompt_text, reacquire=False)
            if not confirm:
                return await ctx.send('Cancelled.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET self_roles = $1 WHERE guild = $2;'
            await connection.fetchval(query, [role.id for role in roles], ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the new roles to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['self_roles'] = roles
            await ctx.send(f'Role{"s" if len(roles) > 1 else ""} '
                           f'{human_join([f"**{role}**" for role in roles], final="and")} successfully set.')

    @self_assign.command(name='add', aliases=['include'])
    @owner_or_guild_permissions(manage_roles=True)
    async def add_selfroles(self, ctx: commands.Context, *new_roles: discord.Role):
        """Add roles to the list that people can assign themselves.

        Provide role IDs, mentions or names as arguments.
        Duplicates and roles that are already on the list will be ignored.
        """
        new_roles = list(dict.fromkeys(new_roles))  # Remove duplicates
        current_roles = self.bot.server_configs[ctx.guild.id]['self_roles']
        new_roles = [role for role in new_roles if role not in current_roles]

        for role in new_roles:
            if role >= ctx.author.top_role:
                return await ctx.send(
                    f'**{role}** role is (higher than) your highest role so you cannot make it available.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET self_roles = array_cat(self_roles, $1) WHERE guild = $2;'
            await connection.fetchval(query, [role.id for role in new_roles], ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the new roles to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['self_roles'] += new_roles
            await ctx.send(f'Role{"s" if len(new_roles) > 1 else ""} '
                           f'{human_join([f"**{role}**" for role in new_roles], final="and")} successfully added.')

    @self_assign.command(name='remove', aliases=['delete'])
    @owner_or_guild_permissions(manage_roles=True)
    async def remove_selfroles(self, ctx: commands.Context, *roles: discord.Role):
        """Remove roles from the list that members can take for themselves.

        Provide role IDs, mentions or names as arguments.
        Duplicates and roles that aren't in the list will be ignored.
        """
        current_roles = self.bot.server_configs[ctx.guild.id]['self_roles']
        to_delete = []
        for role in roles:
            if role >= ctx.author.top_role:
                return await ctx.send(
                    f'**{role}** role is (higher than) your highest role so you cannot remove it from the list.')

            if role in current_roles and role not in to_delete:
                to_delete.append(role)
        if not to_delete:
            return await ctx.send('You gave no valid roles to remove.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET self_roles = array_remove(self_roles, $1) WHERE guild = $2;'
            for role_id in [role.id for role in to_delete]:
                await connection.fetchval(query, role_id, ctx.guild.id)
        except Exception as e:
            await ctx.send(
                f'Failed, {e} while saving the new roles to the database. This might have messed up the list,'
                f' so use `{ctx.prefix}selfassign` to check the current list.')
        else:
            self.bot.server_configs[ctx.guild.id]['self_roles'] = [role for role in current_roles if
                                                                   role not in to_delete]
            await ctx.send(f'Role{"s" if len(to_delete) > 1 else ""} '
                           f'{human_join([f"**{role}**" for role in to_delete], final="and")} successfully removed.')

    @self_assign.command(name='clear', aliases=['wipe'])
    @owner_or_guild_permissions(manage_roles=True)
    async def clear_selfroles(self, ctx: commands.Context):
        """Clear the entire list of roles that people can give themselves."""
        current_roles = self.bot.server_configs[ctx.guild.id]['self_roles']
        if not current_roles:
            return await ctx.send('There are no roles to delete.')

        for role in current_roles:
            if role >= ctx.author.top_role:
                return await ctx.send(
                    f'**{role}** role is (higher than) your highest role so you cannot remove it from the list.')

        prompt_text = 'This will remove all roles from the list, are you sure?'
        confirm = await ctx.prompt(prompt_text, reacquire=False)
        if not confirm:
            return await ctx.send('Cancelled.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = "UPDATE serverconfigs SET self_roles = '{}' WHERE guild = $1;"
            await connection.fetchval(query, ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the new roles to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['self_roles'].clear()
            await ctx.send(f'Role{"s" if len(current_roles) > 1 else ""} '
                           f'{human_join([f"**{role.name}**" for role in current_roles], final="and")} successfully removed.')


def setup(bot: commands.Bot):
    bot.add_cog(Sadmin(bot))
