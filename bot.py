import discord
from discord.ext import commands
import asyncio
import asyncpg
import config
import sys
import traceback

initial_extensions = (
    'cogs.count',
    'cogs.admin'
)


class Curator(commands.Bot):
    def __init__(self, commands_prefix=',', description=''):
        super().__init__(command_prefix=commands_prefix, description=description)

        self.client_id = config.client_id

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f'Failed to load extension {extension}.', file=sys.stderr)
                traceback.print_exc()

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message: discord.message):
        await self.process_commands(message)


def run_bot():
    loop = asyncio.get_event_loop()
    try:
        pool = loop.run_until_complete(asyncpg.create_pool(config.postgresql))
    except Exception as e:
        print(e)
        print('Could not set up PostgreSQL. Exiting.')
        return

    description = '''A bot written by Ruukas.'''
    bot = Curator(description=description)
    bot.pool = pool
    bot.run(config.token)


run_bot()
