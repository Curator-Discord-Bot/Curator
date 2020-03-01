import datetime

import discord
from discord.ext import commands
from .utils import db
from .minecraft import get_uuid


class Profiles(db.Table):
    id = db.PrimaryKeyColumn()
    created_at = db.Column(db.Datetime, default="now() at time zone 'utc'")
    discord_id = db.Column(db.Integer(big=True), unique=True)
    minecraft_uuid = db.Column(db.UUID, unique=True)


class UserProfile:
    __slots__ = ('id', 'created_at', 'discord_id', 'minecraft_uuid')

    def __init__(self, *, record):
        self.id = record['id']
        self.created_at = record['created_at']
        self.discord_id = record['discord_id']
        self.minecraft_uuid = record['minecraft_uuid']

    @classmethod
    def temporary(cls, *, created_at, discord_id, minecraft_uuid):
        pseudo = {
            'id': None,
            'created_at': created_at,
            'discord_id': discord_id,
            'minecraft_uuid': minecraft_uuid
        }
        return cls(record=pseudo)

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f'<Profile created_at={self.created_at} discord_id={self.discord_id}>'


class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_profile_with_create(self, discord_id: int) -> UserProfile:
        return await self.get_profile(discord_id) or await self.create_profile(discord_id)

    async def get_profile(self, discord_id: int, connection=None) -> UserProfile:
        query = "SELECT * FROM profiles WHERE discord_id=$1;"
        con = connection or self.bot.pool
        record = await con.fetchrow(query, discord_id)
        return UserProfile(record=record) if record else None

    async def create_profile(self, discord_id: int) -> UserProfile:
        connection = self.bot.pool
        now = datetime.datetime.utcnow()
        print(f'Registered profile with id {discord_id}')
        p = UserProfile.temporary(created_at=now, discord_id=discord_id, minecraft_uuid=None)
        query = """INSERT INTO profiles (created_at, discord_id, minecraft_uuid)
                   VALUES ($1, $2, $3)
                   RETURNING id;
                """
        row = await connection.fetchrow(query, now, discord_id, None)
        p.id = row[0]
        return p

    @commands.group(invoke_without_command=True)
    async def profile(self, ctx: commands.Context):
        p: UserProfile = await self.get_profile(ctx.author.id)
        if p is None:
            await ctx.send('You do not have a profile yet.')
        else:
            await ctx.send(
                f'Here is your profile:\n```\nCreated at: {p.created_at}\nDiscord ID: {p.discord_id}\nMinecraft UUID: {p.minecraft_uuid}\n```')

    @profile.command()
    async def create(self, ctx: commands.Context):
        p = await self.get_profile(ctx.author.id)
        if p is None:
            await self.create_profile(ctx.author.id)
            await ctx.send(f'Created profile with discord id: {ctx.author.id}.')
        else:
            await ctx.send('You already have a profile.')

    async def minecraft(self, ctx: commands.Context, username: str):
        uuid = get_uuid(username)
        if uuid:
            await self.get_profile_with_create(ctx.author.id)
            update = f'UPDATE profiles SET minecraft_uuid=$1 WHERE discord_id=$2;'
            await self.bot.pool.execute(update, uuid, ctx.author.id)
            await ctx.send(f'Assigned uuid {uuid} to your profile.')
        else:
            await ctx.send('Could not find uuid from supplied username.')

    @commands.command()
    async def auth(self, ctx: commands.Context, pin: int):
        query = 'SELECT minecraft_uuid from auths where pin=$1'
        row = await self.bot.pool.fetchrow(query, pin)
        if row:
            await self.minecraft(ctx, row["minecraft_uuid"])
            await ctx.send(f'You verified minecraft account with UUID {row["minecraft_uuid"]}')
        else:
            await ctx.send('That pin seems to be invalid.')


def setup(bot: commands.Bot):
    bot.add_cog(Profile(bot))
