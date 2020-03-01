import discord
from discord.ext import commands

from twisted.internet import reactor
from quarry.net.server import ServerFactory, ServerProtocol


class DowntimeProtocol(ServerProtocol):
    def packet_login_start(self, buff):
        buff.discard()
        self.close(self.factory.motd)


class DowntimeFactory(ServerFactory):
    protocol = DowntimeProtocol


def run():
    try:
        # Create factory
        factory = DowntimeFactory()
        factory.motd = 'Hello'

        # Listen
        factory.listen("", 25565)
        reactor.run()
    except Exception as e:
        print('Server run failed:', e)


class MCChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def run(self, ctx: commands.Context):
        await ctx.send('Let\'s try this!')
        run()


def setup(bot: commands.Bot):
    bot.add_cog(MCChat(bot))
