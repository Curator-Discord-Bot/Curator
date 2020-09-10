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
from platform import node
import datetime
from cogs.utils.formats import human_join

CONFIG_FILE = 'curator.conf'
DESCRIPTION = 'A bot written by Ruukas and RJTimmerman.'

LOCATION = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

INITIAL_EXTENSIONS = (
    'cogs.profile',
    'cogs.count',
    'cogs.tictactoe',
    'cogs.minecraft',
    'cogs.reminder',
    'cogs.fun',
    'cogs.decode',
    'cogs.info',
    'cogs.random',
    'cogs.admin',
    'cogs.sadmin',
    'cogs.math',
    'cogs.fourinarow',
    'cogs.emojis',
    'cogs.support'#,
    #'cogs.roleselector' ! Do not load yet
)


class Curator(commands.Bot):

    def __init__(self, client_id, command_prefix=',', admins=None, dm_dump=None, description=''):
        super().__init__(command_prefix=command_prefix, description=description)

        self.client_id = client_id
        self.admins = admins
        self.server_configs = {}
        self.dm_dump = dm_dump
        self.last_dm = None

        self._load_initial_extensions()

    def _load_initial_extensions(self):
        for extension in INITIAL_EXTENSIONS:
            try:
                self.load_extension(extension)
            except commands.ExtensionNotFound:
                traceback.print_exc()
                print(f'Couldn\'t find extension {extension}', file=sys.stderr)
            except commands.ExtensionAlreadyLoaded:
                print(f'Extension {extension} was already loaded')
            except commands.NoEntryPointError:
                traceback.print_exc()
                print(f'Exception {extension} has no entry point!', file=sys.stderr)
            except commands.ExtensionFailed:
                traceback.print_exc()
                print(f'Extension {extension} has failed.', file=sys.stderr)
            except Exception as e:
                traceback.print_exc()
                print(f'Extension {extension} failed to load: {e}')

    async def on_ready(self):
        appinfo = await self.application_info()
        self.admins = self.admins if self.admins else [appinfo.owner.id]
        await self.get_server_configs()
        if self.dm_dump:
            self.dm_dump = self.get_channel(self.dm_dump)

        print(f'Logged in as {self.user.name}')
        print(f'At UTC: {datetime.datetime.utcnow()}')
        print(f'User-ID: {self.user.id}')
        print(f'With admin{"s" if len(self.admins) > 1 else ""} {human_join([self.get_user(id) for id in self.admins], final="and")}')
        print(f'Command Prefix: {self.command_prefix}')
        print('-' * len(str(self.user.id)))

    async def get_server_configs(self):
        try:
            query = 'SELECT * FROM serverconfigs;'
            rows = await self.pool.fetch(query)
            for row in rows:
                self.server_configs[row['guild']] = {'logchannel': self.get_channel(row['logchannel']),
                                                     'chartroles': sorted([self.get_guild(row['guild']).get_role(role_id)
                                                                           for role_id in row['chartroles']], reverse=True),
                                                     'ticket_category': self.get_channel(row['ticketcategory'])}
        except Exception as e:
            print(f'Failed getting the server configurations: {e}')
            await self.logout()

        for guild in self.guilds:
            if guild.id not in self.server_configs.keys():
                query = 'INSERT INTO serverconfigs (guild) VALUES ($1);'
                await self.pool.fetchval(query, guild.id)
                self.server_configs[guild.id] = {'logchannel': None, 'chartroles': [], 'ticket_category': None}

    async def on_message(self, message: discord.Message):
        if message.channel.type == discord.ChannelType.private:
            if message.author == self.user:
                return

            if self.dm_dump:
                await self.dm_dump.send(f'**{message.author}** ({message.author.id}): {message.content}\n'
                                    f'{"Attachments: " + str([attachment.url for attachment in message.attachments]) if message.attachments else ""}')

            print(f'DM from {message.author.name}: {message.content}')

            # Safety measure to safely logout extra instances.
            if message.author.id == 261156531989512192 and message.content == 'logout':
                await message.channel.send(f'Okay, I will logout. My prefix was `{self.command_prefix}`, and I was running on `{node()}`.')
                await self.logout()
                return
            elif message.content == 'prefix':
                await message.channel.send(f'My prefix is `{self.command_prefix}`. Use it responsibly.')
                return

            self.last_dm = message.author

        elif message.guild.id == 468366604313559040 and message.author.id == 665938966452764682 \
                and message.content.endswith('join the raid!'):
            await message.channel.send(f'{message.guild.get_role(695770028397690911).mention}, '
                                       f'grab your weapons and head to battle, for there is a raid!')

        if message.author.bot:
            return

        await self.process_commands(message)

    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        if message.guild:
            logchannel = self.server_configs[message.guild.id]['logchannel']
            if logchannel:
                await logchannel.send(
                    f'A message by {message.author} was deleted in {message.channel.mention} on {message.guild}:'
                    f'\n{f"```{message.content}```" if len(message.content) >= 1 else "**No text**"}'
                    f'\n{"Attachments: " + str([attachment.url for attachment in message.attachments]) if message.attachments else ""}')

    async def process_commands(self, message):
        ctx: context.Context = await self.get_context(message, cls=context.Context)

        if ctx.command is None:
            return

        if message.guild:
            logchannel = self.server_configs[message.guild.id]['logchannel']
            if logchannel:
                await logchannel.send(f'{message.author} used command: {message.content.replace("@", "AT")}')

        try:
            await self.invoke(ctx)
        finally:
            # Just in case we have any outstanding DB connections
            await ctx.release()


def get_config():
    config = {}
    configparser = ConfigParser()
    if not os.path.isfile(os.path.join(LOCATION, CONFIG_FILE)):
        print(f'File "{CONFIG_FILE}" not found.')
        sys.exit(1)

    configparser.read(os.path.join(LOCATION, CONFIG_FILE))

    try:
        config['client_id'] = int(configparser.get('Default', 'ClientId'))
        config['token'] = configparser.get('Default', 'Token')
        config['admins'] = [int(id) for id in configparser.get('Default', 'Admins').split(',')]
        config['postgresql'] = configparser.get('Default', 'PostgreSQL')
        config['poolsize'] = int(configparser.get('Default', 'PoolSize'))
        config['command_prefix'] = configparser.get('Default', 'CommandPrefix')
        config['dm_dump'] = int(configparser.get('Default', 'DMDump'))
    except NoSectionError:
        print('Invalid config file. See README.md.')
        sys.exit(1)

    return config


def run_bot():
    config = get_config()

    loop = asyncio.get_event_loop()
    try:
        pool = loop.run_until_complete(
            Table.create_pool(config['postgresql'], command_timeout=60,
                              min_size=config['poolsize'], max_size=config['poolsize'])
        )
    except Exception as e:  # TODO: Replace generic exception.
        print(e)
        traceback.print_exc()
        print('Could not set up PostgreSQL. Exiting.')
        sys.exit(1)

    bot = Curator(config['client_id'], description=DESCRIPTION,
                  command_prefix=config['command_prefix'], admins=config['admins'], dm_dump=config['dm_dump'])
    bot.pool = pool
    bot.run(config['token'])


if __name__ == "__main__":
    run_bot()
    print('Bot loop ended')
