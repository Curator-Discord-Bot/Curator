import discord
from discord.ext import commands
import asyncio

import config
import sys
import traceback

from asyncpg.pool import Pool

from cogs.utils import context
from cogs.utils.db import Table
from cogs.utils.messages import on_ready

initial_extensions = (
    'cogs.profile',
    'cogs.count',
    'cogs.reminder',
    'cogs.minecraft',
    'cogs.fun',
    'cogs.info',
    'cogs.random',
    'cogs.admin'
)


class Curator(commands.Bot):
    pool: Pool

    def __init__(self, commands_prefix=',', description=''):
        super().__init__(command_prefix=commands_prefix, description=description)

        self.client_id = config.client_id
        self.logchannel = None

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
        await self.get_guild(681912993621344361).get_channel(681914163974766637).send(on_ready())

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if 'Count' in self.cogs.keys():
            if await self.cogs['Count'].check_count(message):
                return

        if 'Reminder' in self.cogs.keys():
            if await self.cogs['Reminder'].check_idlerpg(message):
                return

        await self.process_commands(message)

    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        if not self.logchannel:
            self.logchannel = self.get_guild(468366604313559040).get_channel(474922467626975233)

        if self.logchannel:
            await self.logchannel.send(f'A message by {message.author} was deleted in {message.channel} on {message.guild}.')

    async def process_commands(self, message):
        ctx: context.Context = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        if not self.logchannel:
            self.logchannel = self.get_guild(468366604313559040).get_channel(474922467626975233)

        if self.logchannel:
            await self.logchannel.send(f'{message.author} used command: {ctx.message.content.replace("@", "ATSYMBOL")}')

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
        return None

    description = '''A bot written by Ruukas.'''
    bot = Curator(description=description) if config.command_prefix is None else Curator(
        commands_prefix=config.command_prefix, description=description)
    bot.pool = pool
    bot.run(config.token)


if __name__ == "__main__":
    run_bot()
    print('Bot loop ended')
