import datetime
from typing import Optional
from uuid import UUID

import asyncpg
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
    def __init__(self, *, d: dict):
        self.id = d['id']
        self.created_at = d['created_at']
        self.discord_id = d['discord_id']
        self.minecraft_uuid = d['minecraft_uuid']


class UserConnection:
    __slots__ = ('original', 'current', 'connection')
    original: UserProfile
    current: UserProfile
    connection: asyncpg.pool.Pool

    def __init__(self, record, connection):
        self.original = UserProfile(d=db.dict_from_record(record))
        self.current = UserProfile(d=db.dict_from_record(record))
        self.connection = connection

    async def save(self):
        original_keys = self.original.__dict__.keys()
        updates = [(key, value) for key, value in self.current.__dict__.items() if
                   key not in original_keys or value != self.original.__dict__[key]]
        if updates:
            updatestr = ", ".join([str(key) + " = " + (str(value) if type(value) is not UUID else f"'{value.hex}'") for key, value in updates])
            query = f'UPDATE profiles SET {updatestr} WHERE discord_id={self.original.discord_id} RETURNING *;'
            print(query)
            await self.connection.execute(query)

    async def __aenter__(self) -> UserProfile:
        return self.current

    async def __aexit__(self, typ, value, traceback):
        await self.save()

    def __repr__(self):
        return f'<User id={self.current.id}, discord_id={self.current.discord_id}, minecraft_uuid={self.current.minecraft_uuid}>'


async def fetch_user_record(discord_id, connection) -> asyncpg.Record:
    return await connection.fetchrow(
        'INSERT INTO profiles (discord_id) VALUES ($1) ON CONFLICT (discord_id) DO UPDATE SET discord_id = profiles.discord_id RETURNING *',
        discord_id)


class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def profile(self, ctx: commands.Context, target: Optional[discord.Member]):
        id = target.id if target else ctx.author.id
        async with UserConnection(await fetch_user_record(discord_id=id, connection=self.bot.pool),
                                  connection=self.bot.pool) as user:
            if user:
                await ctx.send(
                    f'Here is your profile:\n```\nCreated at: {user.created_at}\nDiscord ID: {user.discord_id}\nMinecraft UUID: {user.minecraft_uuid}\n```')
            else:
                await ctx.send('Could not load your profile.')

    @commands.command(aliases=['verify'])
    async def auth(self, ctx: commands.Context, pin: int):
        query = 'DELETE FROM auths WHERE pin = $1 RETURNING minecraft_uuid;'
        id = await self.bot.pool.fetchval(query, pin)
        if id:
            #TOOD save uuid
            await ctx.send(f'You verified minecraft account with UUID {id}')
        else:
            await ctx.send('That pin seems to be invalid.')


def setup(bot: commands.Bot):
    bot.add_cog(Profile(bot))
