import discord
from discord.ext import commands
import asyncpg
from typing import List

from .formats import human_join


async def set_roles(ctx: commands.Context, bot, key, table, roles: List[discord.Role]):
    """Set lists of roles in server configurations (like chartroles and selfroles)

    Ctx: The commands.Context from where this function called
    Bot: The bot
    Key: The key to use in the server_configs
    Table: The name of the database table
    Roles: A list of the roles to set
    """
    roles = list(dict.fromkeys(roles))  # Remove duplicates
    current_roles = bot.server_configs[ctx.guild.id][key]

    if current_roles:
        prompt_text = f'This will change the roles from {human_join([f"**{role}**" for role in current_roles], final="and")}' \
                      f' to {human_join([f"**{role}**" for role in roles], final="and")}, are you sure?'
        confirm = await ctx.prompt(prompt_text, reacquire=False)
        if not confirm:
            return await ctx.send('Cancelled.')

    try:
        connection: asyncpg.pool = bot.pool
        query = f'UPDATE serverconfigs SET {table} = $1 WHERE guild = $2;'
        await connection.fetchval(query, [role.id for role in roles], ctx.guild.id)
    except Exception as e:
        await ctx.send(f'Failed, `{e}` while saving the new roles to the database.')
    else:
        bot.server_configs[ctx.guild.id][key] = sorted(roles, reverse=True)
        await ctx.send(f'Role{"s" if len(roles) > 1 else ""} '
                       f'{human_join([f"**{role}**" for role in roles], final="and")} successfully set.')


async def add_roles(ctx: commands.Context, bot, key, table, new_roles: List[discord.Role]):
    """Set lists of roles in server configurations (like chartroles and selfroles)

    Ctx: The commands.Context from where this function called
    Bot: The bot
    Key: The key to use in the server_configs
    Table: The name of the database table
    New_roles: A list of the roles to add
    """
    new_roles = list(dict.fromkeys(new_roles))  # Remove duplicates
    current_roles = bot.server_configs[ctx.guild.id][key]
    new_roles = [role for role in new_roles if role not in current_roles]
    if not new_roles:
        return ctx.send('There are no roles on your list that aren\'t already selected.')

    try:
        connection: asyncpg.pool = bot.pool
        query = f'UPDATE serverconfigs SET {table} = array_cat(self_roles, $1) WHERE guild = $2;'
        await connection.fetchval(query, [role.id for role in new_roles], ctx.guild.id)
    except Exception as e:
        await ctx.send(f'Failed, `{e}` while saving the new roles to the database.')
    else:
        bot.server_configs[ctx.guild.id][key] += new_roles
        bot.server_configs[ctx.guild.id][key].sort(reverse=True)
        await ctx.send(f'Role{"s" if len(new_roles) > 1 else ""} '
                       f'{human_join([f"**{role}**" for role in new_roles], final="and")} successfully added.')


async def remove_roles(ctx: commands.Context, bot, key, table, roles: List[discord.Role]):
    """Set lists of roles in server configurations (like chartroles and selfroles)

    Ctx: The commands.Context from where this function called
    Bot: The bot
    Key: The key to use in the server_configs
    Table: The name of the database table
    Roles: A list of the roles to remove
    """
    current_roles = bot.server_configs[ctx.guild.id][key]
    to_delete = []
    for role in roles:
        if role in current_roles and role not in to_delete:
            to_delete.append(role)
    if not to_delete:
        return await ctx.send('You gave no valid roles to remove.')

    try:
        connection: asyncpg.pool = bot.pool
        query = f'UPDATE serverconfigs SET {table} = array_remove(chartroles, $1) WHERE guild = $2;'
        for role_id in [role.id for role in to_delete]:
            await connection.fetchval(query, role_id, ctx.guild.id)
    except Exception as e:
        await ctx.send(f'Failed, `{e}` while saving the new roles to the database. This might have messed up the list,'
                       f' so use `{ctx.prefix}{ctx.command.parent}` to check the current list.')
    else:
        bot.server_configs[ctx.guild.id][key] = [role for role in current_roles if role not in to_delete]
        await ctx.send(f'Role{"s" if len(to_delete) > 1 else ""} '
                       f'{human_join([f"**{role}**" for role in to_delete], final="and")} successfully removed.')


async def clear_roles(ctx: commands.Context, bot, key, table):
    """Set lists of roles in server configurations (like chartroles and selfroles)

    Ctx: The commands.Context from where this function called
    Bot: The bot
    Key: The key to use in the server_configs
    Table: The name of the database table
    """
    current_roles = bot.server_configs[ctx.guild.id][key].copy()
    if not current_roles:
        return await ctx.send('There are no roles to delete.')

    prompt_text = 'This will remove all roles from the list, are you sure?'
    confirm = await ctx.prompt(prompt_text, reacquire=False)
    if not confirm:
        return await ctx.send('Cancelled.')

    try:
        connection: asyncpg.pool = bot.pool
        query = f"UPDATE serverconfigs SET {table} = '{{}}' WHERE guild = $1;"
        await connection.fetchval(query, ctx.guild.id)
    except Exception as e:
        await ctx.send(f'Failed, `{e}` while saving the new roles to the database.')
    else:
        bot.server_configs[ctx.guild.id][key].clear()
        await ctx.send(f'Role{"s" if len(current_roles) > 1 else ""} '
                       f'{human_join([f"**{role.name}**" for role in current_roles], final="and")} successfully removed.')
