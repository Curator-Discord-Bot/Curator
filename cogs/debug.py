import discord
from discord.ext import commands

import emoji


class Debug(commands.Cog):
    """Admin-only debug commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx: commands.Context):
        return ctx.author.id in self.bot.admins

    @commands.command(hidden=True)
    async def print(self, ctx: commands.Context, *, text):
        """Print some text in Python."""
        print(text)
        await ctx.send('Check the Python printer output for your results.')

    @commands.command(hidden=True)
    async def printsendchars(self, ctx: commands.Context, *, text):
        """Print every character in Python and send them in chat.

         This is useful for weird things like keycap numbers.
         """
        for char in text:
            print(char)
            await ctx.send(char if char != ' ' else '[space]')
        await ctx.send('Also check the Python printer output for your results.')

    @commands.command(hidden=True)
    async def printdemoji(self, ctx: commands.Context, emo):
        """Print the demojized version of an emoji in Python."""
        print(emoji.demojize(emo))
        await ctx.send('Check the Python printer output for your results')

    @commands.command(hidden=True)
    async def printsc(self, ctx: commands.Context):
        """Print the current server configurations for every server."""
        print({self.bot.get_guild(guild).name: {attr: value for attr, value in configs.__dict__.items()} for guild, configs in self.bot.server_configs.items()})
        #print({f'{self.bot.get_guild(key).name} ({key})': {'logchannel': f'{value["logchannel"].name} ({value["logchannel"].id})' if value["logchannel"] else None,
        #                                                   'chartroles': [f'{role.name} ({role.id})' for role in value['chartroles']],
        #                                                   'ticket_category': f'{value["ticket_category"].name} ({value["ticket_category"].id})' if value["ticket_category"] else None}
        #       for (key, value) in self.bot.server_configs.items()}) TODO re-write for new SererConfigs class
        await ctx.send('Check the Python printer output for your results')
        # Please do not reformat this code

    @commands.command(hidden=True)
    async def mentions(self, ctx: commands.Context):
        await ctx.send(str([member.name for member in ctx.message.mentions]))

    @commands.command(hidden=True)
    async def authorof(self, ctx: commands.Context, message_link):
        IDs = message_link.split('/')[-2:]
        message = await self.bot.get_channel(int(IDs[0])).fetch_message(int(IDs[1]))
        await ctx.send(message.author.id)
        print(message.author.id)

    @commands.command(hidden=True)
    async def nameof(self, ctx: commands.Context, user_id: int):
        user = await self.bot.fetch_user(user_id)
        await ctx.send(user.name)

    @commands.command(hidden=True)
    async def channelbyid(self, ctx: commands.Context, id: int):
        channel = self.bot.get_channel(id)
        print(channel)
        print(channel.type)
        await ctx.send(channel.name)
        await ctx.send(channel.type)
        await ctx.send('Also check the Python printer output for your results.')


def setup(bot: commands.Bot):
    bot.add_cog(Debug(bot))
