import discord
from discord.ext import commands
import asyncpg
from typing import Union
from asyncio import TimeoutError
import emoji as amoji

from .utils import db, formats


class Rolemenus(db.Table):
    guild = db.Column(db.Integer(big=True))
    message = db.Column(db.Array(sql_type=db.Integer(big=True)), primary_key=True)
    description = db.Column(db.String, default='')
    roles = db.Column(db.Array(sql_type=db.Integer(big=True)), default='{}')
    emojis = db.Column(db.Array(sql_type=db.String), default='{}')
    allow_multiple = db.Column(db.Boolean, default=True)


menus = {}


def make_message(description, roles, emojis):
    message = description
    for i in range(len(roles)):
        message += f'\n\n{emojis[i]}: **{roles[i].name}**'
    return message


async def get_menu_from_link(ctx, url):
    IDs = url.split('/')[-3:]
    if IDs[0] not in menus.keys():
        return None
    if str(IDs[1])+','+str(IDs[2]) not in menus[IDs[0]].keys():
        return None
    return menus[IDs[0]][str(IDs[1])+','+str(IDs[2])]


class SelectionMenu:
    def __init__(self, message, description, roles, emojis, allow_multiple=True, status=True, issues=None):
        self.message = message
        self.description = description
        self.roles = roles
        self.emojis = emojis
        self.allow_multiple = allow_multiple
        self.status = status
        self.issues = issues

    async def reaction_received(self, emoji, member):
        if emoji not in self.emojis:
            await self.message.remove_reaction(emoji, member)
            return

        if not member.dm_channel:
            await member.create_dm()

        role = self.roles[self.emojis.index(emoji)]
        if role in member.roles:
            await self.message.remove_reaction(emoji, member)
            return await member.dm_channel.send(f'**{self.message.guild}:** you already have the **{role}** role.')
        if not self.allow_multiple:
            for r in self.roles:
                if r in member.roles:
                    await self.message.remove_reaction(emoji, member)
                    return await member.dm_channel.send(f'**{self.message.guild}:** you already have a role from this'
                                                        f' menu, you must first remove **{r}** if you want **{role}**.')

        try:
            await member.add_roles(role, reason=f'Selected role ({self.message.jump_url})')
            return await member.dm_channel.send(f'**{self.message.guild}:** gave you the **{role}** role.')
        except discord.Forbidden:
            guild_owner = self.message.guild.owner
            if not guild_owner.dm_channel:
                await guild_owner.create_dm()
            await guild_owner.dm_channel.send(f'**{self.message.guild}:** I do not have the required permissions to give'
                                              f' **{member}** the **{role}** role on your server. I need "Manage Roles"'
                                              f' and my highest role needs to be higher than the roles you want me to add.')
            await member.dm_channel.send(f'**{self.message.guild}:** I don\'t have permission to give you the **{role}**'
                                         f' role. I have contacted the server owner about this.')

    async def reaction_removed(self, reaction, user):
        pass


class RoleSelector(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._task = bot.loop.create_task(self.get_menus())

    @commands.group(name='roleselector', aliases=['rselector', 'rolesel', 'rsel', 'rs'])
    async def role_selector(self, ctx: commands.Context):
        """All commands revolving around the role selection menus."""
        if ctx.guild.id not in menus.keys():
            menus[ctx.guild.id] = {}

        if not ctx.invoked_subcommand:
            await ctx.send(f'Use `{ctx.prefix}help roleselector` for the possible commands.')

    @role_selector.command(name='make', aliases=['create', 'new'])
    async def make_rsel(self, ctx: commands.Context, channel: discord.TextChannel,
                        *roles_and_emojis: Union[discord.Role, discord.Emoji, discord.PartialEmoji, str]):
        if len(roles_and_emojis) % 2 == 1:
            return await ctx.send(f'Provide a valid list of arguments (`{ctx.prefix}help roleselector make` for info on'
                                  f' how to use this command)')

        roles = []
        emojis = []
        i = 0
        for item in roles_and_emojis:
            if i % 2 == 0:
                if type(item) == discord.Role:
                    if item in roles:
                        return await ctx.send('You have put in the same role more than once.')
                    else:
                        roles.append(item)
                else:
                    return await ctx.send(f'`{item}` is invalid.')
            else:
                if type(item) == discord.Emoji or type(item) == discord.PartialEmoji or item in amoji.EMOJI_UNICODE.values():
                    if item in emojis:
                        return await ctx.send('You can only use an emoji once.')
                    else:
                        emojis.append(item)
                else:
                    return await ctx.send(f'`{item}` is invalid.')
            i += 1

        def check1(message):
            return message.author == ctx.author and message.channel == ctx.channel

        await ctx.send('Give the description of the selection menu (times out in 5 minutes).')
        try:
            description = await self.bot.wait_for('message', check=check1, timeout=300)
        except TimeoutError:
            return await ctx.send('Timed out')
        description = description.content

        def check2(reaction, user):
            return user == ctx.author and reaction.message.id == m.id

        m = await ctx.send('Are people allowed to select multiple roles from the list? React with :white_check_mark: or'
                           ' :x: (times out in 1 minute).')
        await m.add_reaction('✅')
        await m.add_reaction('❌')
        try:
            r, u = await self.bot.wait_for('reaction_add', check=check2, timeout=60)
        except TimeoutError:
            return await ctx.send('Timed out')
        allow_multiple = True if r.emoji == '✅' else False

        menu_message = await channel.send(make_message(description, roles, emojis))
        for emoji in emojis:
            await menu_message.add_reaction(emoji)

        query = 'INSERT INTO rolemenus VALUES ($1, $2, $3, $4, $5, $6);'
        await self.bot.pool.fetchval(query, ctx.guild.id, [channel.id, menu_message.id], description, [role.id for role in roles], [str(emoji.id) if type(emoji) == discord.Emoji or type(emoji) == discord.PartialEmoji else emoji for emoji in emojis], allow_multiple)

        await ctx.send(f'Here it is: {menu_message.jump_url}')
        menus[ctx.guild.id][str(channel.id)+','+str(menu_message.id)] = SelectionMenu(menu_message, description, roles, emojis, allow_multiple=allow_multiple)

    @role_selector.command()
    async def info(self, ctx: commands.Context, message_url):
        menu = await get_menu_from_link(ctx, message_url)
        if not menu:
            return await ctx.send('Please provide a valid message URL.')

        embed = discord.Embed(title='Selector Information', description=menu.description)
        embed.add_field(name='Roles', value=formats.human_join([role.name for role in menu.roles], final='and'))

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        emoji, message, user = await self.info_from_payload(payload)
        if user == self.bot.user:
            return

        if message.guild.id in menus.keys():
            if str(message.channel.id) + ',' + str(message.id) in menus[message.guild.id].keys():
                await menus[message.guild.id][str(message.channel.id)+','+str(message.id)].reaction_received(emoji, user)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        emoji, message, user = await self.info_from_payload(payload)
        if message.guild.id in menus.keys():
            if str(message.channel.id) + ',' + str(message.id) in menus[message.guild.id].keys():
                await menus[message.guild.id][str(message.channel.id)+','+str(message.id)].reaction_removed(emoji, user)

    async def info_from_payload(self, payload: discord.RawReactionActionEvent):
        guild: discord.Guild = self.bot.get_guild(payload.guild_id)
        channel: discord.TextChannel = guild.get_channel(payload.channel_id)
        message: discord.Message = await channel.fetch_message(payload.message_id)
        emoji = payload.emoji
        if emoji.is_custom_emoji():
            emoji = await guild.fetch_emoji(emoji.id)
        else:
            emoji = emoji.name
        member = guild.get_member(payload.user_id)
        return emoji, message, member

    async def get_menus(self):
        """Get menus from database."""
        print('Getting role menus from database.')
        query = 'SELECT * FROM rolemenus'
        rows = await self.bot.pool.fetch(query)
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
                      f'({guild.ower}) to check if this message was removed. You can remove this menu from the database with the command '
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
                if emoji_id in amoji.EMOJI_UNICODE.values():
                    emojis.append(amoji.emojize(emoji_id))
                else:
                    emoji_id = str(emoji_id)
                    try:
                        emojis.append(await guild.fetch_emoji(emoji_id))
                    except:
                        print(f'Couldn\'t find emoji with id {emoji_id} for menu {menu_message.jump_url} in guild '
                              f'"{guild}" in channel "{channel}". Contact the server owner ({guild.owner}) to see if '
                              f'they removed this emoji. You can remove this menu from the database with the command '
                              f'`sql DELETE FROM rolemenus WHERE message = \'{{{channel.id}, {menu_message.id}}}\'`.')
                        issues.append(['emoji', emoji_id])
                        emojis.append(None)

            status = True if len(issues) == 0 else False
            menus[guild.id][str(channel.id)+','+str(menu_message.id)] = SelectionMenu(menu_message, menu['description'], roles, emojis, allow_multiple=menu['allow_multiple'], status=status, issues=issues)
        print('Finished getting role menus from database.')

    @commands.command(hidden=True)
    async def printmenus(self, ctx: commands.Context):
        """Print all role menus."""
        if ctx.author.id in self.bot.admins:
            for guild in menus.values():
                for menu in guild.values():
                    print(menu.message, menu.roles, menu.emojis, menu.allow_multiple, menu.status, menu.issues)
            await ctx.send('Check the Python printer output for your results.')
        else:
            await ctx.send('You do not have access to this command.')


def setup(bot: commands.Bot):
    bot.add_cog(RoleSelector(bot))
