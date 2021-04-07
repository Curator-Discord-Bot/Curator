import discord
from discord.ext import commands
from bot import Curator
from typing import Optional, Union
from .utils.converter import *
from .utils.paginator import TextPages
from .utils.formats import human_join


class Sinfo(commands.Cog):
    """Commands to get information about server settings."""

    def __init__(self, bot: Curator):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        return ctx.author.id in self.bot.admins

    @commands.command(hidden=True)
    async def channels(self, ctx: commands.Context, where: Optional[Union[GuildConverter, GlobalCategoryChannel]]):
        where = where or ctx.guild
        if type(where) == discord.Guild:
            await TextPages(ctx, '\n'.join('\n'.join(
                [f'___**{f"{category[0].name}** ({category[0].id})**" if category[0] else "No category"}:**___'] +
                ([f'ᅠ**{channel.name}** ({channel.id}, {f"{channel.mention}" if type(channel) == discord.TextChannel else "_voice channel_"})'
                  for channel in category[1]] if category[1] else ['ᅠNo channels'])) for category in where.by_category()),
                            prefix=f'`Channels in {where}`', suffix=None).paginate()
        else:  # type(where) == discord.CategoryChannel
            await ctx.send(f'`Channels in {where} in {where.guild}`\n' +
                           ('\n'.join([f'**{channel.name}** ({channel.id}, '
                                       f'{f"{channel.mention}" if type(channel) == discord.TextChannel else "_voice channel_"})'
                                       for channel in where.channels]) if where.channels else 'No channels'))

    @commands.command(hidden=True)
    async def sadmins(self, ctx: commands.Context, guild: Optional[GuildConverter]):
        guild: discord.Guild = guild or ctx.guild
        member_list = [f'**{member}** ({member.display_name}, {member.id}{", bot" if member.bot else ""})' for member in guild.members if member.guild_permissions.administrator]
        await ctx.send(human_join(member_list, final='and') + f' ha{"s" if len(member_list) == 1 else "ve"} admin perms in *{guild}*.')

    @commands.command(hidden=True)
    async def sowner(self, ctx: commands.Context, guild: Optional[GuildConverter]):
        guild: discord.Guild = guild or ctx.guild
        await ctx.send(f'**{guild.owner}** ({guild.owner.display_name}, {guild.owner.id}) is the owner of *{guild}*.')

    @commands.command(hidden=True)
    async def rolemembers(self, ctx: commands.Context, guild: Optional[GuildChanger], role: discord.Role):
        ctx.guild = ctx.channel.guild
        guild: discord.Guild = guild or ctx.guild
        await ctx.send((((human_join([f'**{member}** ({member.display_name}, {member.id})' for member in role.members], final='and') + f' ha{"ve" if len(role.members) > 1 else "s"}') if role.members else f'Nobody has') + f' **{role.name}** ({role.id}) in *{guild}* ({guild.id}).') if role != guild.default_role else 'Everyone has the everyone role:rolling_eyes:')


def setup(bot: Curator):
    bot.add_cog(Sinfo(bot))
