import discord
from discord.ext import commands
from bot import Curator
import asyncpg
from typing import Optional, Union
from .utils import db
from .utils.formats import human_join
from .utils.messages import censor_message
from .utils.converter import *
from .utils.checks import owner_or_guild_permissions


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

    def __init__(self, bot: Curator):
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

    @commands.Cog.listener()
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

    @commands.group(aliases=[])
    async def censormessage(self, ctx: commands.Context):
        pass

    @censormessage.command(name='set', aliases=['choose', 'select'])
    async def set_cmessage(self, ctx: commands.Context, *, message):
        """Set a custom message to be displayed when a member sends a censored word.

        You can use {.attribute} anywhere inside the message to insert said attribute.
        The most useful attributes are:
        .name (get the user's name)
        .display_name (get the member's display name, uses the server-specific nickname if they set one)
        .mention (mentions the member)
        Get a full list at https://discordpy.readthedocs.io/en/latest/api.html#member under **Attributes**.
        """
        pass

    @censormessage.command(name='remove', aliases=['delete'])
    async def remove_cmessage(self, ctx: commands.Context):
        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        for word in self.bot.server_configs[message.guild.id].censor_words:
            if word.lower() in message.content.lower():
                await message.delete()
                chosen_message = self.bot.server_configs[message.guild.id].censor_message
                if chosen_message:
                    return await message.channel.send(self.bot.server_configs[message.guild.id].chosen_message.format(message.author))
                else:
                    return await message.channel.send(censor_message(message))

    @commands.group(invoke_without_command=True)
    async def purge(self, ctx: commands.Context, channel: Optional[GlobalTChannelChanger], by_member: Optional[discord.Member], limit: int):
        await self.do_purge(ctx, channel, by_member, limit)

    @purge.command(name='before')
    async def purge_before(self, ctx: commands.Context, channel: Optional[GlobalTChannelChanger], message: discord.Message, by_member: Optional[discord.Member], limit: int):
        await self.do_purge(ctx, channel, by_member, limit, before=message)

    @purge.command(name='after')
    async def purge_after(self, ctx: commands.Context, channel: Optional[GlobalTChannelChanger], message: discord.Message, by_member: Optional[discord.Member], limit: int):
        await self.do_purge(ctx, channel, by_member, limit, after=message)

    @purge.command(name='between')
    async def purge_between(self, ctx: commands.Context, channel: Optional[GlobalTChannelChanger], before_message: discord.Message, after_message: discord.Message, by_member: Optional[discord.Member], limit: int):
        await self.do_purge(ctx, channel, by_member, limit, before=before_message, after=after_message)

    async def do_purge(self, ctx: commands.Context, channel: Optional[discord.TextChannel], by_member: Optional[discord.Member], limit, before=None, after=None):
        ctx.guild = ctx.message.guild
        ctx.channel = ctx.message.channel
        channel = channel or ctx.channel
        if channel not in ctx.guild.text_channels and ctx.author.id not in self.bot.admins:
            return await ctx.send('You can\'t delete message on another server.')
        elif not channel.permissions_for(ctx.author).manage_messages and ctx.author.id not in self.bot.admins:
            return await ctx.send('You need permission to manage messages in order to use this command.')

        if by_member:
            def check(message: discord.Message):
                return message.author == by_member
        else:
            check = None

        prompt_text = f'This will {f"delete (a maximum of) **{limit}** messages" if not by_member else f"go through (a maximum of) **{limit}** messages and delete all by **{by_member}** ({by_member.id})"} in **{channel}** ({channel.id}, {channel.mention}){" and".join([f" {message[0]} **{message[1].content}** by {message[1].author} ({message[1].jump_url})" for message in (("before", before), ("after", after)) if message[1]])}. Are you sure?'
        confirm = await ctx.prompt(prompt_text, timeout=30)
        if not confirm:
            return await ctx.send('You took too long to reply and the purge has been cancelled.')

        try:
            await channel.purge(limit=limit, before=before, after=after, check=check)
        except discord.Forbidden:
            await ctx.send('I do not have permission to delete these messages:grimacing:')
        except discord.HTTPException:
            await ctx.send('I failed in deleting the messages:grimacing:')
        except Exception as e:
            await ctx.send(f'There\'s been a problem while deleting the message{"s" if limit > 1 else ""} that is not '
                           f'of type "Forbidden" or "HTTPEsception", but `{type(e)}: {e}`.')


def setup(bot: Curator):
    bot.add_cog(Moderation(bot))
