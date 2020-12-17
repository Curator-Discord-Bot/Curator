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
    ticket_category = db.Column(db.Integer(big=True))
    count_channels = db.Column(db.Array(sql_type=db.Integer(big=True)), default='{}')
    self_roles = db.Column(db.Array(sql_type=db.Integer(big=True)), default='{}')
    censor_words = db.Column(db.Array(sql_type=db.String), default='{}')
    censor_message = db.Column(db.String)
    raid_role = db.Column(db.Integer(big=True))


class Moderation(commands.Cog):
    """Commands to set the settings and configurations for this server. Only usable by people the appropriate permissions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(aliases=['logging', 'logs', 'log'], invoke_without_command=True)
    @owner_or_guild_permissions(manage_channels=True)
    async def logchannel(self, ctx: commands.Context):
        """Commands for the logging channel.

        This channel will be used to log deleted messages and used commands.
        """
        current_channel = self.bot.server_configs[ctx.guild.id].logchannel
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

        current_channel = self.bot.server_configs[ctx.guild.id].logchannel
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
            self.bot.server_configs[ctx.guild.id].logchannel = new_channel
            await ctx.send('Logging channel successfully set.')

    @logchannel.command(name='remove', aliases=['delete', 'stop', 'disable'])
    @owner_or_guild_permissions(manage_channels=True)
    async def remove_log(self, ctx: commands.Context):
        """Stop logging."""
        current_channel = self.bot.server_configs[ctx.guild.id].logchannel
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
            self.bot.server_configs[ctx.guild.id].logchannel = None
            await ctx.send('Logging channel successfully removed.')

    @commands.Cog.listener
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild:
            logchannel = self.bot.server_configs[message.guild.id].logchannel
            if logchannel:
                await logchannel.send(
                    f'A message by {message.author} was deleted in {message.channel.mention} on {message.guild}:'
                    f'\n{f"```{message.content}```" if len(message.content) >= 1 else "**No text**"}'
                    f'\n{"Attachments: " + str([attachment.url for attachment in message.attachments]) if message.attachments else ""}')

    @commands.group(aliases=['cswords'])
    async def censorwords(self, ctx: commands.Context):
        pass

    @censorwords.command(name='set', aliases=['choose', 'select'])
    async def set_cswords(self, ctx: commands.Context):
        pass

    @censorwords.command(name='add', aliases=['include'])
    async def add_cswords(self, ctx: commands.Context):
        pass

    @censorwords.command(name='remove', aliases=['delete'])
    async def remove_cswords(self, ctx: commands.Context):
        pass

    @censorwords.command(name='clear', aliases=['wipe'])
    async def clear_cswords(self, ctx: commands.Context):
        pass

    @commands.Cog.listener
    async def on_message(self, message: discord.Message):
        for word in self.bot.server_configs[message.guild.id].censor_words:
            if word in message:
                await message.delete()
                return await message.channel.send(self.bot.server_configs[message.guild.id].censor_message or f'Do not use uncool words {message.author.mention}!')


def setup(bot: commands.Bot):
    bot.add_cog(Moderation(bot))
