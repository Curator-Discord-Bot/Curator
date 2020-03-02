import discord
from discord.ext import commands
import asyncio

import config
import sys
import traceback
import random

from cogs.utils import context
from cogs.utils.db import Table

initial_extensions = (
    'cogs.profile',
    'cogs.count',
    'cogs.reminder',
    'cogs.minecraft',
    'cogs.fun',
    'cogs.math',
    'cogs.info',
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
        await self.get_guild(681912993621344361).get_channel(681914163974766637).send(random.choice(['Hey there:smirk:', 'Hey!:smiley:', 'G\'day people:wave:', 'Hi, I\'m alive!', 'Hi, how are ya?', 'Thanks for giving me life!:smiling_face_with_3_hearts:']))

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if 'Count' in self.cogs.keys():
            if await self.cogs['Count'].check_count(message):
                return

        await self.process_commands(message)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        try:
            await self.invoke(ctx)
        finally:
            # Just in case we have any outstanding DB connections
            await ctx.release()


def run_bot():
    loop = asyncio.get_event_loop()
    try:
        pool = loop.run_until_complete(Table.create_pool(config.postgresql, command_timeout=60, min_size=3, max_size=3))
    except Exception as e:
        print(e)
        print('Could not set up PostgreSQL. Exiting.')
        return

    description = '''A bot written by Ruukas.'''
    if config.command_prefix is None:
        bot = Curator(description=description)
    else:
        bot = Curator(commands_prefix=config.command_prefix, description=description)
    bot.pool = pool
    bot.run(config.token)


if __name__ == "__main__":
    run_bot()
