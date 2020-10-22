import base64
import re

import discord
from discord.ext import commands


class Decode(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def formatted_result(self, r):
        r = r.replace('@', 'AT')
        return f'`{r}`'

    @commands.group(invoke_without_command=True)
    async def base64(self, ctx: commands.Context):
        await ctx.send(
            f'Decode or encode base64! See `{ctx.prefix}base64 encode <message>` or `{ctx.prefix}base64 decode <message>`. Or visit https://www.base64encode.org/.')

    @base64.command(name='encode')
    async def base64encode(self, ctx: commands.Context, *, message: str):
        message_bytes = message.encode('ascii')
        base64_bytes = base64.b64encode(message_bytes)
        base64_message = base64_bytes.decode('ascii')
        await ctx.send(base64_message)

    @base64.command(name='decode')
    async def base64decode(self, ctx: commands.Context, message: str):
        base64_message = message
        base64_bytes = base64_message.encode('ascii')
        message_bytes = base64.b64decode(base64_bytes)
        result = message_bytes.decode('ascii')
        await ctx.send(self.formatted_result(result))

    @commands.group(invoke_without_command=True)
    async def alphabet(self, ctx: commands.Context):
        await ctx.send(
            f'Decode or encode alphabet cipher! See `{ctx.prefix}alphabet encode <message>` or `{ctx.prefix}alphabet decode <message>`.')

    @alphabet.command(name='encode')
    async def alphabetencode(self, ctx: commands.Context, *, message: str):
        message = str(message.replace(' ', ''))
        regex = r"^[a-zA-Z ]+$"
        if re.fullmatch(regex, message):
            big_a = ord('A')
            m = ' '.join([str(ord(i)-big_a+1) for i in message if i != ' '])
            await ctx.send(m)
        else:
            await ctx.send('The message should only contain letter a-Z and space is ignored.')

    @alphabet.command(name='decode')
    async def alphabetdecode(self, ctx: commands.Context, *, message: str):
        regex = r"^(2[0-6]|1[0-9]|[1-9])( (2[0-6]|1[0-9]|[1-9]))*$"
        if re.fullmatch(regex, message):
            big_a = ord('A')
            m = ' '.join([chr(int(i)+big_a-1) for i in message.split()])
            await ctx.send(m)
        else:
            await ctx.send(
                f'The message should only contain numbers between 1-26 separated by space. Your message was `{message.replace("@", "")}`')

    @commands.group(invoke_without_command=True)
    async def atbash(self, ctx: commands.Context):
        await ctx.send(
            f'Decode or encode atbash ciper! See `{ctx.prefix}atbash encode <message>` or `{ctx.prefix}atbash decode <message>`.')

    @atbash.command(name='encode', aliases=['decode'])
    async def atbashencode(self, ctx: commands.Context, *, message: str):
        big_a, big_z, small_a, small_z = map(ord, 'AZaz')
        encoded = [chr(big_a + big_z - ord(i) if ord(i) <= big_z else small_a + small_z - ord(i)) if big_a <= ord(
            i) <= small_z else i for i in message]
        await ctx.send(''.join(encoded))

    @commands.group(invoke_without_command=True)
    async def plaintext(self, ctx: commands.Context):
        await ctx.send(
            f'Decode or encode plain text! See `{ctx.prefix}plaintext encode <message>` or `{ctx.prefix}plaintext decode <message>`.')

    @plaintext.command(name='encode')
    async def plaintextencode(self, ctx: commands.Context, *, message: str):
        await ctx.send(message.replace('@', 'AT'))

    @plaintext.command(name='decode')
    async def plaintextdecode(self, ctx: commands.Context, *, message: str):
        await ctx.send(message.replace('@', 'AT'))


def setup(bot: commands.Bot):
    bot.add_cog(Decode(bot))


def teardown():
    """Code to be executed when the cog unloads. This function is not required."""
    pass
