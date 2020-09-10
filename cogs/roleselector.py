import discord
from discord.ext import commands
import asyncpg
from typing import Union
from asyncio import TimeoutError
import emoji as amoji

from .utils import db, formats


class Rolemenus(db.Table):
    guild = db.Column(db.Integer(big=True), primary_key=True)
    message = db.Column(db.Array(sql_type=db.Integer(big=True)), default='{}')
    roles = db.Column(db.Array(sql_type=db.Integer(big=True)), default='{}')
    emojis = db.Column(db.Array(sql_type=db.String), default='{}')
    allow_multiple = db.Column(db.Boolean, default=True)


menus = {}


def make_message(description, roles, emojis):
    message = description
    for i in range(len(roles)):
        message += f'\n\n{emojis[i]}: **{roles[i].name}**'
    return message


class SelectionMenu:
    def __init__(self, message, roles, emojis, allow_multiple=True, status=True):
        self.message = message
        self.roles = roles
        self.emojis = emojis
        self.allow_multiple = allow_multiple
        self.status = status

    async def reaction_received(self, reaction, member):
        if reaction.emoji not in self.emojis:
            await reaction.remove(member)
            return

        if not member.dm_channel:
            await member.create_dm()

        role = self.roles[self.emojis.index(reaction.emoji)]
        if role in member.roles:
            await reaction.remove(member)
            return await member.dm_channel.send(f'**{self.message.guild}:** you already have the **{role}** role.')
        if not self.allow_multiple:
            for r in self.roles:
                if r in member.roles:
                    await reaction.remove(member)
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
        await ctx.send(f'Here it is: {menu_message.jump_url}')

        menus[ctx.guild.id][str(channel.id) + str(menu_message.id)] = SelectionMenu(menu_message, roles, emojis,
                                                                                    allow_multiple=allow_multiple)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.guild.id in menus.keys():
            if str(reaction.message.channel.id) + str(reaction.message.id) in menus[reaction.message.guild.id].keys():
                await menus[reaction.message.guild.id][str(reaction.message.channel.id) +
                                                       str(reaction.message.id)].reaction_received(reaction, user)

    async def get_menus(self):
        # Get menus from database
        query = 'SELECT * FROM rolemenus'
        rows = await self.bot.loop.fetch(query)
        for menu in rows:
            if menu['guild'] not in menus.keys():
                menus[menu['guild']] = {}
            menu_message = await self.bot.get_channel(menu['message'][0]).fetch_message(menu['message'][1])
            roles = [menu_message.get_role(role_id) for role_id in menu['roles']]
            emojis = []
            skip = False
            for emoji_id in menu['emojis']:
                if emoji_id in amoji.EMOJI_UNICODE:
                    emojis.append(amoji.emojize(emoji_id))
                else:
                    try:
                        emojis.append(emoji_id)
                    except discord.NotFound:
                        # Contact server owner in
                        emojis.append(None)
            status = False if None in roles + emojis else True
            menus[menu['guild']][str(menu['message'][0]) + str(menu['message'][1])] = SelectionMenu(menu_message, roles, emojis, allow_multiple=menu['allow_multiple'], status=status)


def setup(bot: commands.Bot):
    bot.add_cog(RoleSelector(bot))
