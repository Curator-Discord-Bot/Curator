from typing import Union

import discord
from discord.ext import commands


class Emojis(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def emoji(self, ctx: commands.Context):
        """Base emoji command."""
        await ctx.send(f'This is the base emoji command.\nSee `{ctx.prefix}help emoji` for the other commands.')

    @emoji.command(aliases=['utf-8', 'utf8', 'hex', 'bytes'])
    async def unicode(self, ctx: commands.Context, *, message: str):
        """Shows the UTF-8 Code for each supplied character"""
        lines = [f'`{c}`: \\u{ord(c):04X}' for c in message]
        await ctx.send('\n'.join(lines))

    @emoji.command()
    async def list(self, ctx: commands.Context):
        """Shows all emojis that are available to Curator."""
        await ctx.send(''.join([str(emoji) for emoji in self.bot.emojis]))

    @emoji.command()
    async def info(self, ctx: commands.Context, emoji: Union[discord.Emoji, discord.PartialEmoji, str]):
        """Shows info about a specific emoji."""
        t = type(emoji)
        embed = None
        if t == discord.Emoji:
            await ctx.send(f'{emoji}\nType: {t}\nName: {emoji.name}\nId: {emoji.id}\nRequire Colons: {emoji.require_colons}\nAnimated: {emoji.animated}\nManaged: {emoji.managed}\nGuild ID: {emoji.guild_id}\nAvailable: {emoji.available}\nCreated at: {emoji.created_at}\nURL: {emoji.url}\nRoles: {emoji.roles}')
            return
        elif t == discord.PartialEmoji:
            await ctx.send(f'{emoji}\nType: {t}\nName: {emoji.name}\nId: {emoji.id}\nAnimated: {emoji.animated}\nCustom Emoji: {emoji.is_custom_emoji()}\nUnicode Emoji: {emoji.is_unicode_emoji()}\nURL: {emoji.url}')
            return
        else:
            await ctx.send(f'{emoji}\nType: {t}\nNot much else to say about it. Maybe you wanna lookup it\'s unicode?\nTry `{ctx.prefix}unicode {emoji}`')



def setup(bot: commands.Bot):
    bot.add_cog(Emojis(bot))
