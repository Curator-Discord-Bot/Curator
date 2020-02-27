import base64
import json

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


class Minecraft(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, aliases=['mojang', 'mc'])
    async def minecraft(self, ctx: commands.Context):
        await ctx.send(f'Try {ctx.prefix}help mc')

    @minecraft.command()
    async def status(self, ctx: commands.Context):
        r = requests.get('https://status.mojang.com/check')
        j = r.json()
        statuses = []
        for d in j:
            for key in d.keys():
                statuses.append('**' + key + '**: ' + color_emoji[d[key]])
        await ctx.send('\n\n'.join(statuses))

    @minecraft.command()
    async def uuid(self, ctx: commands.Context, *names):
        if len(names) > 1:
            r = requests.post('https://api.mojang.com/profiles/minecraft', data=dumps(names))
            rj = r.json()
            await ctx.send('\n'.join(['**' + j['name'] + '**: ' + j['id'] for j in rj]))
        else:
            r = requests.get(f'https://api.mojang.com/users/profiles/minecraft/{names[0]}')
            j = r.json()
            await ctx.send('**' + j['name'] + '**: ' + j['id'])

    @minecraft.command()
    async def server(self, ctx: commands.Context, ip):
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

    @minecraft.command()
    async def skin(self, ctx: commands.Context, uuid):
        r = requests.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{uuid}')
        j = r.json()

        base64_message = j['properties'][0]['value']
        base64_bytes = base64_message.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        message = message_bytes.decode('ascii')
        skin = json.loads(message)['textures']['SKIN']['url']
        await ctx.send(skin)

    @minecraft.command()
    async def body(self, ctx: commands.Context, uuid):
        await ctx.send(f'https://crafatar.com/renders/body/{uuid}?overlay')

    @minecraft.command()
    async def head(self, ctx: commands.Context, uuid):
        await ctx.send(f'https://crafatar.com/renders/head/{uuid}?overlay')

    @minecraft.command(aliases=['avatar'])
    async def face(self, ctx: commands.Context, uuid):
        await ctx.send(f'https://crafatar.com/avatars/{uuid}?overlay')


def setup(bot: commands.Bot):
    bot.add_cog(Minecraft(bot))
