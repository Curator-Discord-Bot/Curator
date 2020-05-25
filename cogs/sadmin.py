import discord
from discord.ext import commands
import asyncpg
from typing import Optional
import cogs.utils.db as db


class Serverconfigs(db.Table):
    guild = db.Column(db.Integer(big=True), primary_key=True)
    logchannel = db.Column(db.Integer(big=True))


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

    @logchannel.command(aliases=['choose', 'select'])
    async def set(self, ctx: commands.Context, new_channel: discord.TextChannel):
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

    @logchannel.command(aliases=['delete', 'stop'])
    async def remove(self, ctx: commands.Context):
        current_channel = self.bot.server_configs[ctx.guild.id]['logchannel']
        if current_channel:
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


def setup(bot: commands.Bot):
    bot.add_cog(Sadmin(bot))
