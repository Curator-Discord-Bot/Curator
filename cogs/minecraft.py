import base64
import json
from typing import Union
from uuid import UUID

import discord
from discord.ext import commands
from json import dumps
import requests
import emoji

color_emoji = {
    'green': emoji.emojize(':green_square:'),
    'yellow': emoji.emojize(':yellow_square:'),
    'red': emoji.emojize(':red_square:')
}


def get_uuid(username):
    try:
        r = requests.get(f'https://api.minetools.eu/uuid/{username}')
        j = r.json()
        return j['id']
    except Exception as e:
        return None


class Minecraft(commands.Cog):
    """Commands related to Minecraft."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, aliases=['mojang', 'mc'])
    async def minecraft(self, ctx: commands.Context):
        """Minecraft commands."""
        await ctx.send(f'Try ```{ctx.prefix}help mc```')

    @minecraft.command()
    async def status(self, ctx: commands.Context):
        """Get the statuses of various Minecraft services."""
        r = requests.get('https://status.mojang.com/check')
        j = r.json()
        statuses = []
        for d in j:
            for key in d.keys():
                statuses.append('**' + key + '**: ' + color_emoji[d[key]])
        await ctx.send('\n\n'.join(statuses))

    @minecraft.command()
    async def server(self, ctx: commands.Context, ip):
        """Get information about a server."""
        url = f'https://api.mcsrvstat.us/2/{ip}'
        r = requests.get(url)
        j = r.json()
        embed: discord.Embed = discord.Embed(title=f'Minecraft Server Status - {ip}', colour=2252497)
        jkeys = j.keys()
        if 'version' in jkeys and len(j["version"]) > 1:
            embed.title += f' ({j["version"]})'

        embed.set_thumbnail(url=f'https://api.mcsrvstat.us/icon/{ip}')

        if 'motd' in jkeys and 'clean' in j['motd'].keys():
            embed.add_field(name='MOTD', value='\n'.join(j['motd']['clean']))

        embed.add_field(name='Online: ', value=j['online'], inline=True)

        if 'players' in jkeys:
            players = j['players']
            print(players)
            embed.add_field(name='Slots', value=f'{players["online"]}/{players["max"]}', inline=True)
            if 'list' in players.keys():
                embed.add_field(name='Players', value=f'{", ".join(players["list"])}', inline=True)
        await ctx.send(embed=embed)

    @minecraft.command(aliases=['skin', 'profile'])
    async def player(self, ctx: commands.Context, user: Union[UUID, discord.User, str]):
        """Get a player's skin and their Discord tag if it is linked."""
        minecraft_username = None
        if type(user) is discord.User:
            minecraft_uuid = await self.bot.pool.fetchval('SELECT minecraft_uuid FROM profiles WHERE discord_id = $1',
                                                          user.id)
            userfound = True
        else:
            userfound = False

        if not userfound or type(user) is UUID:
            minecraft_uuid = user
        else:
            r = requests.get(f'https://api.minetools.eu/uuid/{user}')

            try:
                minecraft_uuid = UUID(r.json()['id'])
                minecraft_username = r.json()['name']
            except Exception as e:
                await ctx.send(f'Error: {e}')
                return

        if minecraft_username is None:
            r = requests.get(f'https://api.minetools.eu/uuid/{user}')
            try:
                minecraft_username = r.json()['name']
            except Exception as e:
                await ctx.send(f'Error: {e}')
                return

            #r = requests.get(f'https://api.minetools.eu/profile/{minecraft_uuid}')
            #skin_url = r.json()['decoded']['textures']['SKIN']['url']

        embed = discord.Embed(title=f'{minecraft_username}\'s NameMC', url=f'https://namemc.com/profile/{minecraft_uuid}')
        embed.description = f'[Download Skin](https://mc-heads.net/download/{minecraft_uuid})'

        embed.set_image(url=f'https://mc-heads.net/body/{minecraft_uuid}')

        if userfound and type(user) is discord.User:
            embed.add_field(name='Discord', value=str(user))
        elif 'Profile' in self.bot.cogs:
            query = "SELECT discord_id FROM profiles WHERE minecraft_uuid=$1;"
            discord_id = await self.bot.pool.fetchval(query, minecraft_uuid)
            if discord_id:
                member = await ctx.guild.fetch_member(discord_id)
                embed.add_field(name='Discord', value=str(member))

        await ctx.send(embed=embed)

    @minecraft.command()
    async def namemc(self, ctx: commands.Context, username):
        """Get the NameMC link of a player."""
        await ctx.send(f'https://namemc.com/search?q={username}')

    @minecraft.command()
    async def head(self, ctx: commands.Context, username):
        """Get the head of a player."""
        embed = discord.Embed(title='Head')
        embed.set_image(url=f'https://crafatar.com/renders/head/{get_uuid(username)}?overlay')
        await ctx.send(embed=embed)
        await ctx.send('Up to 1.12.2: `/give @p skull 1 3 {SkullOwner:%s}`' % username)
        await ctx.send('1.13+: `/give @p minecraft:player_head{SkullOwner:%s}`' % username)

    @minecraft.command(aliases=['avatar'])
    async def face(self, ctx: commands.Context, username):
        """Get a player's skin's face."""
        embed = discord.Embed(title='Face')
        embed.set_image(url=f'https://crafatar.com/avatars/{get_uuid(username)}?overlay')
        await ctx.send(embed=embed)

    @minecraft.command(aliases=['nh', 'prevnames'])
    async def namehistory(self, ctx: commands.Context, username):
        """Get a player's previous usernames."""
        r = requests.get(f'https://api.mojang.com/user/profiles/{get_uuid(username)}/names')
        j = r.json()
        await ctx.send(j)

        print(j)


def setup(bot: commands.Bot):
    bot.add_cog(Minecraft(bot))
