import sys
import traceback
from configparser import ConfigParser, NoSectionError
import discord
from discord.ext import commands
import asyncio
from asyncpg.pool import Pool
from cogs.utils import context
from cogs.utils.db import Table
import os

# import cogs.utils.messages

CONFIG_FILE = 'curator.conf'
DESCRIPTION = 'A bot written by Ruukas.'

LOCATION = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


INITIAL_EXTENSIONS = (
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
    # pool: Pool

    def __init__(self, client_id, command_prefix=',', description=''):
        super().__init__(command_prefix=command_prefix, description=description)

        self.client_id = client_id
        self.logchannel = None

        for extension in INITIAL_EXTENSIONS:
            try:
                self.load_extension(extension)
            except Exception as e:  # TODO: Replace generic exception.
                print(e)
                print(f'Failed to load extension {extension}.', file=sys.stderr)
                traceback.print_exc()

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print(f'Command Prefix: {self.command_prefix}')
        print('-'*len(str(self.user.id)))
        # TODO : Set logon greeting channels in config or database
        # await self.get_guild(681912993621344361).get_channel(681914163974766637).send(messages.on_ready())
        # await self.get_guild(468366604313559040).get_channel(474922467626975233).send(messages.on_ready())

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

        from cogs.count import running_counts, deleted_count
        if message.channel.id in running_counts.keys():
            await deleted_count(message)

        if not self.logchannel:
            self.logchannel = self.get_guild(468366604313559040).get_channel(474922467626975233)

        if self.logchannel:
            await self.logchannel.send(
                f'A message by {message.author.mention} was deleted in {message.channel.mention} on {message.guild.name}:'
                '\n`--------------------------------------------------`'
                f'\n{message.content.replace("@", "AT")}'
                '\n`--------------------------------------------------`')

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


def get_config():
    config = {}
    configparser = ConfigParser()
    if not os.path.isfile(os.path.join(LOCATION, CONFIG_FILE)):
        print('File %s not found.' % CONFIG_FILE)
        sys.exit(1)

    configparser.read(os.path.join(LOCATION, CONFIG_FILE))

    try:
        config['client_id'] = int(configparser.get('Default', 'ClientId'))
        config['token'] = configparser.get('Default', 'Token')
        config['postgresql'] = configparser.get('Default', 'PostgreSQL')
        config['poolsize'] = int(configparser.get('Default', 'PoolSize'))
        config['command_prefix'] = configparser.get('Default', 'CommandPrefix')
    except NoSectionError:
        print('Invalid config file. See README.md.')
        sys.exit(1)

    return config


def run_bot():
    config = get_config()

    loop = asyncio.get_event_loop()
    try:
        pool = loop.run_until_complete(
            Table.create_pool(config['postgresql'], command_timeout=60, min_size=config['poolsize'], max_size=config['poolsize'])
        )
    except Exception as e:  # TODO: Replace generic exception.
        print(e)
        traceback.print_exc()
        print('Could not set up PostgreSQL. Exiting.')
        sys.exit(1)

    bot = Curator(config['client_id'], description=DESCRIPTION, command_prefix=config['command_prefix'])
    bot.pool = pool
    bot.run(config['token'])


if __name__ == "__main__":
    run_bot()
    print('Bot loop ended')
