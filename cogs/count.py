import datetime
import itertools
from collections import OrderedDict
from typing import Optional
import re

import asyncpg
import discord
from discord.ext import commands
import emoji
from random import choice

import bot
from .utils import db, formats


class Counts(db.Table):
    id = db.PrimaryKeyColumn()

    guild = db.Column(db.Integer(big=True))
    channel = db.Column(db.Integer(big=True))

    started_by = db.Column(db.ForeignKey(table='profiles', column='discord_id', sql_type=db.Integer(big=True)))
    started_at = db.Column(db.Datetime, default="now() at time zone 'utc'")

    score = db.Column(db.Integer, default='0')
    contributors = db.Column(db.JSON, default="'{}'::jsonb")

    timed_out = db.Column(db.Boolean, default="FALSE")
    duration = db.Column(db.Interval)
    ruined_by = db.Column(db.ForeignKey(table='profiles', column='discord_id', sql_type=db.Integer(big=True)))

    type = db.Column(db.String, default="normal")


class Counters(db.Table):
    user_id = db.Column(db.ForeignKey(table='profiles', column='discord_id', sql_type=db.Integer(big=True)),
                        primary_key=True)
    last_count = db.Column(db.ForeignKey(table='counts', column='id', sql_type=db.Integer()))
    best_count = db.Column(db.ForeignKey(table='counts', column='id', sql_type=db.Integer()))
    best_ruin = db.Column(db.ForeignKey(table='counts', column='id', sql_type=db.Integer()))
    total_score = db.Column(db.Integer, default=0)
    counts_participated = db.Column(db.Integer, default=0)
    counts_ruined = db.Column(db.Integer, default=0)
    counts_started = db.Column(db.Integer, default=0)


number_aliases = {
    'keycap_0': ['0'],
    'regional_indicator_symbol_letter_o': ['0'],
    'O_button_(blood_type)': ['0'],
    'heavy_large_circle': ['0'],
    'keycap_1': ['1'],
    'one_o’clock': ['1', '13'],
    'regional_indicator_symbol_letter_i': ['1'],
    '1st_place_medal': ['1'],
    'keycap_2': ['2'],
    '2nd_place_medal': ['2'],
    'two_o’clock': ['2', '14'],
    'keycap_3': ['3'],
    'three_o’clock': ['3', '15'],
    'alarm_clock': ['3'],
    '3rd_place_medal': ['3'],
    'evergreen_tree': ['3'],
    'deciduous_tree': ['3'],
    'palm_tree': ['3'],
    'Christmas_tree': ['3'],
    'cactus': ['3'],
    'shamrock': ['3'],
    'keycap_4': ['4'],
    'four_o’clock': ['4', '16'],
    'four_leaf_clover': ['4'],
    'keycap_5': ['5'],
    'white_medium_star': ['5'],
    'five_o’clock': ['5', '17'],
    'keycap_6': ['6'],
    'six_o’clock': ['6', '18'],
    'dotted_six-pointed_star': ['6'],
    'keycap_7': ['7'],
    'seven_o’clock': ['7', '19'],
    'keycap_8': ['8'],
    'eight_o’clock': ['8', '20'],
    'pool_8_ball': ['8'],
    'sun': ['8'],
    '\u267E': ['8'],
    'keycap_9': ['9'],
    'nine_o’clock': ['9', '21'],
    'mantelpiece_clock': ['9', '21'],
    'keycap_10': ['10'],
    'ten_o’clock': ['10', '22'],
    'eleven_o’clock': ['11', '23'],
    'twelve_o’clock': ['12', '0', '24'],
    'ringed_planet': ['42'],
    'milky_way': ['42'],
    'OK_hand': ['69'],
    'Cancer': ['69'],
    'hundred_points': ['100', '00'],
    'input_numbers': ['1', '2', '3', '4'],
    '\u3007': ['0'],
    '\u96F6': ['0'],
}

roman_re = re.compile('^(?=[MDCLXVI])M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3})$')
binary_re = re.compile('^[01]+$')

running_counts = {}
finished_counts = {}

"""    Old parsing function
def parsed(number: str) -> list:
    number = emoji.emojize(number)
    plist = [c for c in number]
    emojis = [(i['emoji'], i['location']) for i in emoji.emoji_lis(number)]
    for e, i in emojis:
        plist[i] = number_aliases[emoji.demojize(e)]

    return [''.join(i) for i in itertools.product(*plist)]
"""


def parsed(number: str) -> list:
    results = ['']
    numbers = filter(None, emoji.demojize(number).split(':'))
    for digit in numbers:
        if digit.isdigit():
            results = add_parsed(results, [digit])
        elif digit in number_aliases.keys():
            results = add_parsed(results, number_aliases[digit])
        else:
            return []
    return results


def add_parsed(old_results: list, numbers: list) -> list:
    new_results = []
    for number in numbers:
        for result in old_results:
            s = result + number
            if len(s) > 0 and s[0] != '0':
                new_results.append(s)
    return new_results


def write_roman(num):
    # from https://stackoverflow.com/questions/28777219/basic-program-to-convert-integer-to-roman-numerals/28777781
    roman = OrderedDict()
    roman[1000] = "M"
    roman[900] = "CM"
    roman[500] = "D"
    roman[400] = "CD"
    roman[100] = "C"
    roman[90] = "XC"
    roman[50] = "L"
    roman[40] = "XL"
    roman[10] = "X"
    roman[9] = "IX"
    roman[5] = "V"
    roman[4] = "IV"
    roman[1] = "I"

    def roman_num(num):
        for r in roman.keys():
            x, y = divmod(num, r)
            yield roman[r] * x
            num -= (r * x)
            if num <= 0:
                break

    return ''.join([i for i in roman_num(num)])


def from_roman(num):
    # from https://stackoverflow.com/questions/19308177/converting-roman-numerals-to-integers-in-python
    roman_numerals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    for i, c in enumerate(num):
        if (i + 1) == len(num) or roman_numerals[c] >= roman_numerals[num[i + 1]]:
            result += roman_numerals[c]
        else:
            result -= roman_numerals[c]
    return result


async def fetch_counter_record(discord_id, connection) -> asyncpg.Record:
    return await connection.fetchrow(
        'INSERT INTO counters (user_id) VALUES ($1) ON CONFLICT (user_id) DO UPDATE SET user_id = counters.user_id RETURNING *',
        discord_id)


def is_count_channel(channel: discord.TextChannel):
    return 'count' in channel.name.lower()


async def check_channel(channel: discord.TextChannel, message=False) -> bool:
    if not is_count_channel(channel):
        if message:
            await channel.send(
                'Count commands are intended for use only in channels that contain "count" in the name...')
        return False
    return True


class CounterProfile:
    # __slots__ = (
    #    'user_id', 'last_count', 'best_count', 'best_ruin', 'total_score', 'counts_participated', 'counts_ruined',
    #    'counts_started')

    def __init__(self, *, d: dict):
        self.user_id = d['user_id']
        self.last_count = d['last_count']
        self.best_count = d['best_count']
        self.best_ruin = d['best_ruin']
        self.total_score = d['total_score']
        self.counts_participated = d['counts_participated']
        self.counts_ruined = d['counts_ruined']
        self.counts_started = d['counts_started']


class Counter:
    __slots__ = ('original', 'current', 'connection')
    original: CounterProfile
    current: CounterProfile
    connection: asyncpg.pool.Pool

    def __init__(self, record, connection):
        self.original = CounterProfile(d=db.dict_from_record(record))
        self.current = CounterProfile(d=db.dict_from_record(record))
        self.connection = connection

    async def save(self):
        original_keys = self.original.__dict__.keys()
        updates = [(key, value) for key, value in self.current.__dict__.items() if
                   key not in original_keys or value != self.original.__dict__[key]]
        if updates:
            query = f'UPDATE counters SET {", ".join([str(key) + " = " + str(value) for key, value in updates])} ' \
                    f'WHERE user_id={self.original.user_id} RETURNING *;'
            await self.connection.execute(query)

    async def __aenter__(self) -> CounterProfile:
        return self.current

    async def __aexit__(self, typ, value, traceback):
        await self.save()

    def __repr__(self):
        return f'<Counter discord_id={self.current.user_id}>'


class Counting:
    __slots__ = ('id', 'guild', 'channel', 'started_by', 'started_at', 'score', 'contributors', 'last_active_at',
                 'last_counter', 'timed_out', 'duration', 'ruined_by', 'mode')

    def __init__(self, *, record):
        self.id = record['id']
        self.guild = record['guild']
        self.channel = record['channel']
        self.started_by = record['started_by']
        self.started_at = record['started_at']
        self.score = record['score']
        self.contributors = record['contributors']
        self.last_active_at = record['last_active_at']
        self.last_counter = record['last_counter']
        self.timed_out = False
        self.ruined_by = None
        self.mode = 'any'

    @classmethod
    def temporary(cls, *, guild, channel, started_by, started_at, score=0, contributors=None, last_active_at,
                  last_counter=None):
        if contributors is None:
            contributors = {}
        pseudo = {
            'id': None,
            'guild': guild,
            'channel': channel,
            'started_by': started_by,
            'started_at': started_at,
            'score': score,
            'contributors': contributors,
            'last_active_at': last_active_at,
            'last_counter': last_counter
        }
        return cls(record=pseudo)

    def attempt_count(self, counter: discord.User, count: str) -> bool:
        target = self.score + 1
        target_s = str(target)
        if (counter.id != self.last_counter) and (
                count == target_s or count == write_roman(target) or count == bin(target)[2:] or target_s in parsed(count)):
            self.last_active_at = datetime.datetime.utcnow()
            self.last_counter = counter.id
            self.score += 1
            if counter.id not in self.contributors.keys():
                self.contributors[counter.id] = 1
            else:
                self.contributors[counter.id] += 1
            return True
        return False

    async def finish(self, curator: bot.Curator, timed_out: bool, ruined_by: discord.User):
        connection: asyncpg.pool = curator.pool
        self.timed_out = timed_out
        self.ruined_by = ruined_by.id

        # async with Counter(await fetch_counter_record(discord_id=self.started_by, connection=connection),
        #                   connection=connection) as counter:
        #    counter.counts_started += 1

        # async with Counter(await fetch_counter_record(discord_id=self.ruined_by, connection=connection),
        #                   connection=connection) as counter:
        #    counter.counts_ruined += 1
        #
        # Commented out because it seems like this is already done in the for-loop below

        query = """INSERT INTO counts (guild, channel, started_by, started_at, score, contributors, timed_out, duration, ruined_by)
                   VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9)
                   RETURNING id;
                """
        self.id = await connection.fetchval(query, self.guild, self.channel, self.started_by, self.started_at,
                                            self.score, self.contributors, self.timed_out,
                                            datetime.datetime.utcnow() - self.started_at, self.ruined_by)

        score_query = 'SELECT score FROM counts where id = $1'

        for discord_id, contribution in self.contributors.items():
            async with Counter(await fetch_counter_record(discord_id, connection), connection) as counter:
                finished_counts[self.channel]['last_counts'][counter.user_id] = counter.last_count
                finished_counts[self.channel]['best_counts'][counter.user_id] = counter.best_count

                counter.last_count = self.id
                counter.total_score += contribution
                counter.counts_participated += 1

                if counter.best_count is None:
                    counter.best_count = self.id
                else:
                    best_score = await connection.fetchval(score_query, counter.best_count)
                    if not best_score or best_score < self.score:
                        counter.best_count = self.id

                if counter.user_id == self.started_by:
                    counter.counts_started += 1

                if counter.user_id == self.ruined_by:
                    finished_counts[self.channel]['ruiner_best'] = counter.best_ruin

                    counter.counts_ruined += 1
                    if counter.best_ruin is None:
                        counter.best_ruin = self.id
                    else:
                        best_ruin_score = await connection.fetchval(score_query, counter.best_ruin)
                        if not best_ruin_score or best_ruin_score < self.score:
                            counter.best_ruin = self.id


class Count(commands.Cog):
    """Commands for the counting game."""

    def __init__(self, curator: bot.Curator):
        self.bot = curator

    async def check_count(self, message: discord.Message) -> bool:
        if is_count_channel(message.channel):
            if 'check' in message.content.lower():
                await message.add_reaction(
                    choice(('\u2705', '\u2611', '\u2714')) if message.channel.id in running_counts.keys()
                    else choice(('\u274c', '\u274e', '\u2716')))
            if message.channel.id not in running_counts.keys():
                return False
        else:
            return False

        c: Counting = running_counts[message.channel.id]

        if not c.attempt_count(message.author, message.content.split()[0]):
            finished_counts[message.channel.id] = {'count': running_counts[message.channel.id], 'last_counts': {},
                                                   'best_counts': {}}
            del (running_counts[message.channel.id])
            await message.channel.send(f'{message.author.mention} failed, and ruined the count for '
                                       f'{len(c.contributors.keys())} counters...\nThe count reached {c.score}.')
            await c.finish(self.bot, False, message.author)

            return False

        query = 'SELECT score FROM counts WHERE guild = $1 ORDER BY score DESC LIMIT 3;'
        top = [count['score'] for count in await self.bot.pool.fetch(query, message.guild.id)]
        for i, v in enumerate(top):
            if c.score == v + 1:
                await message.add_reaction(('\U0001F947', '\U0001F948', '\U0001F949')[i])
                break

        return True

    @commands.group(invoke_without_command=True)
    async def count(self, ctx: commands.Context):
        """Commands for the counting game."""
        await ctx.send(f'You need to supply a subcommand. Try `{ctx.prefix}help count`')

    @count.command(aliases=['begin'])
    async def start(self, ctx: commands.Context):
        """Use this to start a counting game!"""
        if is_count_channel(ctx.channel):
            query = 'SELECT score FROM counts WHERE guild = $1 ORDER BY score DESC LIMIT 3;'
            top = [count['score'] for count in await self.bot.pool.fetch(query, ctx.guild.id)]
            running_counts[ctx.channel.id] = Counting.temporary(guild=ctx.guild.id, channel=ctx.channel.id,
                                                                started_by=ctx.author.id,
                                                                started_at=datetime.datetime.utcnow(),
                                                                last_active_at=datetime.datetime.utcnow())
            await ctx.send(f'Count has been started. Try for top three: '
                           f'{formats.human_join([str(i) for i in top]) if top and len(top) == 3 else "good luck"}!')
        else:
            await ctx.send("You can't start a count outside of the count channel.")

    # noinspection PyUnreachableCode
    @count.command(aliases=['unfail', 'repair', 'revert'])
    async def restore(self, ctx: commands.Context):
        """Unfail a count.

        For if a count fails due to a bug.
        """
        return await ctx.send('Not working correctly yet.')
        if ctx.author.id in [261156531989512192, 314792415733088260, 183374539743428608,
                             341795028642824192] or await self.bot.is_owner(ctx.author):
            if ctx.channel.id in finished_counts.keys():
                running_counts[ctx.channel.id] = finished_counts[ctx.channel.id]['count']
                count = running_counts[ctx.channel.id]
                connection: asyncpg.pool = self.bot.pool

                for discord_id, contribution in count.contributors.items():
                    async with Counter(await fetch_counter_record(discord_id, connection), connection) as counter:
                        counter.last_count = finished_counts[ctx.channel.id]['last_counts'][counter.user_id]
                        counter.total_score -= contribution
                        counter.counts_participated -= 1
                        counter.best_count = finished_counts[ctx.channel.id]['best_counts'][counter.user_id]
                        if counter.user_id == count.started_by:
                            counter.counts_started -= 1
                        if counter.user_id == count.ruined_by:
                            counter.counts_ruined -= 1
                            counter.best_ruin = finished_counts[ctx.channel.id]['ruiner_best']

                query = 'DELETE FROM counts WHERE id = $1'
                await connection.fetchval(query, count.id)

                await ctx.send('Successful! Sorry for failing, this bug will be fixed soon.')
                await ctx.send(str(count.score))
            else:
                await ctx.send('There is no count data to reset to.')
        else:
            await ctx.send(
                'You cannot use this command, ask someone with the right permissions to use this, if the count failed by a bug.')

    @count.command()
    async def profile(self, ctx: commands.Context, *, user: Optional[discord.User]):
        """Get your counter profile.

        This holds information about your total score, the number of games you've contributed to, the number of games you have started, the number of games you ruined, and the IDs of you're best game, the highest count you ruined and the last game you participated in.
        """
        # The sentence above is not formatted into multiple lines because the line breaks get shown in the help message
        user: discord.User = user or ctx.author
        async with Counter(await fetch_counter_record(user.id, self.bot.pool), self.bot.pool) as counter:
            embed = discord.Embed(title=f'{user.name} - counting profile')
            embed.add_field(name='Total Score', value=f'{counter.total_score} counts')
            embed.add_field(name='Contributed in', value=f'{counter.counts_participated} rounds')
            embed.add_field(name='Rounds Started', value=f'{counter.counts_started} rounds')
            embed.add_field(name='Rounds Ruined', value=f'{counter.counts_ruined} rounds')
            embed.add_field(name='Best Round', value=f'Round {counter.best_count}')
            embed.add_field(name='Worst Fail', value=f'Round {counter.best_ruin}')
            embed.add_field(name='Last Count', value=f'Round {counter.last_count}')
            await ctx.send(embed=embed)

    @count.command()
    async def check(self, ctx: commands.Context):
        """Get a list of channels where a count is currently running."""
        found = False
        channels = ctx.guild.text_channels
        for channel in channels:
            if channel.id in running_counts.keys():
                await ctx.send(f'A count is running in {channel.mention}.')
                found = True
        if not found:
            await ctx.send('No count is running on this server.')

    @count.command()
    async def aliases(self, ctx: commands.Context, number: Optional[str]):
        """Get a list of number aliases.

        You can add a number as an argument to only get the aliases of that number.
        """
        try:
            await ctx.send('\n'.join(f'{emoji.emojize(f":{key}:")}: {formats.human_join(value)}'
                                     for key, value in number_aliases.items() if not number or number in value))
        except discord.HTTPException:
            await ctx.send(f'{number} has no aliases.')

    @count.command(aliases=['best', 'highscore', 'hiscore', 'top'])
    async def leaderboard(self, ctx: commands.Context):
        """Get the data of the top 5 highest counts."""
        async with ctx.typing():
            embed = discord.Embed(title='Count Leaderboard', description='Top 5 Highest Counts :slight_smile:')
            query = 'SELECT score, contributors FROM counts WHERE guild = $1 ORDER BY score DESC LIMIT 5;'
            rows = await self.bot.pool.fetch(query, ctx.guild.id)
            users = {
            }
            i = 0
            for row in rows:
                i += 1
                contributors = row['contributors']
                keys = contributors.keys()
                a = [f'**Score: {row["score"]}**']
                for user_id in keys:
                    if user_id in users.keys():
                        name = users[user_id]
                    else:
                        user = await self.bot.fetch_user(user_id)
                        name = user.name
                        users[user_id] = name

                    a.append(f'**{name}**: {contributors[user_id]}')

                embed.add_field(name=str(i), value='\n'.join(a), inline=False)

            await ctx.send(embed=embed)

    @count.command(aliases=['latest', 'newest', 'youngest'])
    async def last(self, ctx: commands.Context):
        """Get the data of the last count."""
        async with ctx.typing():
            embed = discord.Embed(title='Last Count', description='Last count data')
            query = 'SELECT score, contributors FROM counts WHERE guild = $1 ORDER BY started_at + duration DESC;'
            row = await self.bot.pool.fetchrow(query, ctx.guild.id)
            users = {
            }
            contributors = row[1]
            keys = contributors.keys()
            a = [f'**Score: {row[0]}**']
            for user_id in keys:
                if user_id in users.keys():
                    name = users[user_id]
                else:
                    user = await self.bot.fetch_user(user_id)
                    name = user.name
                    users[user_id] = name

                a.append(f'**{name}**: {contributors[user_id]}')

            embed.add_field(name='Last', value='\n'.join(a), inline=False)

            await ctx.send(embed=embed)

    @count.command(aliases=['current', 'active', 'atm'])
    async def running(self, ctx: commands.Context):
        """Get the data of all the currently running counts."""
        async with ctx.typing():
            embed = discord.Embed(title='Currently Running Counts',
                                  description='Data of the counts that are still running')
            guild_channels = ctx.guild.text_channels
            running_channels = []
            for guild_channel in guild_channels:
                if guild_channel.id in running_counts.keys():
                    running_channels.append(self.bot.get_channel(guild_channel.id))
            if len(running_channels) == 0:
                return await ctx.send('There are no counts running on this server.')
            for channel in running_channels:
                c: Counting = running_counts[channel.id]

                users = {
                }
                contributors = c.contributors
                keys = contributors.keys()
                a = [f'**Score thus far: {c.score}**']
                for user_id in keys:
                    if user_id in users.keys():
                        name = users[user_id]
                    else:
                        user = await self.bot.fetch_user(user_id)
                        name = user.name
                        users[user_id] = name

                    a.append(f'**{name}**: {contributors[user_id]}')

                embed.add_field(name=f'Count in {channel.name}', value='\n'.join(a), inline=False)

            await ctx.send(embed=embed)

    @count.command(aliases=['try'])
    async def parse(self, ctx: commands.Context, number: str):
        """Check if a number alias is working."""
        parse = parsed(number)
        roman = from_roman(number) if roman_re.fullmatch(number) else None
        binary = str(int(number, 2)) if binary_re.fullmatch(number) else None

        if roman:
            parse.append(roman)

        if binary:
            parse.append(binary)

        if parse:
            await ctx.send(formats.human_join(sorted(parse), final='and'))
        else:
            await ctx.send('Could not parse that.')

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and message.channel.type == discord.ChannelType.text:
            await self.check_count(message)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id in running_counts.keys():
            if message.id == message.channel.last_message_id:
                await message.channel.send(f'{running_counts[message.channel.id].score}, '
                                           f'shame on {message.author.mention} for deleting their count!')


def setup(curator: bot.Curator):
    curator.add_cog(Count(curator))


"""def teardown(curator: bot.Curator):
    \"""Code being executed upon unloading of the cog.\"""
    for channel_id in running_counts.keys():  # Let counters know the count is silently dying
        counters = len(running_counts[channel_id]['contributors'])
        s = 's' if counters > 1 else ''
        await curator.get_channel(channel_id).send(
            f'Sorry, {f"counter{s}, " if counters >= 1 else ""}due to this module being un-/reloaded, the count that '
            f'was running here is now down. No data of it has been saved to the database of counts or '
            f'{f"your counter profile{s}" if counters >= 1 else "the counter profile of the starter"}.')"""
