import discord
from discord.ext import commands
from bot import Curator
from typing import Optional, Union
from .utils.converter import *


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


class Control(commands.Cog):  # TODO add more exception catching, check prompts and confirmations
    """Commands that can be used to take control over the bot's actions."""

    def __init__(self, bot: Curator):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        return ctx.author.id in self.bot.admins

    @commands.command(aliases=['sayhere'], hidden=True)
    async def echo(self, ctx: commands.Context, *, message):  # TODO: implement delete_after?
        """Let the bot delete and resend your message."""
        await ctx.message.delete()
        await ctx.send(message)

    @commands.command(hidden=True)
    async def dm(self, ctx: commands.Context, user: discord.User, *, message):  # TODO: implement delete_after?
        """Send a DM to a user."""
        try:
            await user.send(message)
        except discord.Forbidden:
            await ctx.send('I don\'t have permission to send this message:grimacing:')
        except discord.HTTPException:
            await ctx.send('I failed in sending the message:grimacing:')
        except Exception as e:
            await ctx.send(f'There\'s been a problem while sending the message that\'s not of type "Forbidden" or'
                           f' "HTTPException", but `{type(e)}: {e}`.')
        else:
            await ctx.send(f'Message sent to {user.name}')

    @commands.command(aliases=['replydm'], hidden=True)
    async def dmreply(self, ctx: commands.Context, *, message):
        """Send a DM to the user I last received a DM from."""
        if self.bot.last_dm:
            await ctx.invoke(self.dm, self.bot.last_dm, message=message)
        else:
            await ctx.send(f'There is no last user stored, try `{ctx.prefix}dm <user> <message>`.')

    @commands.command(aliases=['say'], hidden=True)
    async def send(self, ctx: commands.Context, channel: GlobalTextChannel, *, message):  # TODO: implement delete_after?
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

    @commands.group(hidden=True, invoke_without_command=True)
    async def reply(self, ctx: commands.Context, message_link, *, message, mention=False):  # TODO: implement delete_after?
        """"Send a message using the reply feature on a message.

        Use "reply mention" instead to mention the author.
        """
        IDs = message_link.split('/')[-2:]
        channel = await get_channel_by_id(self.bot, ctx, int(IDs[0]))
        if channel:
            reference = await get_message_by_id(channel, ctx, int(IDs[1]))
            if reference:
                try:
                    await reference.reply(message, mention_author=mention)
                except discord.Forbidden:
                    await ctx.send('I don\'t have permission to send this message:grimacing:')
                except discord.InvalidArgument:
                    await ctx.send('Something went wrong with the message to reply to.')  # "The files list is not of the appropriate size, you specified both file and files, or the reference object is not a Message or MessageReference."
                except discord.HTTPException:
                    await ctx.send('I failed in sending the message:grimacing:')
                except Exception as e:
                    await ctx.send(
                        f'There\'s been a problem that\'s not of type "Forbidden" or "HTTPException", but `{type(e)}: {e}`.')
                else:
                    await ctx.send(f'Message sent in server "{channel.guild.name}" in channel "{channel.mention}":'
                                   f' {channel.last_message.jump_url}.')

    @reply.command(hidden=True, name='mention', aliases=['ping'])
    async def reply_mention(self, ctx: commands.Context, message_link, *, message):  # TODO: implement delete_after?
        """Send a message using the reply feature with a ping."""
        await ctx.invoke(self.reply, message_link, message=message, mention=True)

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

    @commands.group(invoke_without_command=True, hidden=True)
    async def delete(self, ctx: commands.Context, message: discord.Message, delay: Optional[float]):
        """Delete a message."""
        #IDs = message_link.split('/')[-2:]
        #channel = await get_channel_by_id(self.bot, ctx, int(IDs[0]))
        #if channel:
        #    message = await get_message_by_id(channel, ctx, int(IDs[1]))
        #    if message:
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
                           f' "{message.guild.name}" in channel "{message.channel.mention}".')

    @delete.command(name='discrete', aliases=['discretely', 'selfdestruct', 'selfdelete', 'noevidence', 'secretly'])
    async def delete_discrete(self, ctx: commands.Context, message: discord.Message, delay: Optional[float]):
        try:
            await message.delete(delay=delay)
        except discord.Forbidden:
            await ctx.author.send('I don\'t have permission to delete this message:grimacing:')
        except discord.NotFound:
            await ctx.author.send('This message was already deleted.')
        except discord.HTTPException:
            await ctx.author.send('I failed in deleting the message:grimacing:')
        except Exception as e:
            await ctx.author.send(f'There\'s been a problem while deleting the message that\'s not of type "Forbidden",'
                                  f' "NotFound" or "HTTPException", but `{type(e)}: {e}`.')
        else:
            await ctx.author.send(f'Message "{message.content}" by {message.author.name} deleted in server'
                                  f' "{message.guild.name}" in channel "{message.channel.mention}".')

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.author.send('I don\'t have permission to delete your command:grimacing:')
        except discord.NotFound:
            await ctx.author.send('Your command message was already deleted.')
        except discord.HTTPException:
            await ctx.author.send('I failed in deleting your command:grimacing:')
        except Exception as e:
            await ctx.author.send(f'There\'s been a problem while deleting your command that\'s not of type "Forbidden"'
                                  f', "NotFound" or "HTTPException", but `{type(e)}: {e}`.')
        else:
            await ctx.author.send(f'Successfully deleted your command "{ctx.message.content}" in server'
                                  f' "{ctx.guild.name}" in channel "{ctx.channel.mention}".')

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
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

    @commands.command(aliases=['addroles'], hidden=True)
    async def giveroles(self, ctx: commands.Context, guild: Optional[GuildChanger], member: discord.Member, *roles: discord.Role):  # TODO catch exceptions
        """Give roles to a user on a server.

        Cannot use a user_id for the member argument due to the lack of a converter for discord.Guild.
        """
        ctx.guild = ctx.message.guild
        guild = guild or ctx.guild
        await member.add_roles(*roles)  # Can raise discord.Forbidden and discord.HTTPException

    @commands.command(aliases=['removeroles'], hidden=True)
    async def takeroles(self, ctx: commands.Context, guild: Optional[GuildChanger], member: discord.Member, *roles: discord.Role):  # TODO catch exceptions
        """Remove roles from a user on a server.

        Cannot use a user_id for the member argument due to the lack of a converter for discord.Guild.
        """
        ctx.guild = ctx.message.guild
        guild = guild or ctx.guild
        await member.remove_roles(*roles)  # Can raise discord.Forbidden and discord.HTTPException

    @commands.group(hidden=True, invoke_without_command=True)
    async def channel(self, ctx: commands.Context):
        await ctx.send('You need to supply a subcommand.')

    @channel.group(name='create', aliases=['make', 'instantiate'], hidden=True, invoke_without_command=True)
    #async def create_channel(self, ctx: commands.Context, where: Optional[Union[GuildConverter, GlobalCategoryChannel]], name, position: Optional[int]):  # Discord is very weird with channel positioning
    async def create_channel(self, ctx: commands.Context, where: Optional[Union[GuildConverter, GlobalCategoryChannel]], name, *, description: Optional[str]):
        """Create a text channel.

        Discord is very weird with channel positioning, the position parameter might not work how you would expect it to.
        """
        #await create_the_channel(ctx, where, name, position)
        await create_the_channel(ctx, where, name, description=description)

    @create_channel.command(name='private', aliases=['hidden', 'secret'], hidden=True)
    #async def create_private_channel(self, ctx: commands.Context, where: Optional[Union[GuildChanger, GlobalCChannelGChanger]], name, position: Optional[int], roles_and_members: Union[discord.Role, discord.Member]):
    async def create_private_channel(self, ctx: commands.Context, where: Optional[Union[GuildChanger, GlobalCChannelGChanger]], name, roles_and_members: commands.Greedy[Union[discord.Role, discord.Member]], *, description: Optional[str]):
        """Create a private text channel.

        Discord is very weird with channel positioning, the position parameter might not work how you would expect it to.
        """
        ctx.guild = ctx.message.guild
        await create_the_channel(ctx, where, name, description=description, roles_and_members=roles_and_members)

    @channel.group(name='edit', aliases=['change'], invoke_without_command=True, hidden=True)
    async def edit_channel(self, ctx: commands.Context):
        """Commands for editing a channel."""
        await ctx.send('You need to supply a subcommand.')  # TODO add said subcommands

    @commands.group(invoke_without_command=True, hidden=True)
    async def role(self, ctx: commands.Context):
        """Commands to do with roles."""
        await ctx.send('Supply a subcommand, please.')

    @role.command(name='create', aliases=['make', 'new'], hidden=True)
    async def create_role(self, ctx: commands.Context, guild: Optional[GuildChanger], name, colour: Optional[discord.Colour], position: Optional[int], show_separate: Optional[bool]):
        """Create a role.

        Use role edit for further settings, the new role will start with no permissions and it will not be mentionable.
        show_separate defaults to False.
        """
        ctx.guild = ctx.channel.guild
        guild = guild or ctx.guild
        colour = colour or discord.Colour.default()  # Makes sure no colour defaults to default
        show_separate = True if show_separate else False  # Makes sure None is also False
        role: discord.Role = await guild.create_role(name=name, colour=colour, hoist=show_separate)
        if position:
            await role.edit(position=position)

    @role.command(name='give', aliases=['giveto', 'donate', 'distribute'], hidden=True)
    async def give_role(self, ctx: commands.Context, guild: Optional[GuildChanger], role: discord.Role, *members: discord.Member):
        ctx.guild = ctx.channel.guild
        for member in members:
            await member.add_roles(role)

    @role.group(name='edit', aliases=['change'], invoke_without_command=True, hidden=True)
    async def edit_role(self, ctx: commands.Context):
        """Commands for editing roles."""
        await ctx.send('Please supply a subcommand.')

    @edit_role.command(name='name', hidden=True)
    async def edit_role_name(self, ctx: commands.Context, guild: Optional[GuildChanger], role: discord.role, name):
        """Edit the name of a role."""
        await role.edit(name=name)

    @edit_role.command(name='position', hidden=True)
    async def edit_role_position(self, ctx: commands.Context, guild: Optional[GuildChanger], role: discord.Role, position: int):
        """Reposition a role in the hierarchy."""
        await role.edit(position=position)

    @edit_role.command(name='hoist', hidden=True)
    async def edit_role_hoist(self, ctx: commands.Context, guild: Optional[GuildChanger], role: discord.Role, show_separate: Optional[bool]):
        """Choose if this role should be displayed separately in the member list.

        It will toggle if you don't supply a boolean.
        """
        await role.edit(hoist=show_separate if show_separate is not None else False if role.hoist else True)

    @edit_role.command(name='colour', aliases=['color'], hidden=True)
    async def edit_role_colour(self, ctx: commands.Context, guild: Optional[GuildChanger], role: discord.Role, colour: Optional[discord.Colour]):
        """Edit the colour of a role.

        If no colour is provided I will change it to the default colour.
        """
        await role.edit(colour=colour if colour else discord.Colour.default())

    @edit_role.command(name='mentionable', hidden=True)
    async def edit_role_mentionable(self, ctx: commands.Context, guild: Optional[GuildChanger], role: discord.Role, mentionable: Optional[bool]):
        """Choose if this role should be mentionable by everyone.

        It will toggle if you don't supply a boolean.
        """
        await role.edit(mentionable=mentionable if mentionable is not None else False if role.mentionable else True)

    @role.command(name='delete', aliases=['remove'], hidden=True)
    async def delete_role(self, ctx: commands.Context, guild: Optional[GuildChanger], role: discord.Role):
        """Delete a DIscord role."""
        await role.delete()


#async def create_the_channel(ctx: commands.Context, where: Optional[Union[discord.Guild, discord.CategoryChannel]], name, position: Optional[int], roles_and_members=None):
async def create_the_channel(ctx: commands.Context, where: Optional[Union[discord.Guild, discord.CategoryChannel]], name, description=None, roles_and_members=None):
    where = where or ctx.guild
    guild = where if type(where) == discord.Guild else where.guild
    overwrites = None
    if roles_and_members:
        overwrites = {who: discord.PermissionOverwrite(read_messages=True) for who in roles_and_members}
        overwrites[guild.default_role] = discord.PermissionOverwrite(read_messages=False)

    #channel = await where.create_text_channel(name, overwrites=overwrites, position=position)
    channel = await where.create_text_channel(name, topic=description, overwrites=overwrites)
    await ctx.send(f'Channel **{channel.name}** created with ID _{channel.id}_ in {f"category **{channel.category}** with ID _{channel.category_id}_" if channel.category else "no category"} in guild **{channel.guild}** with ID _{channel.guild.id}_: {channel.mention} with {f"topic `{channel.topic}`" if channel.topic else "no topic"}.')


def setup(bot: Curator):
    bot.add_cog(Control(bot))
