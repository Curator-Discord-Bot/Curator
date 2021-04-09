import discord
from discord.ext import commands


class GuildConverter(commands.IDConverter):
    """Converts to a :class:`~discord.Guild`.

    All lookups are done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    """

    async def convert(self, ctx: commands.Context, argument):  # Code by DarkNinja2462#3141 (358408384426409984) on Discord. This will have to do until discord.py gets its own GuildChanger
        match = self._get_id_match(argument)
        if match:
            guild = ctx.bot.get_guild(int(match.group(1)))
            if not guild:
                raise commands.BadArgument('Guild "{}" not found.'.format(argument))
            return guild
        else:
            raise commands.BadArgument('Guild "{}" not found.'.format(argument))


class GuildChanger(GuildConverter):
    async def convert(self, ctx, argument):
        result = await super().convert(ctx, argument)
        ctx.guild = result
        return result


class GlobalTextChannel(commands.Converter):  # Code by Rapptz AKA Danny (the creator of the discord.py module, Danny#0007 (80088516616269824) on Discord) (https://github.com/Rapptz/RoboDanny/blob/6f278d1363a45ad7001e97361da0cde4f997c1fc/cogs/admin.py#L65-L79) and adapted by me (RJTimmerman), same for GlobalCategoryChannel
    async def convert(self, ctx, argument):
        try:
            return await commands.TextChannelConverter().convert(ctx, argument)
        except commands.BadArgument:
            # Not found... so fall back to ID + global lookup
            try:
                channel_id = int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f'Could not find a text channel by ID {argument!r}.')
            else:
                channel = ctx.bot.get_channel(channel_id)
                if channel is None or type(channel) != discord.TextChannel:
                    raise commands.BadArgument(f'Could not find a text channel by ID {argument!r}.')
                return channel


class GlobalCategoryChannel(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            return await commands.CategoryChannelConverter().convert(ctx, argument)
        except commands.BadArgument:
            # Not found... so fall back to ID + global lookup
            try:
                channel_id = int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f'Could not find a category by ID {argument!r}.')
            else:
                channel = ctx.bot.get_channel(channel_id)
                if channel is None or type(channel) != discord.CategoryChannel:
                    raise commands.BadArgument(f'Could not find a category by ID {argument!r}.')
                return channel


class GlobalTChannelChanger(GlobalTextChannel):
    async def convert(self, ctx, argument):
        result = await super().convert(ctx, argument)
        ctx.guild = result.guild
        ctx.channel = result.channel
        return result


class GlobalCChannelGChanger(GlobalCategoryChannel):
    async def convert(self, ctx, argument):
        result = await super().convert(ctx, argument)
        ctx.guild = result.guild
        return result
