import discord
from discord.ext import commands
from typing import Optional


async def get_guild_by_id(bot, ctx, ID) -> Optional[discord.Guild]:
    guild = bot.get_guild(ID)
    if guild is None:
        await ctx.send('I could not find the server:grimacing:')
        return None
    else:
        return guild


async def get_channel_by_id(bot, ctx, ID) -> Optional[discord.TextChannel]:
    channel = bot.get_channel(ID)
    if channel is None:
        await ctx.send('I could not find the channel:grimacing:')
        return None
    else:
        return channel


async def get_message_by_id(channel, ctx, ID) -> Optional[discord.Message]:
    try:
        message = await channel.fetch_message(ID)
    except discord.NotFound:
        await ctx.send('I couldn\'t find the message')
        return None
    except discord.Forbidden:
        await ctx.send('I don\'t have permission to get to the message')
        return None
    except discord.HTTPException:
        await ctx.send('I failed in getting to the message')
        return None
    except Exception as e:
        await ctx.send(f'There\'s been a problem while getting the message that\'s not of type "NotFound", "Forbidden"'
                       f' or "HTTPException", but `{type(e)}: {e}`.')
        return None
    else:
        return message


class Template(commands.Cog):
    """Commands that can be used to take control over the bot's actions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        if ctx.author.id in self.bot.admins:
            return True
        if not ctx.command.name == 'help':
            await ctx.send(f'This command is only for the bot admin{"" if len(self.bot.admins) == 1 else "s"}.')
        return False

    @commands.command(hidden=True)
    async def echo(self, ctx: commands.Context, *, message):  # TODO: implement delete_after?
        """Let the bot delete and resend your message."""
        m: discord.Message = ctx.message
        await m.delete()
        await ctx.send(message)

    @commands.command(hidden=True)
    async def dm(self, ctx: commands.Context, user: discord.User, *, message):  # TODO: implement delete_after?
        """Send a DM to a user."""
        if not user.dm_channel:
            await user.create_dm()
        try:
            await user.dm_channel.send(message)
        except discord.Forbidden:
            await ctx.send('I don\'t have permission to send this message:grimacing:')
        except discord.HTTPException:
            await ctx.send('I failed in sending the message:grimacing:')
        except Exception as e:
            await ctx.send(f'There\'s been a problem while sending the message that\'s not of type "Forbidden" or'
                           f' "HTTPException", but `{type(e)}: {e}`.')
        else:
            await ctx.send(f'Message sent to {user.name}')

    @commands.command(hidden=True)
    async def reply(self, ctx: commands.Context, *, message):
        """Send a DM to the user I last received a DM from."""
        if self.bot.last_dm:
            await ctx.invoke(self.dm, self.bot.last_dm, message=message)
        else:
            await ctx.send(f'There is no last user stored, try `{ctx.prefix}dm <user> <message>`.')

    @commands.command(hidden=True)
    async def send(self, ctx: commands.Context, channel: discord.TextChannel, *, message):  # TODO: implement delete_after?
        """Send a message in a channel."""
        try:
            await channel.send(message)
        except discord.Forbidden:
            await ctx.send('I don\'t have permission to send this message:grimacing:')
        except discord.HTTPException:
            await ctx.send('I failed in sending the message:grimacing:')
        except Exception as e:
            await ctx.send(f'There\'s been a problem that\'s not of type "Forbidden" or "HTTPException", but `{type(e)}: {e}`.')
        else:
            await ctx.send(f'Message sent in server "{channel.guild.name}" in channel "{channel.mention}":'
                           f' {channel.last_message.jump_url}.')

    @commands.command(hidden=True)
    async def edit(self, ctx: commands.Context, message_link, *, new_message):  # TODO: implement delete_after?
        """Edit a message."""
        IDs = message_link.split('/')[-2:]
        channel = await get_channel_by_id(self.bot, ctx, int(IDs[0]))
        if channel:
            message = await get_message_by_id(channel, ctx, int(IDs[1]))
            if message:
                old_content = message.content
                try:
                    await message.edit(content=new_message)
                except discord.Forbidden:
                    await ctx.send('This message isn\'t mine:grimacing:')
                except discord.HTTPException:
                    await ctx.send('I failed in editing the message:grimacing:')
                except Exception as e:
                    await ctx.send(f'There\'s been a problem while editing the message that\'s not of type "Forbidden"'
                                   f' or "HTTPException", but `{type(e)}: {e}`.')
                else:
                    await ctx.send(f'Message "{old_content}" edited in server "{channel.guild.name}" in channel'
                                   f' "{channel.mention}".')

    @commands.command(hidden=True)
    async def react(self, ctx: commands.Context, message_link, *emojis):
        """React to a message."""
        IDs = message_link.split('/')[-2:]
        channel = await get_channel_by_id(self.bot, ctx, int(IDs[0]))
        if channel:
            message = await get_message_by_id(channel, ctx, int(IDs[1]))
            if message:
                successes = []
                for emoji in emojis:
                    try:
                        await message.add_reaction(emoji)
                    except discord.Forbidden:
                        return await ctx.send('I don\'t have permission to react to the message:grimacing:')
                    except discord.NotFound:
                        await ctx.send(f'"{emoji}" was not found:grimacing:')
                    except discord.InvalidArgument:
                        await ctx.send(f'"{emoji}" is invalid:grimacing:')
                    except discord.HTTPException:
                        await ctx.send(f'I failed in adding the reaction ("{emoji}"):grimacing:')
                    except Exception as e:
                        await ctx.send(f'There\'s been a problem while adding the reaction "{emoji}" that\'s not of type '
                                       f'"Forbidden", "NotFound", "InvalidArgument" or "HTTPException", but `{type(e)}: {e}`.')
                    else:
                        if emoji not in successes:
                            successes.append(emoji)
                if len(successes) >= 1:
                    await ctx.send(f'Successfully reacted in server "{channel.guild.name}" in channel "{channel.mention}"'
                                   f' to message "{message.content}" by {message.author.name}'
                                   f' with emoji{"s" if len(successes) > 1 else ""} {successes}.')

    @commands.command(hidden=True)
    async def delete(self, ctx: commands.Context, message_link, delay: Optional[float]):
        """Delete a message."""
        IDs = message_link.split('/')[-2:]
        channel = await get_channel_by_id(self.bot, ctx, int(IDs[0]))
        if channel:
            message = await get_message_by_id(channel, ctx, int(IDs[1]))
            if message:
                try:
                    await message.delete(delay=delay)
                except discord.Forbidden:
                    await ctx.send('I don\'t have permission to delete this message:grimacing:')
                except discord.NotFound:
                    await ctx.send('This message was already deleted.')
                except discord.HTTPException:
                    await ctx.send('I failed in deleting the message:grimacing:')
                except Exception as e:
                    await ctx.send(f'There\'s been a problem while deleting the message that\'s not of type "Forbidden",'
                                   f' "NotFound" or "HTTPException", but `{type(e)}: {e}`.')
                else:
                    await ctx.send(f'Message "{message.content}" by {message.author.name} deleted in server'
                                   f' "{channel.guild.name}" in channel "{channel.mention}".')

    @commands.command
    async def pin(self, ctx: commands.Context, message_link, reason: Optional[str]):
        """Pin a message."""
        IDs = message_link.split('/')[-2:]
        channel = await get_channel_by_id(self.bot, ctx, int(IDs[0]))
        if channel:
            message = await get_message_by_id(channel, ctx, int(IDs[1]))
            if message:
                try:
                    await message.pin(reason=reason)
                except discord.Forbidden:
                    await ctx.send('I don\'t have permission to pin this message:grimacing:')
                except discord.NotFound:
                    await ctx.send('I couldn\'t find the message.')
                except discord.HTTPException:
                    await ctx.send('I failed in pinning the message:grimacing:')
                except Exception as e:
                    await ctx.send(f'There\'s been a problem while pinning the message that\'s not of type "Forbidden",'
                                   f' "NotFound" or "HTTPException", but `{type(e)}: {e}`.')
                else:
                    await ctx.send(f'Message "{message.content}" by {message.author.name} pinned in server'
                                   f' "{channel.guild.name}" in channel "{channel.mention}".')

    @commands.command
    async def unpin(self, ctx: commands.Context, message_link, reason: Optional[str]):
        """Unpin a message."""
        IDs = message_link.split('/')[-2:]
        channel = await get_channel_by_id(self.bot, ctx, int(IDs[0]))
        if channel:
            message = await get_message_by_id(channel, ctx, int(IDs[1]))
            if message:
                try:
                    await message.unpin(reason=reason)
                except discord.Forbidden:
                    await ctx.send('I don\'t have permission to unpin this message:grimacing:')
                except discord.NotFound:
                    await ctx.send('I couldn\'t find the message.')
                except discord.HTTPException:
                    await ctx.send('I failed in unpinning the message:grimacing:')
                except Exception as e:
                    await ctx.send(f'There\'s been a problem while unpinning the message that\'s not of type "Forbidden",'
                                   f' "NotFound" or "HTTPException", but `{type(e)}: {e}`.')
                else:
                    await ctx.send(f'Message "{message.content}" by {message.author.name} unpinned in server'
                                   f' "{channel.guild.name}" in channel "{channel.mention}".')


def setup(bot: commands.Bot):
    bot.add_cog(Template(bot))
