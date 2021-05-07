import datetime
from collections import OrderedDict
from typing import Optional, List, Dict
import re

import asyncpg
import discord
from discord.ext import commands
from bot import Curator
import emoji
import unicodedata
from random import choice

import bot
from .utils import db
from .utils.checks import owner_or_guild_permissions
from .utils.formats import human_join


class Counts(db.Table):
    id = db.PrimaryKeyColumn()

    guild = db.Column(db.Integer(big=True))
    channel = db.Column(db.Integer(big=True))

    started_by = db.Column(db.Integer(big=True))
    started_at = db.Column(db.Datetime, default="now() at time zone 'utc'")

    score = db.Column(db.Integer, default='0')
    contributors = db.Column(db.JSON, default="'{}'::jsonb")

    timed_out = db.Column(db.Boolean, default="FALSE")
    duration = db.Column(db.Interval)
    ruined_by = db.Column(db.Integer(big=True))

    type = db.Column(db.String, default="normal")


class Counters(db.Table):
    user_id = db.Column(db.Integer(big=True), primary_key=True)
    last_count = db.Column(db.ForeignKey(table='counts', column='id', sql_type=db.Integer()))
    best_count = db.Column(db.ForeignKey(table='counts', column='id', sql_type=db.Integer()))
    best_ruin = db.Column(db.ForeignKey(table='counts', column='id', sql_type=db.Integer()))
    total_score = db.Column(db.Integer, default=0)
    counts_participated = db.Column(db.Integer, default=0)
    counts_ruined = db.Column(db.Integer, default=0)
    counts_started = db.Column(db.Integer, default=0)


number_aliases = {  # Keycap numbers (except keycap_10) and infinity are handled separately; these names are the Unicode names of symbols, as retrieved by unicodedata.name()
    'DEGREE SIGN': ['0'],
    'WHITE CIRCLE': ['0'],
    'REGIONAL INDICATOR SYMBOL LETTER O': ['0'],
    'HEAVY LARGE CIRCLE': ['0'],
    'NO ENTRY SIGN': ['0'],
    'RADIO BUTTON': ['0'],
    'LATIN SMALL LETTER O': ['0'],
    'LATIN CAPITAL LETTER O': ['0'],
    'ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS': ['0'],
    'CLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS': ['0'],
    'PERCENT SIGN': ['0', '00'],
    'PER MILLE SIGN': ['0', '00', '000'],
    'PER TEN THOUSAND SIGN': ['0', '000', '0000'],
    'Z NOTATION TYPE COLON': ['00'],
    'CLOCK FACE ONE OCLOCK': ['1', '13'],
    'REGIONAL INDICATOR SYMBOL LETTER I': ['1', 'I'],
    'FIRST PLACE MEDAL': ['1'],
    'LATIN SMALL LETTER I': ['1'],
    'LATIN CAPITAL LETTER I': ['1', 'I'],
    'SUPERSCRIPT TWO': ['2'],
    'CLOCK FACE TWO OCLOCK': ['2', '14'],
    'SECOND PLACE MEDAL': ['2'],
    'SUPERSCRIPT THREE': ['3'],
    'CLOCK FACE THREE OCLOCK': ['3', '15'],
    'ALARM CLOCK': ['3', '15'],
    'THIRD PLACE MEDAL': ['3'],
    'EVERGREEN TREE': ['3'],
    'DECIDUOUS TREE': ['3'],
    'PALM TREE': ['3'],
    'CHRISTMAS TREE': ['3'],
    'CACTUS': ['3'],
    'CLOCK FACE FOUR OCLOCK': ['4', '16'],
    'FOUR LEAF CLOVER': ['4'],
    'CLOCK FACE FIVE OCLOCK': ['5', '17'],
    'WHITE MEDIUM STAR': ['5'],
    'WHITE STAR': ['5'],
    'CLOCK FACE SIX OCLOCK': ['6', '18'],
    'SIX POINTED STAR WITH MIDDLE DOT': ['6'],
    'CLOCK FACE SEVEN OCLOCK': ['7', '19'],
    'CLOCK FACE EIGHT OCLOCK': ['8', '20'],
    'BILLIARDS': ['8'],
    'INFINITY': ['8'],
    'CLOCK FACE NINE OCLOCK': ['9', '21'],
    'MANTELPIECE CLOCK': ['9', '21'],
    'KEYCAP TEN': ['10'],
    'CLOCK FACE TEN OCLOCK': ['10', '22'],
    'CLOCK FACE ELEVEN OCLOCK': ['11', '23'],
    'CLOCK FACE TWELVE OCLOCK': ['12', '0', '24'],
    #'RINGED PLANET': ['42'],  # unicodedata seems to somehow not know this character anymore
    'MILKY WAY': ['42'],
    'OK HAND SIGN': ['69'],
    'CANCER': ['69'],
    'HUNDRED POINTS SYMBOL': ['100', '00'],
    'INPUT SYMBOL FOR NUMBERS': ['1', '2', '3', '4'],
    'IDEOGRAPHIC NUMBER ZERO': ['0'],
    'CJK UNIFIED IDEOGRAPH-96F6': ['0'],
    'REGIONAL INDICATOR SYMBOL LETTER A': ['A'],
    'NEGATIVE SQUARED AB': ['AB'],
    'REGIONAL INDICATOR SYMBOL LETTER B': ['B'],
    'REGIONAL INDICATOR SYMBOL LETTER C': ['C'],
    'COPYRIGHT SIGN': ['C'],
    'WATER WAVE': ['C'],
    'REGIONAL INDICATOR SYMBOL LETTER D': ['D'],
    'REGIONAL INDICATOR SYMBOL LETTER E': ['E'],
    'REGIONAL INDICATOR SYMBOL LETTER F': ['F'],
    'REGIONAL INDICATOR SYMBOL LETTER V': ['V'],
    'REGIONAL INDICATOR SYMBOL LETTER X': ['X'],
    'CROSS MARK': ['X'],
    'MULTIPLICATION SIGN': ['X'],
    'NEGATIVE SQUARED CROSS MARK': ['X'],
    'TWISTED RIGHTWARDS ARROWS': ['X'],
    'REGIONAL INDICATOR SYMBOL LETTER L': ['L'],
    'REGIONAL INDICATOR SYMBOL LETTER M': ['M'],
    'CIRCLED LATIN CAPITAL LETTER M': ['M'],
    'SQUARED CL': ['CL'],
    'ROMAN NUMERAL ONE': ['I', '1'],
    'ROMAN NUMERAL TWO': ['II', '11', '2'],
    'ROMAN NUMERAL THREE': ['III', '111', '3'],
    'ROMAN NUMERAL FOUR': ['IV', '4'],
    'ROMAN NUMERAL FIVE': ['V', '5'],
    'ROMAN NUMERAL SIX': ['VI', '6'],
    'ROMAN NUMERAL SEVEN': ['VII', '7'],
    'ROMAN NUMERAL EIGHT': ['VIII', '8'],
    'ROMAN NUMERAL NINE': ['IX', '9'],
    'ROMAN NUMERAL TEN': ['X', '10'],
    'ROMAN NUMERAL ELEVEN': ['XI', '11'],
    'ROMAN NUMERAL TWELVE': ['XII', '12'],
    'ROMAN NUMERAL FIFTY': ['L', '50'],
    'ROMAN NUMERAL ONE HUNDRED': ['C', '100'],
    'ROMAN NUMERAL FIVE HUNDRED': ['D', '500'],
    'ROMAN NUMERAL ONE THOUSAND': ['M', '1000'],
    'SMALL ROMAN NUMERAL ONE': ['I', '1'],
    'SMALL ROMAN NUMERAL TWO': ['II', '11', '2'],
    'SMALL ROMAN NUMERAL THREE': ['III', '111', '3'],
    'SMALL ROMAN NUMERAL FOUR': ['IV', '4'],
    'SMALL ROMAN NUMERAL FIVE': ['V', '5'],
    'SMALL ROMAN NUMERAL SIX': ['VI', '6'],
    'SMALL ROMAN NUMERAL SEVEN': ['VII', '7'],
    'SMALL ROMAN NUMERAL EIGHT': ['VIII', '8'],
    'SMALL ROMAN NUMERAL NINE': ['IX', '9'],
    'SMALL ROMAN NUMERAL TEN': ['X', '10'],
    'SMALL ROMAN NUMERAL ELEVEN': ['XI', '11'],
    'SMALL ROMAN NUMERAL TWELVE': ['XII', '12'],
    'SMALL ROMAN NUMERAL FIFTY': ['L', '50'],
    'SMALL ROMAN NUMERAL ONE HUNDRED': ['C', '100'],
    'SMALL ROMAN NUMERAL FIVE HUNDRED': ['D', '500'],
    'SMALL ROMAN NUMERAL ONE THOUSAND': ['M', '1000'],
    'FRACTION NUMERATOR ONE': ['1'],
    'VULGAR FRACTION ONE HALF': ['1', '2', '12'],
    'VULGAR FRACTION ONE THIRD': ['1', '3', '13'],
    'VULGAR FRACTION ONE QUARTER': ['1', '4', '14'],
    'VULGAR FRACTION ONE FIFTH': ['1', '5', '15'],
    'VULGAR FRACTION ONE SIXTH': ['1', '6', '16'],
    'VULGAR FRACTION ONE SEVENTH': ['1', '7', '17'],
    'VULGAR FRACTION ONE EIGHTH': ['1', '8', '18'],
    'VULGAR FRACTION ONE NINTH': ['1', '9', '19'],
    'VULGAR FRACTION ONE TENTH': ['1', '10', '110'],
    'VULGAR FRACTION TWO FIFTHS': ['2', '5', '25'],
    'VULGAR FRACTION TWO THIRDS': ['2', '3', '23'],
    'VULGAR FRACTION THREE QUARTERS': ['3', '4', '34'],
    'VULGAR FRACTION THREE FIFTHS': ['3', '5', '35'],
    'VULGAR FRACTION THREE EIGHTHS': ['3', '8', '38'],
    'VULGAR FRACTION FOUR FIFTHS': ['4', '5', '45'],
    'VULGAR FRACTION FIVE SIXTHS': ['5', '6', '56'],
    'VULGAR FRACTION FIVE EIGHTHS': ['5', '8', '58'],
    'VULGAR FRACTION SEVEN EIGHTHS': ['7', '8', '78'],
    'CARE OF': ['C', '0'],
    'ADDRESSED TO THE SUBJECT': ['A'],
    'AKTIESELSKAB': ['A']
}

special_aliases = {  # These are all followed by "VARIATION SELECTOR-16" (0xfe0f)
    'NEGATIVE SQUARED LATIN CAPITAL LETTER O': ['0'],
    'SHAMROCK': ['3'],
    'STAR OF DAVID': ['6'],
    'WHEEL OF DHARMA': ['6'],
    'BLACK SUN WITH RAYS': ['8'],
    'PERMANENT PAPER SIGN': ['8'],
    'EIGHT SPOKED ASTERISK': ['8'],
    'SPARKLE': ['8'],
    'NEGATIVE SQUARED LATIN CAPITAL LETTER A': ['A'],
    'NEGATIVE SQUARED LATIN CAPITAL LETTER B': ['B'],
    'COPYRIGHT SIGN': ['C'],
    'SKULL AND CROSSBONES': ['X']
}

roman_re = re.compile('^(?=[MDCLXVI])M*(C[MD]|D?C{0,3})(X[CL]|L?X{0,3})(I[XV]|V?I{0,3})$')
binary_re = re.compile('^[01]+$')
hex_re = re.compile('^[\dA-F]+$')


def parsed(number: str) -> List[int]:
    if number.startswith('#'):
        desymboled = parse_symbols(number[1:])
        return [int(result, 16) for result in desymboled if hex_re.fullmatch(result.upper())]

    desymboled = parse_symbols(number)
    results = [int(result) for result in desymboled if result.isnumeric()]
    results += [int(result, 2) for result in desymboled if binary_re.fullmatch(result)]
    results += [from_roman(result) for result in desymboled if roman_re.fullmatch(result)]
    return list(dict.fromkeys(results))  # Removes duplicates


def parse_symbols(number: str) -> List[str]:
    results = ['']

    def add_parsed(numbers: list):
        nonlocal results
        new_results = []
        for n in numbers:
            for result in results:
                s = result + n
                new_results.append(s)
        results = new_results

    i = 0
    while i < len(number):
        digit = number[i]
        if digit.isdigit():
            add_parsed([digit])
            if i < len(number) - 2 and number[i+2] == '\u20e3':  # ⃣ , used for keycap numbers, which are very weird
                i += 2
        elif unicodedata.name(digit) in special_aliases.keys() and i < len(number) - 1 and number[i + 1] == '\ufe0f':  # VARIATION SELECTOR-16
            add_parsed(special_aliases[unicodedata.name(digit)])
            i += 1
        elif unicodedata.name(digit) in number_aliases.keys():
            add_parsed(number_aliases[unicodedata.name(digit)])
        elif False and digit == '*':  # Asterisk exception  # Disabled due to Discord handling asterisks in messages, this also applies to the keycap version
            if i < len(number) - 2 and number[i + 2] == '\u20e3':  # Keycap asterisk
                add_parsed(['6'])
                i += 2
            else:  # Normal asterisk
                add_parsed(['5'])
        else:
            add_parsed([digit])
        i += 1
    return results


def write_roman(num):  # from https://stackoverflow.com/questions/28777219/basic-program-to-convert-integer-to-roman-numerals/28777781
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


def from_roman(num):  # from https://stackoverflow.com/questions/19308177/converting-roman-numerals-to-integers-in-python
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


def is_count_channel(configs, channel: discord.TextChannel) -> bool:
    return ('count' in channel.name.lower() and not configs[channel.guild.id].count_channels) or channel in configs[channel.guild.id].count_channels


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
        if counter.id != self.last_counter and (str(target) == count or target in parsed(count)):  # str(target) == count is added for performance; means it doesn't need to go through the parsing function when the count is just normal numbers
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
                # finished_counts[self.channel]['last_counts'][counter.user_id] = counter.last_count
                # finished_counts[self.channel]['best_counts'][counter.user_id] = counter.best_count

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
                    # finished_counts[self.channel]['ruiner_best'] = counter.best_ruin

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
        self.running_counts: Dict[int, Counting] = {}

    async def check_count(self, message: discord.Message) -> bool:
        if is_count_channel(self.bot.server_configs, message.channel):
            if 'check' in message.content.lower():
                await message.add_reaction(
                    choice(('\u2705', '\u2611', '\u2714')) if message.channel.id in self.running_counts.keys()
                    else choice(('\u274c', '\u274e', '\u2716')))
            if message.channel.id not in self.running_counts.keys():
                return False
        else:
            return False

        c: Counting = self.running_counts[message.channel.id]

        if not c.attempt_count(message.author, message.content.split()[0]):
            del (self.running_counts[message.channel.id])
            await message.channel.send(f'{message.author.mention} failed, and ruined the count for '
                                       f'{len(c.contributors.keys())} counters...\nThe count reached {c.score}.')
            await c.finish(self.bot, False, message.author)

            return False

        if '69' in str(c.score):
            await message.add_reaction('👌🏻')
        if c.score % 100 == 0:
            await message.add_reaction('💯')
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

    @count.command(aliases=['begin', 'initiate', 'instantiate'])
    async def start(self, ctx: commands.Context):
        """Use this to start a counting game!"""
        if is_count_channel(self.bot.server_configs, ctx.channel):
            query = 'SELECT score FROM counts WHERE guild = $1 ORDER BY score DESC LIMIT 3;'
            top = [count['score'] for count in await self.bot.pool.fetch(query, ctx.guild.id)]
            self.running_counts[ctx.channel.id] = Counting.temporary(guild=ctx.guild.id, channel=ctx.channel.id,
                                                                started_by=ctx.author.id,
                                                                started_at=datetime.datetime.utcnow(),
                                                                last_active_at=datetime.datetime.utcnow())
            await ctx.send(f'Count has been started. Try for top three: '
                           f'{human_join([str(i) for i in top]) if top and len(top) == 3 else "good luck"}!')
        else:
            await ctx.send("You can't start a count outside of a count channel.")

    @count.group(aliases=['channel'], invoke_without_command=True)
    async def channels(self, ctx: commands.Context):
        """Commands to set/remove counting channels.

        Counting channels are channels where counts can be played.
        If there are no channels set, any channel with "count" in the name is available.
        """
        await ctx.send(f'The counting game is currently available in '
                       f'{human_join([channel.mention for channel in ctx.guild.text_channels if is_count_channel(self.bot.server_configs, channel)], final="and")}.\n'
                       f'{f"You can create your own list with `{ctx.prefix}count channels add/remove`." if not self.bot.server_configs[ctx.guild.id].count_channels else f"You can remove channels with `{ctx.prefix}count channels remove`."}')

    @owner_or_guild_permissions(manage_channels=True)
    @channels.command(name='add', aliases=['set', 'include'])
    async def add_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Add or set a counting channel.

        Provide a channel mention, ID or name.
        If a counting channel is set, channels with "count" in their name won't be able to be used anymore.
        """
        if channel in self.bot.server_configs[ctx.guild.id].count_channels:
            return await ctx.send('This is already a channel on the list.')

        query = 'UPDATE serverconfigs SET count_channels = array_append(count_channels, $1) WHERE guild = $2;'
        await self.bot.pool.fetchval(query, channel.id, ctx.guild.id)
        self.bot.server_configs[ctx.guild.id].count_channels.append(channel)
        await ctx.send(f'Successfully added {channel.mention}.')

    @owner_or_guild_permissions(manage_channels=True)
    @channels.command(name='remove', aliases=['delete'])
    async def remove_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Remove a counting channel.

        Provide a channel mention, ID or name.
        If there are no counting channels left, every channel with "count" in the name will be available.
        """
        if channel not in self.bot.server_configs[ctx.guild.id].count_channels:
            return await ctx.send('The channel was not found in the list.')

        query = 'UPDATE serverconfigs SET count_channels = array_remove(count_channels, $1) where guild = $2;'
        await self.bot.pool.execute(query, channel.id, ctx.guild.id)
        self.bot.server_configs[ctx.guild.id].count_channels.remove(channel)
        await ctx.send(f'Successfully removed {channel.mention}.')

    @count.command()
    async def profile(self, ctx: commands.Context, *, user: Optional[discord.User]):
        """Get your counter profile.

        This holds information about your total score, the number of games you've contributed to, the number of games you have started, the number of games you ruined, and the IDs of you're best game, the highest count you ruined and the last game you participated in.
        """  # The sentence above is not formatted into multiple lines because the line breaks get shown in the help message
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
            if channel.id in self.running_counts.keys():
                await ctx.send(f'A count is running in {channel.mention}.')
                found = True
        if not found:
            await ctx.send('No count is running on this server.')

    @count.command(aliases=['alternatives', 'replacements'])
    async def aliases(self, ctx: commands.Context, number: Optional[str]):
        """Get a list of number aliases.

        Number aliases can be used in place of digits in the counting game.
        Some aliases can parse into multiple different digits and some can replace groups of digits instead of single ones.
        You can add a number as an argument to only get the aliases of that number.
        """
        try:
            await ctx.send('\n'.join(x for x in [f'{i}️⃣: {i}' for i in range(10)] + list(f'{unicodedata.lookup(name)}: {human_join(value)}'
                                     for name, value in number_aliases.items()) + list(f'{unicodedata.lookup(name)}\ufe0f: {human_join(value)}'
                                     for name, value in special_aliases.items())# + [':asterisk:: 6', '*: 5']  # Asterisks disabled due to Discord handling asterisks in messages, this also applies to the keycap version
                                     if not number or number in x))
        except discord.HTTPException:  # Trying to send an empty string
            await ctx.send(f'{number} has no aliases.')
        #except KeyError:
        #    await ctx.send(f'There\'s a problem with my internal list of aliases, please contact RJTimmerman#9465 or Ruukas#9050 if this perists.')

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

    @count.command(aliases=['current', 'active', 'atm', 'status'])
    async def running(self, ctx: commands.Context):
        """Get the data of all the currently running counts."""
        async with ctx.typing():
            embed = discord.Embed(title='Currently Running Counts',
                                  description='Data of the counts that are still running')
            guild_channels = ctx.guild.text_channels
            running_channels = []
            for guild_channel in guild_channels:
                if guild_channel.id in self.running_counts.keys():
                    running_channels.append(self.bot.get_channel(guild_channel.id))
            if len(running_channels) == 0:
                return await ctx.send('There are no counts running on this server.')
            for channel in running_channels:
                c: Counting = self.running_counts[channel.id]

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

        if parse:
            await ctx.send(human_join([str(i) for i in sorted([int(i) for i in parse])]))
        else:
            await ctx.send('Could not parse that.')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.author.bot and message.channel.type == discord.ChannelType.text:
            await self.check_count(message)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.channel.id in self.running_counts.keys() and message.id == message.channel.last_message_id:
            await message.channel.send(f'**{self.running_counts[message.channel.id].score}**, '
                                       f'shame on {message.author.mention} for deleting their count!')

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.channel.id in self.running_counts.keys() and before.id == before.channel.last_message_id \
                and self.running_counts[before.channel.id].score not in parsed(after.content.split()[0]):
            await after.channel.send(f'**{self.running_counts[before.channel.id].score}**, '
                              f'shame on {after.author.mention} for editing away their count!')


def setup(curator: bot.Curator):
    curator.add_cog(Count(curator))


"""def teardown(curator: bot.Curator):
    \"""Code being executed upon unloading of the cog.\"""
    for channel_id in self.running_counts.keys():  # Let counters know the count is silently dying
        counters = len(self.running_counts[channel_id]['contributors'])
        s = 's' if counters > 1 else ''
        await curator.get_channel(channel_id).send(
            f'Sorry, {f"counter{s}, " if counters >= 1 else ""}due to this module being un-/reloaded, the count that '
            f'was running here is now down. No data of it has been saved to the database of counts or '
            f'{f"your counter profile{s}" if counters >= 1 else "the counter profile of the starter"}.')"""
