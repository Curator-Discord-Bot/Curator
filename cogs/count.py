import datetime
from typing import Optional

import asyncpg
import discord
from discord.ext import commands
import json
from os import path
import emoji

import bot
from . import profile
from .utils import db


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
    ':keycap_1:': ['1'],
    ':1st_place_medal:': ['1'],
    ':keycap_2:': ['2'],
    ':2nd_place_medal:': ['1'],
    ':keycap_3:': ['3'],
    ':3rd_place_medal:': ['1'],
    ':keycap_4:': ['4'],
    ':keycap_5:': ['5'],
    ':keycap_6:': ['6'],
    ':keycap_7:': ['7'],
    ':keycap_8:': ['8'],
    ':keycap_9:': ['9'],
    ':keycap_10:': ['10'],
    ':pool_8_ball:': ['8'],
    ':OK_hand:': ['69'],
    ':hundred_points:': ['100', '00'],
    ':input_numbers:': ['1234']
}


def parsed(number: str) -> str:
    s = emoji.demojize(number)
    for key in number_aliases.keys():
        for i in range(s.count(key)):
            s = ', '.join([s.replace(key, alias, 1) for alias in number_aliases[key]])
    s = ', '.join(set([i for i in s.split(', ') if i.isdigit()]))
    if len(s) < 1:
        return 'invalid'
    return s


def is_number(number: str, to_check: str) -> bool:
    return parsed(to_check) == number


class CounterProfile:
    __slots__ = (
        'user_id', 'last_count', 'best_count', 'best_ruin', 'total_score', 'counts_participated', 'counts_ruined',
        'counts_started')

    def __init__(self, *, record):
        self.user_id = record['user_id']
        self.last_count = record['last_count']
        self.best_count = record['best_count']
        self.best_ruin = record['best_ruin']
        self.total_score = record['total_score']
        self.counts_participated = record['counts_participated']
        self.counts_ruined = record['counts_ruined']
        self.counts_started = record['counts_started']

    @classmethod
    def temporary(cls):
        pseudo = {
            'user_id': None,
            'last_count': None,
            'best_count': None,
            'best_ruin': None,
            'total_score': 0,
            'counts_participated': 0,
            'counts_ruined': 0,
            'counts_started': 0
        }
        return cls(record=pseudo)

    def __eq__(self, other):
        try:
            return self.user_id == other.user_id
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.user_id)

    def __repr__(self):
        return f'<CounterProfile discord_id={self.user_id}>'


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

        if 'Count' in curator.cogs:
            c_cog = curator.cogs['Count']
            await c_cog.get_profile_with_create(self.started_by)
            await c_cog.get_profile_with_create(self.ruined_by)

        query = """INSERT INTO counts (started_by, started_at, score, contributors, timed_out, duration, ruined_by )
                   VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7)
                   RETURNING id;
                """
        row = await connection.fetchrow(query, self.started_by, self.started_at, self.score, self.contributors,
                                        self.timed_out, datetime.datetime.utcnow() - self.started_at, self.ruined_by)
        self.id = row[0]

        score_query = 'SELECT score FROM counts where id=$1'

        if 'Count' in curator.cogs:
            c_cog = curator.cogs['Count']
            for key in self.contributors.keys():
                counter: CounterProfile = await c_cog.get_profile_with_create(key)
                contribution = self.contributors[key]
                updates = ['last_count=' + str(self.id), 'total_score=' + str(counter.total_score + contribution),
                           'counts_participated=' + str(counter.counts_participated + 1)]

                if counter.best_count is None:
                    updates.append('best_count=' + str(self.id))
                else:
                    best_score = await connection.execute(score_query, counter.best_count)
                    if best_score is None or int(best_score.split(' ')[1]) < self.score:
                        updates.append('best_count=' + str(self.id))

                if self.started_by == key:
                    updates.append('counts_started=' + str(counter.counts_started + 1))

                if self.ruined_by == key:
                    updates.append('counts_ruined=' + str(counter.counts_ruined + 1))
                    if counter.best_ruin is None:
                        updates.append('best_ruin=' + str(self.id))
                    else:
                        best_ruin_score = await connection.execute(score_query, counter.best_ruin)
                        if best_ruin_score is None or int(best_ruin_score.split(' ')[1]) < self.score:
                            updates.append('best_ruin=' + str(self.id))

                updates = ', '.join(updates)
                counter_query = f'UPDATE counters SET {updates} WHERE user_id=$1;'

                await connection.execute(counter_query, key)


class Count(commands.Cog):
    def __init__(self, curator: bot.Curator):
        self.bot = curator
        self.counting = None
        self.count_channel = None

    async def get_profile_with_create(self, discord_id: int) -> CounterProfile:
        return await self.get_profile(discord_id) or await self.create_profile(discord_id)

    async def get_profile(self, discord_id: int, connection=None) -> CounterProfile:
        query = "SELECT * FROM counters WHERE user_id=$1;"
        con = connection or self.bot.pool
        record = await con.fetchrow(query, discord_id)
        return CounterProfile(record=record) if record else None

    async def create_profile(self, discord_id: int) -> CounterProfile:
        connection = self.bot.pool
        print(f'Registered counter with id {discord_id}')

        if 'Profile' in self.bot.cogs:
            p_cog = self.bot.cogs['Profile']
            await p_cog.get_profile_with_create(discord_id)

        p = CounterProfile.temporary()
        query = """INSERT INTO counters (user_id)
                   VALUES ($1)
                   RETURNING user_id;
                """
        row = await connection.fetchrow(query, discord_id)
        p.user_id = row[0]
        return p

    def is_count_channel(self, channel: discord.TextChannel):
        return 'count' in channel.name.lower()

    async def check_channel(self, channel: discord.TextChannel, message=False) -> bool:
        if not self.is_count_channel(channel):
            if message:
                await channel.send('Count commands are intended for use only in channels that contain "count" in the name...')
            return False
        return True

    async def check_count(self, message: discord.Message) -> bool:
        if not self.is_count_channel(message.channel) or self.counting is None:
            return False

        c: Counting = self.counting

        if not c.attempt_count(message.author, message.content.split()[0]):
            await message.channel.send(message.author.mention + ' failed, and ruined the count for ' + str(
                len(c.contributors.keys())) + ' counters...\nThe count reached ' + str(c.score) + '.')
            await message.channel.send(c.contributors)
            await c.finish(self.bot, False, message.author)
            self.counting = None
            return False
        return True

    @commands.group(invoke_without_command=True)
    async def count(self, ctx: commands.Context):
        if await self.check_channel(ctx.channel):
            await ctx.send(f'You need to supply a subcommand. Try {ctx.prefix}help count')

    @count.command()
    async def start(self, ctx: commands.Context):
        if await self.check_channel(ctx.channel):
            await ctx.send('Count has been started. Good luck!')
            self.counting = Counting.temporary(started_by=ctx.author.id)
        else:
            await ctx.send("You can't start a count outside of the count channel.")

    @count.command()
    async def profile(self, ctx: commands.Context, *, user: Optional[discord.User]):
        user: discord.User = user or ctx.author
        counter: CounterProfile = await self.get_profile_with_create(user.id)

        if profile:
            embed = discord.Embed(title=f'{user.name} - counting profile')
            embed.add_field(name='Total Score', value=f'{counter.total_score} counts')
            embed.add_field(name='Contributed in', value=f'{counter.counts_participated} rounds')
            embed.add_field(name='Rounds Started', value=f'{counter.counts_started} rounds')
            embed.add_field(name='Rounds Ruined', value=f'{counter.counts_ruined} rounds')
            embed.add_field(name='Best Round', value=f'Round {counter.best_count}')
            embed.add_field(name='Worst Fail', value=f'Round {counter.best_ruin}')
            embed.add_field(name='Last Count', value=f'Round {counter.last_count}')
            await ctx.send(embed=embed)
        else:
            await ctx.send('Could not find your profile.')

    @count.command()
    async def data(self, ctx: commands.Context):
        await ctx.send(self.counting.__dict__)

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
    async def parse(self, ctx: commands.Context, number: str):
        parse = parsed(number)
        await ctx.send(parse)


def setup(curator: bot.Curator):
    curator.add_cog(Count(curator))
