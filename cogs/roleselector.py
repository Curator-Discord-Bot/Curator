from __future__ import annotations

import discord
from discord.ext import commands
from bot import Curator
import asyncpg
from typing import Optional, List, Union
import asyncio
import emoji as amoji
from datetime import datetime

from .utils import db
from .utils import selecting
from.utils.formats import human_date, human_join

from .utils.checks import is_bot_admin, owner_or_guild_permissions


class Rolemenus(db.Table):
    guild = db.Column(db.Integer(big=True))  # Server the menu is in (ID)
    message = db.Column(db.Array(sql_type=db.Integer(big=True)), primary_key=True)  # ID of the channel and of the message
    description = db.Column(db.String, default='')  # Description at the top of the menu message
    roles = db.Column(db.Array(sql_type=db.Integer(big=True)), default='{}')  # The roles to choose from (list of IDs)
    emojis = db.Column(db.Array(sql_type=db.String), default='{}')  # The emojis to react with (list of IDs or unicode emojis in string format)
    role_descs = db.Column(db.Array(sql_type=db.String), default='{}')  # Short descriptions of all the roles to choose from
    allow_multiple = db.Column(db.Boolean, default=True)  # Specifies if you can select multiple roles from the list (true/false)
    created_by = db.Column(db.Integer(big=True))  # User who created the menu (ID)
    created_at = db.Column(db.Datetime, default="now() at time zone 'utc'")  # The moment the menu was created
    last_edited_by = db.Column(db.Integer(big=True))  # User who last edited the menu (ID)
    last_edited_at = db.Column(db.Datetime)  # The last moment the menu was edited
    enabled = db.Column(db.Boolean, default=True)  # Specifies if the menu is enabled/disabled on purpose


menus = {}


def make_message(description, roles, emojis, role_descs, status=True) -> str:
    status_text = '***This menu is currently out of service***\n\n' if not status else ''
    message = status_text + description
    for i in range(len(roles)):
        message += f'\n\n{emojis[i]}: **{roles[i].name}**'
        if role_descs[i]:
            message += f'\n{role_descs[i]}'
    return message


async def get_menu_from_link(ctx, url) -> Optional[SelectionMenu]:
    IDs = url.split('/')[-3:]
    IDs[0] = int(IDs[0])
    if IDs[0] not in menus.keys() or (int(IDs[0]) != ctx.guild.id and ctx.author.id not in ctx.bot.admins):
        await ctx.send('Please provide a valid message URL of a menu on this server.')
        return None
    if IDs[1]+','+IDs[2] not in menus[IDs[0]].keys():
        await ctx.send('Please provide a valid message URL of a menu on this server.')
        return None
    return menus[IDs[0]][str(IDs[1])+','+str(IDs[2])]


class SelectionMenu:
    def __init__(self, message, description, roles, emojis, role_descs, allow_multiple, created_by, created_at, last_edited_by=None, last_edited_at=None, status=True, issues=None):
        self.message: discord.Message = message
        self.description: str = description
        self.roles: List[discord.Role] = roles
        self.emojis: List[Union[discord.Emoji, discord.PartialEmoji, str]] = emojis
        self.role_descs: List[str] = role_descs  # description text per role
        self.allow_multiple: bool = allow_multiple
        self.created_by: discord.User = created_by
        self.created_at: datetime = created_at
        self.last_edited_by: Optional[discord.User] = last_edited_by
        self.last_edited_at: Optional[datetime] = last_edited_at
        self.status: bool = status
        self.issues: Optional[List[List[str, int]]] = issues
        self.ignore_next = False  # Used to ignore a reaction being deleted when it is the bot that deletes it

    async def reaction_received(self, emoji: Union[discord.Emoji, discord.PartialEmoji, str], member: discord.Member):
        if emoji not in self.emojis:
            self.ignore_next = True
            await self.message.remove_reaction(emoji, member)
            return

        if not self.status:
            self.ignore_next = True
            await self.message.remove_reaction(emoji, member)
            return await member.send(f'**{self.message.guild}:** the menu you tried to use is currently out of service, sorry for the inconvenience.')

        role = self.roles[self.emojis.index(emoji)]
        if role in member.roles:
            return await member.send(f'**{self.message.guild}:** you already have the **{role}** role.')
        if not self.allow_multiple:
            for r in self.roles:
                if r in member.roles:
                    self.ignore_next = True
                    await self.message.remove_reaction(emoji, member)
                    return await member.send(f'**{self.message.guild}:** you already have a role from this'
                                                        f' menu, you must first remove **{r}** if you want **{role}**.')

        try:
            await member.add_roles(role, reason=f'Selected role ({self.message.jump_url})')
            await member.send(f'**{self.message.guild}:** gave you the **{role}** role.')
        except discord.Forbidden:
            self.ignore_next = True
            await self.message.remove_reaction(emoji, member)
            guild_owner = self.message.guild.owner
            await guild_owner.send(f'**{self.message.guild}:** I do not have the required permissions to give'
                                              f' **{member}** the **{role}** role on your server. I need "Manage Roles"'
                                              f' permissions and my highest role needs to be higher than the roles you'
                                              f' want me to add/remove.')
            await member.send(f'**{self.message.guild}:** I don\'t have permission to give you the **{role}**'
                                         f' role. I have contacted the server owner about this.')

    async def reaction_removed(self, emoji: Union[discord.Emoji, discord.PartialEmoji, str], member: discord.Member):
        if self.ignore_next:
            self.ignore_next = False
            return

        if not self.status:
            await self.message.remove_reaction(emoji, member)
            return await member.send(f'**{self.message.guild}:** the menu you tried to use is currently out of service, sorry for the inconvenience.')

        role = self.roles[self.emojis.index(emoji)]
        if role not in member.roles:
            return await member.send(f'**{self.message.guild}:** you do not have the **{role}** role so I couldn\'t remove it.')

        try:
            await member.remove_roles(role, reason=f'Removed role ({self.message.jump_url})')
            await member.send(f'**{self.message.guild}:** removed the **{role}** role.')
        except discord.Forbidden:
            guild_owner = self.message.guild.owner
            await guild_owner.send(f'**{self.message.guild}:** I do not have the required permissions to'
                                              f' remove the **{role}** role from **{member}** on your server. I need'
                                              f' "Manage Roles" permissions and my highest role needs to be higher than'
                                              f' the roles you want me to add/remove.')
            await member.send(f'**{self.message.guild}:** I don\'t have permission to remove the **{role}**'
                                         f' role from you. I have contacted the server owner about this.')


class RoleSelector(commands.Cog):
    def __init__(self, bot: Curator):
        self.bot = bot
        self._task = bot.loop.create_task(self.get_menus())

    @commands.group(name='roleselector', aliases=['rselector', 'rolesel', 'rsel', 'rs', 'rolemenu', 'rmenu'])
    async def role_selector(self, ctx: commands.Context):
        """All commands revolving around the role selection menus."""
        if ctx.guild.id not in menus.keys():
            menus[ctx.guild.id] = {}

        if not ctx.invoked_subcommand:
            await ctx.send(f'Use `{ctx.prefix}help roleselector` for the possible commands.')

    @role_selector.group(name='make', aliases=['create', 'new'], invoke_without_command=True)
    @owner_or_guild_permissions(manage_roles=True)
    async def make_rsel(self, ctx: commands.Context, channel: discord.TextChannel,
                        *roles_and_emojis: Union[discord.Role, discord.Emoji, discord.PartialEmoji, str], allow_multiple=True):
        """Create a role selection menu!

        Provide the channel for the menu.
        More instructions coming soon.

        Use "roleselector make unique" instead to restrict members to choosing only one role from the list.
        """
        if len(roles_and_emojis) % 2 == 1:
            return await ctx.send(f'Provide a valid list of arguments (`{ctx.prefix}help roleselector make` for info on'
                                  f' how to use this command)')

        roles = []
        emojis = []
        i = 0
        for item in roles_and_emojis:
            if i % 2 == 0:  # Item should be a role
                if type(item) == discord.Role:
                    if item in roles:
                        return await ctx.send('You have put in the same role more than once.')
                    elif item >= ctx.author.top_role:
                        return await ctx.send(f'**{item}** is (higher than) your highest role so you cannot make it available.')
                    else:
                        roles.append(item)
                else:
                    return await ctx.send(f'`{item}` is invalid.')
            else:  # Item should be an emoji   TODO custom emoji must be from the ctx.guild
                if type(item) == discord.Emoji or type(item) == discord.PartialEmoji or item in amoji.unicode_codes.EMOJI_UNICODE_ENGLISH.values():
                    #if item not in ctx.guild.
                    if item in emojis:
                        return await ctx.send('You can only use an emoji once.')
                    else:
                        emojis.append(item)
                else:
                    return await ctx.send(f'`{item}` is invalid.')
            i += 1

        def check1(message1):
            return message1.author == ctx.author and message1.channel == ctx.channel

        await ctx.send('Give the description of the selection menu (times out in 5 minutes).')
        try:
            description = await self.bot.wait_for('message', check=check1, timeout=300)
        except asyncio.TimeoutError:
            return await ctx.send('Timed out')
        description = description.content

        """def check2(reaction2, user2):
            return user2 == ctx.author and reaction2.message == msg2 and (reaction2.emoji == '✅' or reaction2.emoji == '❌')

        msg2 = await ctx.send('Are people allowed to select multiple roles from the list? '
                              'React with :white_check_mark: or :x: (times out in 1 minute).')
        await msg2.add_reaction('✅')
        await msg2.add_reaction('❌')
        try:
            r2, u2 = await self.bot.wait_for('reaction_add', check=check2, timeout=60)
        except asyncio.TimeoutError:
            return await ctx.send('Timed out')
        allow_multiple = True if r2.emoji == '✅' else False"""  # Obsoleted due to using a sub-command

        def check3_reply(message3):
            if message3.author == ctx.author and message3.channel == ctx.channel:
                nonlocal event
                event = 'message'
                return True
            else:
                return False

        def check3_react(reaction3, user3):
            if reaction3.message == msg3 and user3 == ctx.author and reaction3.emoji == '❌':
                nonlocal event
                event = 'reaction'
                return True
            else:
                return False

        role_descs = []
        for role in roles:
            event = None
            msg3 = await ctx.send(f'Give a (short) description for the **{role.name}** role. '
                                  f'React to this message with :x: if you do not wish to add a description. '
                                  f'Times out in 2 minutes.')
            await msg3.add_reaction('❌')
            pending_tasks = [self.bot.wait_for('message', check=check3_reply),
                             self.bot.wait_for('reaction_add', check=check3_react)]
            done_tasks, pending_tasks = await asyncio.wait(pending_tasks, timeout=120, return_when=asyncio.FIRST_COMPLETED)
            for task in pending_tasks:  # The event(s) that didn't trigger (both in case of a timeout)
                task.cancel()
            if not event:  # timeout on asyncio.wait() does not raise an error, it returns all unfinished tasks in the pending_tasks set
                return await ctx.send('Timed out.')
            for task in done_tasks:  # The thing that happened, can only be one. In an iterable because done_tasks is a set
                if event == 'message':  # User replied with a description
                    role_description = await task
                    role_descs.append(role_description.content)
                else:  # User reacted with ❌
                    role_descs.append(None)

        menu_message = await channel.send(make_message(description, roles, emojis, role_descs))
        for emoji in emojis:
            await menu_message.add_reaction(emoji)
        created_at = datetime.utcnow()

        query = 'INSERT INTO rolemenus VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NULL, NULL, True);'
        await self.bot.pool.fetchval(query, ctx.guild.id, [channel.id, menu_message.id], description, [role.id for role in roles],
                                     [str(emoji.id) if type(emoji) != str else emoji for emoji in emojis], role_descs,
                                     allow_multiple, ctx.author.id, created_at)

        await ctx.send(f'Here it is: {menu_message.jump_url}')
        menus[channel.guild.id][str(channel.id)+','+str(menu_message.id)] = SelectionMenu(menu_message, description, roles,
                                                                                          emojis, role_descs, allow_multiple,
                                                                                          ctx.author, created_at)

    @make_rsel.command(name='unique', aliases=['singular', 'limited'])
    @owner_or_guild_permissions(manage_roles=True)
    async def make_rsel_unique(self, ctx: commands.Context, channel: discord.TextChannel,
                               *roles_and_emojis: Union[discord.Role, discord.Emoji, discord.PartialEmoji, str]):
        """Create a role selection menu from which only one role can be selected."""
        await ctx.invoke(self.make_rsel, channel, *roles_and_emojis, allow_multiple=False)

    @role_selector.command()
    @owner_or_guild_permissions(manage_roles=True)
    async def enable(self, ctx: commands.Context, menu_url):
        """Enable the role menu."""
        menu = await get_menu_from_link(ctx, menu_url)
        if not menu:
            return

        if menu.status:
            return await ctx.send('This menu is already enabled:thinking:')

        if menu.issues:
            issue_list = '\n'.join([f'Couldn\'t find **{issue[0]}** with ID **{issue[1]}**' for issue in menu.issues])
            return await ctx.send(f'You cannot do this because the menu is broken.\n_{issue_list}_\nUse `changeemoji` and/or `removerole` to fix this.')

        menu.status = True
        query = 'UPDATE rolemenus SET enabled = True WHERE message = $1;'
        await self.bot.pool.fetchval(query, [menu.message.channel.id, menu.message.id])
        await menu.message.edit(content=menu.message.content.split('\n', 2)[2:][0])
        await ctx.send('Successfully enabled.')

    @role_selector.command()
    @owner_or_guild_permissions(manage_roles=True)
    async def disable(self, ctx: commands.Context, menu_url):
        """Disable the role menu."""
        menu = await get_menu_from_link(ctx, menu_url)
        if not menu:
            return

        if not menu.status:
            return await ctx.send('This menu is already inactive:thinking:')

        menu.status = False
        query = 'UPDATE rolemenus SET enabled = False WHERE message = $1;'
        await self.bot.pool.fetchval(query, [menu.message.channel.id, menu.message.id])
        await menu.message.edit(content='***This menu is currently out of service***\n\n'+menu.message.content)
        await ctx.send('Successfully disabled.')

    @role_selector.command()
    @owner_or_guild_permissions(manage_roles=True)
    async def addrole(self, ctx: commands.Context, menu_url, role: discord.Role, emoji: Union[discord.Emoji, discord.PartialEmoji, str], *, description: Optional[str]):
        """Add a role to the menu."""
        menu = await get_menu_from_link(ctx, menu_url)
        if not menu:
            return

        if role in menu.roles:
            return await ctx.send('This role is already in this menu:thinking:')

        if role >= ctx.author.top_role:
            return await ctx.send('This role is (higher than) your highest role so you cannot make it available.')

        if type(emoji) == str and emoji not in amoji.unicode_codes.EMOJI_UNICODE_ENGLISH.values():
            return await ctx.send('Please give me a valid emoji.')

        menu.roles.append(role)
        menu.emojis.append(emoji)
        menu.role_descs.append(description)
        query = 'UPDATE rolemenus SET roles = array_append(roles, $1), emojis = array_append(emojis, $2), role_descs = array_append(role_descs, $3) WHERE message = $4;'
        await self.bot.pool.fetchval(query, role.id, str(emoji) if type(emoji) != str else emoji, description, [menu.message.channel.id, menu.message.id])
        await menu.message.edit(content=menu.message.content+f'\n\n{emoji}: **{role.name}**'+(f'\n{description}' if description else ''))
        await menu.message.add_reaction(emoji)
        await self.update_last_edit(menu, ctx.author)
        await ctx.send(f'Successfully added **{role}**.')

    @role_selector.command()
    @owner_or_guild_permissions(manage_roles=True)
    async def removerole(self, ctx: commands.Context, menu_url, role: Union[discord.Role, int]):
        """Remove a role from the menu."""
        menu = await get_menu_from_link(ctx, menu_url)
        if not menu:
            return

        if type(role) == int:
            if role - 1 not in list(range(len(menu.roles))):
                return await ctx.send(f'Provide a role or one of these numbers: {human_join([str(n) for n in range(len(menu.roles))])}.')
            role = menu.roles[role - 1]

        if role >= ctx.author.top_role:
            return await ctx.send('That role is (higher than) your highest role so you cannot remove it from the menu.')

        if role not in menu.roles:
            return await ctx.send('That role is already not in this menu:thinking:')

        index = menu.roles.index(role)
        menu.roles.pop(index)
        emoji = menu.emojis.pop(index)
        role_desc = menu.role_descs.pop(index)
        query = 'UPDATE rolemenus SET roles = array_remove(roles, $1), emojis = array_remove(emojis, $2), role_descs = array_remove(role_descs, $3) WHERE message = $4;'
        await self.bot.pool.fetchval(query, role.id, str(emoji.id) if type(emoji) != str else emoji, role_desc, [menu.message.channel.id, menu.message.id])
        await menu.message.edit(content=make_message(menu.description, menu.roles, menu.emojis, menu.role_descs, status=menu.status))
        await menu.message.clear_reaction(emoji)
        await self.update_last_edit(menu, ctx.author)
        await ctx.send(f'Successfully removed **{role}**.')

    @role_selector.command(aliases=['changemoji', 'editemoji', 'newemoji'])
    @owner_or_guild_permissions(manage_roles=True)
    async def changeemoji(self, ctx: commands.Context, menu_url, role: discord.Role, emoji: Union[discord.Emoji, discord.PartialEmoji, str]):
        """Change the emoji for a role.

        Requires permission to manage messages in the channel of the menu
        """
        menu = await get_menu_from_link(ctx, menu_url)
        if not menu:
            return

        if role not in menu.roles:
            return await ctx.send('No such role exists in the menu you provided.')

        if emoji == menu.emojis[menu.roles.index(role)]:
            return await ctx.send('That role is already using that emoji:thinking:')
        if emoji in menu.emojis:
            return await ctx.send('This emoji is already used in this menu. You can only use an emoji once.')

        if type(emoji) == str and emoji not in amoji.unicode_codes.EMOJI_UNICODE_ENGLISH.values():
            return await ctx.send(f'Please give me a valid emoji.')

        old_emoji = menu.emojis[menu.roles.index(role)]
        menu.emojis[menu.roles.index(role)] = emoji
        query = 'UPDATE rolemenus SET emojis = array_replace(emojis, $1, $2) WHERE message = $3;'
        await self.bot.pool.fetchval(query, str(old_emoji.id) if type(old_emoji) != str else old_emoji, str(emoji.id) if type(emoji) != str else emoji, [menu.message.channel.id, menu.message.id])
        await menu.message.edit(content=make_message(menu.description, menu.roles, menu.emojis, menu.role_descs, status=menu.status))
        await menu.message.clear_reactions()
        for e in menu.emojis:
            await menu.message.add_reaction(e)
        await self.update_last_edit(menu, ctx.author)
        await ctx.send('Successfully changed the emoji.')

    @role_selector.command(aliases=['changeroledescription', 'changerdesc', 'editroledesc', 'roledescription', 'roledesc'])
    @owner_or_guild_permissions(manage_roles=True)
    async def changeroledesc(self, ctx: commands.Context, menu_url, role: discord.Role, *, description: Optional[str]):
        menu = await get_menu_from_link(ctx, menu_url)
        if not menu:
            return

        if role not in menu.roles:
            return await ctx.send('This role is not in this menu.')

        if description == menu.role_descs[menu.roles.index(role)]:
            return await ctx.send('This is already the description for this role:thinking:')

        menu.role_descs[menu.roles.index(role)] = description
        query = 'UPDATE rolemenus SET role_descs = $1 WHERE message = $2;'  # This query is not using the PostgreSQL array_replace() function because role descriptions do not have to be unique
        await self.bot.pool.fetchval(query, menu.role_descs, [menu.message.channel.id, menu.message.id])
        await menu.message.edit(content=make_message(menu.description, menu.roles, menu.emojis, menu.role_descs, status=menu.status))
        await self.update_last_edit(menu, ctx.author)
        await ctx.send(f'Successfully {"changed" if description else "removed"} role description.')

    @role_selector.command(aliases=['description'])
    @owner_or_guild_permissions(manage_roles=True)
    async def changedescription(self, ctx: commands.Context, menu_url, *, description):
        menu = await get_menu_from_link(ctx, menu_url)
        if not menu:
            return

        if description == menu.description:
            return await ctx.send('But that is already the description:thinking:')

        menu.description = description
        query = 'UPDATE rolemenus SET description = $1 WHERE message = $2;'
        await self.bot.pool.fetchval(query, description, [menu.message.channel.id, menu.message.id])
        await menu.message.edit(content=make_message(description, menu.roles, menu.emojis, menu.role_descs, status=menu.status))
        await self.update_last_edit(menu, ctx.author)
        await ctx.send('Successfully changed description.')

    @role_selector.command(aliases=['order'])
    @owner_or_guild_permissions(manage_roles=True)
    async def reorder(self, ctx: commands.Context, menu_url, *order: int):
        """Re-order the items in the list.

        Example for order argument: 1 4 3 2 (swap the second and fourth role in the list)
        """
        menu = await get_menu_from_link(ctx, menu_url)
        if not menu:
            return

        sorted_order = list(order).copy()
        sorted_order.sort()
        if list(range(1, len(menu.roles) + 1)) != sorted_order:
            return await ctx.send(f'Please provide the numbers {human_join([str(n) for n in range(1, len(menu.roles) + 1)], final="and")}, each once.')

        menu.roles = [menu.roles[index - 1] for index in order]
        menu.emojis = [menu.emojis[index - 1] for index in order]
        menu.role_descs = [menu.role_descs[index - 1] for index in order]
        query = 'UPDATE rolemenus SET roles = $1, emojis = $2, role_descs = $3 WHERE message = $4;'
        await self.bot.pool.fetchval(query, [role.id for role in menu.roles], [str(emoji.id) if type(emoji) != str else emoji for emoji in menu.emojis], menu.role_descs, [menu.message.channel.id, menu.message.id])
        await menu.message.edit(content=make_message(menu.description, menu.roles, menu.emojis, menu.role_descs, status=menu.status))
        await menu.message.clear_reactions()
        for emoji in menu.emojis:
            await menu.message.add_reaction(emoji)
        await self.update_last_edit(menu, ctx.author)
        await ctx.send('Successfully re-ordered.')

    @role_selector.command(aliases=['transport'])
    @owner_or_guild_permissions(manage_channels=True)
    async def move(self, ctx: commands.Context, menu_url, channel: discord.TextChannel):
        """Move a selection menu to another channel.

        Provide the URL of the message that contains the menu.
        """
        menu = await get_menu_from_link(ctx, menu_url)
        if not menu:
            return

        if channel == menu.message.channel:
            return await ctx.send('The menu is already in that channel:thinking:')

        if channel.guild != menu.message.guild:
            return await ctx.send('You have to move it to a channel in the same server.')

        new_message = await channel.send(menu.message.content)
        for emoji in menu.emojis:
            await new_message.add_reaction(emoji)
        query = 'UPDATE rolemenus SET message = $1 WHERE message = $2;'
        await self.bot.pool.fetchval(query, [channel.id, new_message.id], [menu.message.channel.id, menu.message.id])
        menus[channel.guild.id][str(channel.id)+','+str(new_message.id)] = menus[menu.message.guild.id].pop(str(menu.message.channel.id)+','+str(menu.message.id))
        await menu.message.delete()
        for emoji in menu.emojis:
            await new_message.add_reaction(emoji)
        menu.message = new_message
        await ctx.send(f'Here it is: {menu.message.jump_url}')

    @role_selector.command(aliases=['remove'])
    @owner_or_guild_permissions(manage_roles=True)
    async def delete(self, ctx: commands.Context, menu_url):
        menu = await get_menu_from_link(ctx, menu_url)
        if not menu:
            return

        for role in menu.roles:
            if role >= ctx.author.top_role:
                return await ctx.send(f'**{role}** is (higher than) your highest role so you cannot remove a menu containing it.')

        prompt_text = 'Are you sure you want to completely delete this role selection menu? This action cannot be undone.'
        confirm = await ctx.prompt(prompt_text, reacquire=False)
        if not confirm:
            return await ctx.send('Timed out.')

        query = 'DELETE FROM rolemenus WHERE message = $1;'
        await self.bot.pool.fetchval(query, [menu.message.channel.id, menu.message.id])
        await menu.message.delete()
        del (menus[menu.message.guild.id][str(menu.message.channel.id)+','+str(menu.message.id)])
        await ctx.send('Successfully deleted the menu.')

    async def update_last_edit(self, menu: SelectionMenu, user):
        moment = datetime.utcnow()
        query = 'UPDATE rolemenus SET last_edited_by = $1, last_edited_at = $2 WHERE message = $3;'
        await self.bot.pool.fetchval(query, user.id, moment, [menu.message.channel.id, menu.message.id])
        menu.last_edited_by = user
        menu.last_edited_at = moment

    @role_selector.command()
    async def info(self, ctx: commands.Context, menu_url):
        """Get all the information there is about a role menu.

        Provide the URL of the message that contains the menu.
        """
        menu = await get_menu_from_link(ctx, menu_url)
        if not menu:
            return

        embed = discord.Embed(title='Selector Information', description=f'{"Multiple" if menu.allow_multiple else "Single"}-choice menu\nCreated by {menu.created_by} at {human_date(menu.created_at)}{f" and last edited by {menu.last_edited_by} at {human_date(menu.last_edited_at)}" if menu.last_edited_by else ""}\nThe menu is [here]({menu.message.jump_url})')
        embed.add_field(name='Menu description', value=menu.description, inline=False)
        for i in range(len(menu.roles)):
            embed.add_field(name=(str(menu.emojis[i]) if menu.emojis[i] else '*Emoji not found*'), value=f'{f"**{menu.roles[i].name}**" if menu.roles[i] else "*Role not found*"}\n{menu.role_descs[i] if menu.role_descs[i] else "No description"}')
        if menu.issues:
            embed.add_field(name=f'Issue{"s" if len(menu.issues) > 1 else ""}', value='\n'.join([f'Couldn\'t find **{issue[0]}** with ID **{issue[1]}**' for issue in menu.issues]), inline=False)
        embed.set_footer(icon_url=('https://www.iconsdb.com/icons/preview/lime/square-xxl.png' if menu.status else 'https://www.iconsdb.com/icons/preview/red/square-xxl.png'), text=f'Status: {"in" if menu.status else "out of"} service')

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        emoji, message, member = await self.info_from_payload(payload)
        if member == self.bot.user:
            return

        if message.guild.id in menus.keys():
            if str(message.channel.id)+','+str(message.id) in menus[message.guild.id].keys():
                await menus[message.guild.id][str(message.channel.id)+','+str(message.id)].reaction_received(emoji, member)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        emoji, message, member = await self.info_from_payload(payload)
        if message.guild.id in menus.keys():
            if str(message.channel.id)+','+str(message.id) in menus[message.guild.id].keys():
                await menus[message.guild.id][str(message.channel.id)+','+str(message.id)].reaction_removed(emoji, member)

    async def info_from_payload(self, payload: discord.RawReactionActionEvent):
        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        channel: discord.TextChannel = guild.get_channel(payload.channel_id)
        message: discord.Message = await channel.fetch_message(payload.message_id)
        emoji: discord.PartialEmoji = payload.emoji
        if emoji.is_custom_emoji():
            try:
                emoji: discord.Emoji = await guild.fetch_emoji(emoji.id)  # TODO figure out why this is giving (NotFound) errors at seemingly random moments, might be linked to todo in line 180
            except Exception as e:
                print('Exception received from the emoji thing')
                print(emoji, emoji)
                raise e

        else:
            emoji = emoji.name
        member = guild.get_member(payload.user_id)
        return emoji, message, member

    async def get_menus(self):
        """Get menus from database."""
        if not self.bot.is_ready():
            await self.bot.wait_for('ready')

        try:
            menus.clear()
            rows = await self.bot.pool.fetch('SELECT * FROM rolemenus')
            for menu in rows:
                guild = self.bot.get_guild(menu['guild'])
                if not guild:
                    print(f'Guild with id {menu["guild"]} not found. You can use the `unguild` command to clear '
                          f'everything from this guild from the database.')
                    continue

                channel = guild.get_channel(menu['message'][0])
                if not channel:
                    print(f'Channel with id {menu["message"][0]} not found in guild "{guild}" ({guild.id}). Contact the '
                          f'guild owner ({guild.owner}) to check if I still have permission to this channel, or you can '
                          f'use the `unchannel` command to clear everything from this channel from the database.')
                    continue

                try:
                    menu_message = await channel.fetch_message(menu['message'][1])
                except:
                    print(f'Couldn\'t find a role menu message (https://discordapp.com/channels/{guild.id}/{channel.id}/'
                          f'{menu["message"][1]}) in guild "{guild}" in channel "{channel}". Contact the guild owner '
                          f'({guild.owner}) to check if this message was removed. You can remove this menu from the database with the command '
                          f'`sql DELETE FROM rolemenus WHERE message = \'{{{channel.id}, {menu["message"][1]}}}\'`.')
                    continue

                if guild.id not in menus.keys():
                    menus[menu['guild']] = {}

                issues = []  # A list of issues with getting roles or emojis. If this list is not empty, the status of this menu will be "False".

                roles = []
                for role_id in menu['roles']:
                    role = guild.get_role(role_id)
                    if not role:
                        print(f'Couldn\'t find role with id {role_id} for menu {menu_message.jump_url} in guild "{guild}" '
                              f'in channel "{channel}". Contact the server owner ({guild.owner}) to see if they removed '
                              f'this role. You can remove this menu from the database with the command '
                              f'`sql DELETE FROM rolemenus WHERE message = \'{{{channel.id}, {menu_message.id}}}\'`.')
                        issues.append(['role', role_id])
                        roles.append(None)
                    else:
                        roles.append(role)

                emojis = []
                for emoji_id in menu['emojis']:
                    if emoji_id in amoji.unicode_codes.EMOJI_UNICODE_ENGLISH.values():
                        emojis.append(amoji.emojize(emoji_id))
                    else:
                        emoji_id = int(emoji_id)
                        try:
                            emojis.append(await guild.fetch_emoji(emoji_id))
                        except:
                            print(f'Couldn\'t find emoji with id {emoji_id} for menu {menu_message.jump_url} in guild '
                                  f'"{guild}" in channel "{channel}". Contact the server owner ({guild.owner}) to see if '
                                  f'they removed this emoji. You can remove this menu from the database with the command '
                                  f'`sql DELETE FROM rolemenus WHERE message = \'{{{channel.id}, {menu_message.id}}}\'`.')
                            issues.append(['emoji', emoji_id])
                            emojis.append(None)

                created_by = await self.bot.fetch_user(menu['created_by'])
                last_edited_by = None
                if menu['last_edited_by']:
                    last_edited_by = await self.bot.fetch_user(menu['last_edited_by'])
                status = True if (not issues) and menu['enabled'] else False
                if (not status) and (not menu_message.content.startswith('***This menu is currently out of service***\n\n')):
                    await menu_message.edit(content='***This menu is currently out of service***\n\n'+menu_message.content)
                menus[guild.id][str(channel.id)+','+str(menu_message.id)] = \
                    SelectionMenu(menu_message, menu['description'], roles, emojis, menu['role_descs'],
                                  menu['allow_multiple'], created_by, menu['created_at'], last_edited_by=last_edited_by,
                                  last_edited_at=menu['last_edited_at'], status=status, issues=issues)
        except (OSError, discord.ConnectionClosed, asyncpg.PostgresConnectionError):
            self._task.cancel()
            self._task = self.bot.loop.create_task(self.get_menus())

    @commands.command(aliases=['printrss', 'printrs'], hidden=True)
    @is_bot_admin()
    async def printmenus(self, ctx: commands.Context):
        """Print all role menus."""
        print(menus)
        await ctx.send('Check the Python printer output for your results.')

    @commands.command(aliases=['iam', 'iwant', 'gimme'])
    async def giveme(self, ctx: commands.Context, role: discord.Role):
        """Give yourself a role from the list of roles you can give yourself."""
        available_roles = self.bot.server_configs[ctx.guild.id].self_roles
        if role not in available_roles:
            return await ctx.send(f'You can only give yourself {human_join([f"**{r}**" for r in available_roles], final="and")}.')

        if role in ctx.author.roles:
            return await ctx.send('You already have this role:thinking:')

        try:
            await ctx.author.add_roles(role, reason=f'Selected role ({ctx.message.jump_url})')
            await ctx.send('Gave you the role.')
        except discord.Forbidden:
            await ctx.send('I do not have the required permissions to give you the role. I need "Manage Roles" '
                           'permissions and my highest role needs to be higher than the roles I am supposed to add/remove.')

    @commands.command(aliases=['imnot', 'removerole'])
    async def takerole(self, ctx: commands.Context, role: discord.Role):
        """Remove a role from yourself if it is on the list of self-assignable roles."""
        available_roles = self.bot.server_configs[ctx.guild.id].self_roles
        if role not in available_roles:
            return await ctx.send(f'You can only remove {human_join([f"**{r}**" for r in available_roles], final="and")} from yourself.')

        if role not in ctx.author.roles:
            return await ctx.send('You do not have this role:thinking:')

        try:
            await ctx.author.remove_roles(role, reason=f'Removed role ({ctx.message.jump_url})')
            await ctx.send('Removed the role from you.')
        except discord.Forbidden:
            await ctx.send('I do not have the required permissions to remove that role from you. I need "Manage Roles" '
                           'permissions and my highest role needs to be higher than the roles I am supposed to add/remove.')

    @commands.group(name='selfassign', aliases=['selfroles'], invoke_without_command=True)
    #@owner_or_guild_permissions(manage_roles=True)
    async def self_assign(self, ctx: commands.Context):
        """See which roles members can assign to themselves using a command. Use subcommands to change the list."""
        current_roles = self.bot.server_configs[ctx.guild.id].self_roles
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
        for role in roles:
            if role >= ctx.author.top_role:
                return await ctx.send(f'**{role}** role is (higher than) your highest role so you cannot make it available.')

        await selecting.set_roles(ctx, self.bot, 'self_roles', list(roles))

    @self_assign.command(name='add', aliases=['include'])
    @owner_or_guild_permissions(manage_roles=True)
    async def add_selfroles(self, ctx: commands.Context, *new_roles: discord.Role):
        """Add roles to the list that people can assign themselves.

        Provide role IDs, mentions or names as arguments.
        Duplicates and roles that are already on the list will be ignored.
        """
        for role in new_roles:
            if role >= ctx.author.top_role:
                return await ctx.send(f'**{role}** role is (higher than) your highest role so you cannot make it available.')

        await selecting.add_roles(ctx, self.bot, 'self_roles', list(new_roles))

    @self_assign.command(name='remove', aliases=['delete'])
    @owner_or_guild_permissions(manage_roles=True)
    async def remove_selfroles(self, ctx: commands.Context, *roles: discord.Role):
        """Remove roles from the list that members can take for themselves.

        Provide role IDs, mentions or names as arguments.
        Duplicates and roles that aren't in the list will be ignored.
        """
        for role in roles:
            if role >= ctx.author.top_role:
                return await ctx.send(f'**{role}** role is (higher than) your highest role so you cannot remove it from'
                                      f' the list.')

        await selecting.remove_roles(ctx, self.bot, 'self_roles', list(roles))

    @self_assign.command(name='clear', aliases=['wipe'])
    @owner_or_guild_permissions(manage_roles=True)
    async def clear_selfroles(self, ctx: commands.Context):
        """Clear the entire list of roles that people can give themselves."""
        current_roles = self.bot.server_configs[ctx.guild.id].self_roles
        for role in current_roles:
            if role >= ctx.author.top_role:
                return await ctx.send(f'**{role}** role is (higher than) your highest role so you cannot remove it from'
                                      f' the list. No roles have been removed.')

        await selecting.clear_roles(ctx, self.bot, 'self_roles')


def setup(bot: Curator):
    bot.add_cog(RoleSelector(bot))
