import discord
from discord.ext import commands
import asyncpg
from typing import Optional
import cogs.utils.db as db


class Serverconfigs(db.Table):
    guild = db.Column(db.Integer(big=True), primary_key=True)
    logchannel = db.Column(db.Integer(big=True))
    chartroles = db.Column(db.Array(sql_type=db.Integer(big=True)), default='{}')


class Sadmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ('manage_guild', True) in ctx.author.guild_permissions or ctx.author.id in [261156531989512192, 314792415733088260] or await self.bot.is_owner(ctx.author)

    @commands.group(aliases=['logging', 'logs', 'log'], invoke_without_command=True)
    async def logchannel(self, ctx: commands.Context):
        current_channel = self.bot.server_configs[ctx.guild.id]['logchannel']
        if current_channel:
            await ctx.send(f'The current logging channel is{current_channel.mention}, '
                           f'use `{ctx.prefix}logchannel set <channel>` to change it, '
                           f'or `{ctx.prefix}logchannel remove` to stop logging.')
        else:
            await ctx.send(
                f'You currently don\'t have a logging channel, use `{ctx.prefix}logchannel set <channel>` to set one.')

    @logchannel.command(name='set', aliases=['choose', 'select'])
    async def set_log(self, ctx: commands.Context, new_channel: discord.TextChannel):
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

    @logchannel.command(name='remove', aliases=['delete', 'stop'])
    async def remove_log(self, ctx: commands.Context):
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

    @commands.group(invoke_without_command=True)
    async def chartroles(self, ctx: commands.Context):
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        if len(current_roles) >= 1:
            await ctx.send(f'The current roles to be used in information charts are '
                           f'{", ".join(f"**{role.name}**" for role in current_roles[:-1])} and **{current_roles[-1].name}**,'
                           f' use `{ctx.prefix}help chartroles` for information on how to change them.')

        else:
            await ctx.send(f'You currently don\'t have any roles set to be used in information charts,'
                           f' use `{ctx.prefix}chartroles set <role_ids>` to set some.')

    @chartroles.command('set', aliases=['choose', 'select'])
    async def set_chartroles(self, ctx: commands.Context, *role_ids: int):
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        new_roles = [ctx.guild.get_role(role_id) for role_id in role_ids]
        if None in new_roles:
            return await ctx.send(f'*{role_ids[new_roles.index(None)]}* is invalid.')

        if len(current_roles) >= 1:
            prompt_text = f'This will change the roles from {", ".join(f"**{role.name}**" for role in current_roles[:-1])}' \
                          f' and **{current_roles[-1].name}** to {", ".join(f"**{role.name}**" for role in new_roles[:-1])}' \
                          f' and **{new_roles[-1].name}**, are you sure?'
            confirm = await ctx.prompt(prompt_text, reacquire=False)
            if not confirm:
                return await ctx.send('Cancelled.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET chartroles = $1 WHERE guild = $2;'
            await connection.fetchval(query, [role_id for role_id in role_ids], ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the new roles to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['chartroles'] = new_roles
            await ctx.send(f'Role{"s" if len(new_roles) > 1 else ""} {", ".join(f"**{role.name}**" for role in new_roles[:-1])}'
                           f' and **{new_roles[-1].name}** successfully set.')

    @chartroles.command(name='add')
    async def add_chartroles(self, ctx: commands.Context, *role_ids: int):
        current_roles = self.bot.server_configs[ctx.guild.id]['chartroles']
        new_roles = [ctx.guild.get_role(role_id) for role_id in role_ids if ctx.guild.get_role(role_id) not in current_roles]
        if None in new_roles or len(new_roles) == 0:
            return await ctx.send(f'You provided an invalid argument.')

        try:
            connection: asyncpg.pool = self.bot.pool
            query = 'UPDATE serverconfigs SET chartroles = array_cat(chartroles, $1) WHERE guild = $2;'
            await connection.fetchval(query, [role_id for role_id in role_ids], ctx.guild.id)
        except Exception as e:
            await ctx.send(f'Failed, {e} while saving the new roles to the database.')
        else:
            self.bot.server_configs[ctx.guild.id]['chartroles'] += new_roles
            await ctx.send(f'Role{"s" if len(new_roles) > 1 else ""} {", ".join(f"**{role.name}**" for role in new_roles[:-1])}'
                           f' and **{new_roles[-1].name}** successfully added.')

    @chartroles.command(name='remove', aliases=['delete'])
    async def remove_chartroles(self, ctx: commands.Context, *role_ids: Optional[int]):
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
            await ctx.send(f'Role{"s" if len(to_delete) > 1 else ""} {", ".join(f"**{role.name}**" for role in to_delete[:-1])}'
                           f' and **{to_delete[-1].name}** successfully removed.')

    @chartroles.command(name='clear')
    async def clear_chartroles(self, ctx: commands.Context):
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
            await ctx.send(f'Role{"s" if len(current_roles) > 1 else ""} {", ".join(f"**{role.name}**" for role in current_roles[:-1])}'
                           f' and **{current_roles[-1].name}** successfully removed.')


def setup(bot: commands.Bot):
    bot.add_cog(Sadmin(bot))
