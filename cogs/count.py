import datetime
import itertools
from typing import Optional

import asyncpg
import discord
from discord.ext import commands
import emoji

import bot
from .utils import db
from .utils import formats


class Counts(db.Table):
    id = db.PrimaryKeyColumn()

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
    ':keycap_0:': ['0'],
    ':regional_indicator_o:': ['0'],
    ':O_button_(blood_type):': ['0'],
    ':heavy_large_circle:': ['0'],
    ':keycap_1:': ['1'],
    ':regional_indicator_i:': ['1'],
    ':1st_place_medal:': ['1'],
    ':keycap_2:': ['2'],
    ':2nd_place_medal:': ['2'],
    ':keycap_3:': ['3'],
    ':3rd_place_medal:': ['3'],
    ':evergreen_tree:': ['3'],
    ':deciduous_tree:': ['3'],
    ':palm_tree:': ['3'],
    ':christmas_tree:': ['3'],
    ':cactus:': ['3'],
    ':shamrock:': ['3'],
    ':keycap_4:': ['4'],
    ':four_leaf_clover:': ['4'],
    ':keycap_5:': ['5'],
    ':keycap_6:': ['6'],
    ':keycap_7:': ['7'],
    ':keycap_8:': ['8'],
    ':pool_8_ball:': ['8'],
    ':keycap_9:': ['9'],
    ':keycap_10:': ['10'],
    ':ringed_planet:': ['42'],
    ':OK_hand:': ['69'],
    ':cancer:': ['69'],
    ':hundred_points:': ['100', '00'],
    ':input_numbers:': ['1234']
}

running_counts = {}


def parsed(number: str) -> list:
    number = emoji.emojize(number)
    plist = [c for c in number]
    emojis = [(i['emoji'], i['location']) for i in emoji.emoji_lis(number)]
    for e, i in emojis:
        plist[i] = number_aliases[emoji.demojize(e)]

    return [''.join(i) for i in itertools.product(*plist)]


def is_number(number: str, to_check: str) -> bool:
    return number in parsed(to_check)


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


async def deleted_count(message):
    if message.id == message.channel.last_message_id:
        await message.channel.send(f'{running_counts[message.channel.id].score}, shame on {message.author.mention} for deleting their count!')


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
    __slots__ = (
        'id', 'started_by', 'started_at', 'score', 'contributors', 'last_active_at', 'last_counter', 'timed_out',
        'duration', 'ruined_by')

    def __init__(self, *, record):
        self.id = record['id']
        self.started_by = record['started_by']
        self.started_at = record['started_at']
        self.score = record['score']
        self.contributors = record['contributors']
        self.last_active_at = record['last_active_at']
        self.last_counter = record['last_counter']
        self.timed_out = False
        self.ruined_by = None

    @classmethod
    def temporary(cls, *, started_by, started_at=datetime.datetime.utcnow(), score=0, contributors=None,
                  last_active_at=datetime.datetime.utcnow(), last_counter=None):
        if contributors is None:
            contributors = {}
        pseudo = {
            'id': None,
            'started_by': started_by,
            'started_at': started_at,
            'score': score,
            'contributors': contributors,
            'last_active_at': last_active_at,
            'last_counter': last_counter
        }
        return cls(record=pseudo)

    def attempt_count(self, counter: discord.User, count: str) -> bool:
        if self.is_next(count) and counter.id != self.last_counter:
            self.last_active_at = datetime.datetime.utcnow()
            self.last_counter = counter.id
            self.score += 1
            if counter.id not in self.contributors.keys():
                self.contributors[counter.id] = 1
            else:
                self.contributors[counter.id] += 1
            return True
        return False

    def is_next(self, message: str):
        return is_number(str(self.score + 1), message.split()[0])

    async def finish(self, curator: bot.Curator, timed_out: bool, ruined_by: discord.User):
        connection: asyncpg.pool = curator.pool
        self.timed_out = timed_out
        self.ruined_by = ruined_by.id

        async with Counter(await fetch_counter_record(discord_id=self.started_by, connection=connection),
                           connection=connection) as counter:
            counter.counts_started += 1

        async with Counter(await fetch_counter_record(discord_id=self.ruined_by, connection=connection),
                           connection=connection) as counter:
            counter.counts_ruined += 1

        query = """INSERT INTO counts (started_by, started_at, score, contributors, timed_out, duration, ruined_by )
                   VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7)
                   RETURNING id;
                """
        self.id = await connection.fetchval(query, self.started_by, self.started_at, self.score, self.contributors,
                                            self.timed_out, datetime.datetime.utcnow() - self.started_at,
                                            self.ruined_by)

        score_query = 'SELECT score FROM counts where id=$1'

        for discord_id, contribution in self.contributors.items():
            async with Counter(await fetch_counter_record(discord_id, connection), connection) as counter:
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
                    counter.counts_ruined += 1
                    if counter.best_ruin is None:
                        counter.best_ruin = self.id
                    else:
                        best_ruin_score = await connection.fetchval(score_query, counter.best_ruin)
                        if not best_ruin_score or best_ruin_score < self.score:
                            counter.best_ruin = self.id
        del self


class Count(commands.Cog):
    def __init__(self, curator: bot.Curator):
        self.bot = curator
        self.count_channel = None
        self.top = []

    async def check_count(self, message: discord.Message) -> bool:
        if is_count_channel(message.channel):
            if 'check' in message.content.lower():
                await message.add_reaction('\u2705' if message.channel.id in running_counts.keys() else '\u274c')
            if not message.channel.id in running_counts.keys():
                return False
        else:
            return False

        c: Counting = running_counts[message.channel.id]

        if not c.attempt_count(message.author, message.content.split()[0]):
            del(running_counts[message.channel.id])
            self.top.append(c.score)
            self.top = sorted(self.top)[3:0:-1]
            await message.channel.send(f'{message.author.mention} failed, and ruined the count for '
                                       f'{len(c.contributors.keys())} counters...\nThe count reached {c.score}.')
            await c.finish(self.bot, False, message.author)

            return False

        for i, v in enumerate(self.top):
            if c.score == v + 1:
                await message.add_reaction(('\U0001F947', '\U0001F948', '\U0001F949')[i])
                break

        return True

    @commands.group(invoke_without_command=True)
    async def count(self, ctx: commands.Context):
        await ctx.send(f'You need to supply a subcommand. Try {ctx.prefix}help count')

    @count.command()
    async def start(self, ctx: commands.Context):
        if is_count_channel(ctx.channel):
            if not self.top or len(self.top) < 3:
                query = 'SELECT score FROM counts ORDER BY score DESC LIMIT 3;'
                self.top = [count['score'] for count in await self.bot.pool.fetch(query)]
            running_counts[ctx.channel.id] = Counting.temporary(started_by=ctx.author.id)
            await ctx.send(
                f'Count has been started. Try for top three: {formats.human_join([str(i) for i in self.top]) if self.top and len(self.top) == 3 else "good luck"}!')
        else:
            await ctx.send("You can't start a count outside of the count channel.")

    @count.command()
    async def profile(self, ctx: commands.Context, *, user: Optional[discord.User]):
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
        channels = ctx.guild.text_channels
        for channel in channels:
            if channel.id in running_counts.keys():
                await ctx.send('A count is running.')
                return
        await ctx.send('No count is running.')
        return

    @count.command()
    async def aliases(self, ctx: commands.Context):
        await ctx.send('\n'.join(f'{emoji.emojize(key, use_aliases=True)}: {formats.human_join(value)}' for key, value in number_aliases.items()))

    @count.command(aliases=['best', 'highscore', 'hiscore', 'top'])
    async def leaderboard(self, ctx: commands.Context):
        embed = discord.Embed(title='Count Leaderboard', description='Top 5 Highest Counts :slight_smile:')
        query = 'SELECT score, contributors FROM counts ORDER BY score DESC LIMIT 5;'
        rows = await self.bot.pool.fetch(query)
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
                    member = await ctx.guild.fetch_member(user_id)
                    name = member.name
                    users[user_id] = name

                a.append(f'**{name}**: {contributors[user_id]}')

            embed.add_field(name=str(i), value='\n'.join(a), inline=False)

        await ctx.send(embed=embed)

    @count.command()
    async def last(self, ctx: commands.Context):
        embed = discord.Embed(title='Last Count', description='Last count data')
        query = 'SELECT score, contributors, started_at FROM counts ORDER BY started_at DESC LIMIT 1;'
        rows = await self.bot.pool.fetch(query)
        users = {
        }
        i = 1
        for row in rows:
            i += 1
            contributors = row['contributors']
            keys = contributors.keys()
            a = [f'**Score: {row["score"]}**']
            for user_id in keys:
                if user_id in users.keys():
                    name = users[user_id]
                else:
                    member = await ctx.guild.fetch_member(user_id)
                    name = member.name
                    users[user_id] = name

                a.append(f'**{name}**: {contributors[user_id]}')

                embed.add_field(name=str(i), value='\n'.join(a), inline=False)

    @count.command()
    async def parse(self, ctx: commands.Context, number: str):
        parse = parsed(number)
        if parse:
            await ctx.send(str(parse))
        else:
            await ctx.send("Could not parse that.")
    
    #@count.command()
    #async def role(self, ctx: commands.Context, action):
        #if action == 'get':
            #code
        #elif action == 'remove':
            #code
        #else:
            #await ctx.send('Provide a valid argument: \'get\' or \'remove\'')


def setup(curator: bot.Curator):
    curator.add_cog(Count(curator))
