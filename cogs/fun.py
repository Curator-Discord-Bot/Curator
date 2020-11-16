import string

import discord
from asyncio import sleep as slp
from discord.ext import commands
from typing import Optional
from random import choice, randint
import requests
from .utils.messages import hello, collect


deleted_usernames = {}


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(hello(ctx))

    @commands.command()
    async def yesno(self, ctx: commands.Context):
        r = requests.get('https://yesno.wtf/api')
        j = r.json()
        embed = discord.Embed(title=j['answer'])
        embed.set_image(url=j['image'])
        await ctx.send(embed=embed)

    @commands.command()
    async def reverse(self, ctx: commands.Context, *options):
        if len(options) < 1:
            await ctx.send('Give me something to reverse.')
        else:
            await ctx.send(f"{ctx.author}: {' '.join(options)[::-1].replace('@', 'AT')}")

    @commands.command()
    async def collect(self, ctx: commands.Context, amount: float):
        if not amount.is_integer():
            await ctx.send('Everybody knows you can\'t split a diamond!')
        elif amount < 0:
            await ctx.send(f'You want to give me {int(-amount)} diamond{"s" if amount < -1 else ""}?')
        elif amount == 0:
            await ctx.send('Collect nothing?')
        elif amount > 68:
            await ctx.send('I don\'t have that many!')
        else:
            amount = int(amount)
            await ctx.send(amount * '<:diamond:495591554937913344>')
            await ctx.send(collect(ctx))

    @commands.command(aliases=('jokalise', 'caseshuffle'))
    async def jokalize(self, ctx: commands.Context, *, text):
        if len(text) == 0:
            text = "There is no text."
        new_text = ''
        for letter in text:
            new_text += choice([letter.lower(), letter.upper()])
        await ctx.send(new_text.replace('@', 'AT'))

    @commands.command(aliases=('vaporize', 'vaporise'))
    async def vaporwave(self, ctx: commands.Context, *, message):
        await ctx.send(' '.join(message.upper()))

    @commands.command()
    async def secret(self, ctx: commands.Context):
        e = discord.Embed(title='**Top Secret**', description='[Don\' tell me you didn\'t ask for it.](https://www.youtube.com/watch?v=dQw4w9WgXcQ)')
        await ctx.send(embed=e)

    @commands.command()
    async def deleteme(self, ctx: commands.Context):
        name = ctx.author.display_name

        if 'bot' in name.lower():
            return await ctx.send(f'I don\'t take commands from bots. Hehe.')

        if randint(0, 1):
            e = discord.Embed(description='The action can\'t be completed because the file is open in Curator.\n\nClose the file and try again.')
            e.set_footer(text='\u02C4 Fewer details')
            e.set_thumbnail(url=self.bot.user.avatar_url)
            e.set_author(name='File In Use')
            e.add_field(name='Curator.bot', value='File type: BOT File\nSize: 1.38 TB\nBans: 3.7K')
            e.add_field(name=':wink:', value='[T__r__y Again](https://www.youtube.com/watch?v=dQw4w9WgXcQ)', inline=False)
            e.add_field(name=':innocent:', value='[Cancel](https://www.youtube.com/watch?v=dQw4w9WgXcQ)', inline=True)
            await ctx.send(embed=e)

        else:
            if ctx.message.guild is None:
                return await ctx.send('There\'s no one here to delete.')
            if ctx.message.guild.owner is not None and ctx.author.id == ctx.message.guild.owner.id:
                return await ctx.send('I couldn\'t possibly delete the server owner...')
            if ctx.author.id in deleted_usernames.keys() and deleted_usernames[ctx.author.id] == name:
                return await ctx.send('You are already deleted... Why are you here?')

            await ctx.send(f'Deleting {name.replace("@", "AT")}.')
            letters = 'abcdef'
            numbers = '0123456789'
            tag = ''.join(choice(numbers) for i in range(4)) + ''.join(choice(letters) for i in range(2)) + ''.join(choice(numbers) for i in range(2))

            await ctx.author.edit(nick=f'Deleted User {tag}')
            await ctx.send(f'Successfully deleted {name.replace("@", "AT")}.')
            deleted_usernames[ctx.message.author.id] = f'Deleted User {tag}'
            await slp(10)
            if ctx.author.display_name == f'Deleted User {tag}':
                await ctx.author.edit(nick=name)

    @commands.command(aliases=['hamdog'])
    async def chomp(self, ctx: commands.Context, amount: Optional[float]):
        if not amount:
            if len(ctx.message.content.split()) == 1:
                await ctx.send('<a:hamdog:741335292597895781>' + 3 * '<a:ham:741335318891855902>')
            elif ctx.message.content.split()[1] == '0':
                await ctx.send('No hamburgers?:worried:')
        elif amount < 0:
            if not amount.is_integer():
                await ctx.send('I only chomp out full burgers.')
            elif amount < -75:
                await ctx.send('My stomach is not that full!')
            else:
                amount = -int(amount)
                await ctx.send('<a:godham:741367312380330026>' + amount * '<a:mah:741367328465354772>')
        else:
            if not amount.is_integer():
                await ctx.send('I only chomp on full burgers.')
            elif amount > 75:
                await ctx.send('The kitchen is too slow:neutral_face:')
            else:
                amount = int(amount)
                await ctx.send('<a:hamdog:741335292597895781>' + amount * '<a:ham:741335318891855902>')

    @commands.command(name='LOG', aliases=['LOGGER', 'LOGGERS'])
    async def log_meme(self, ctx: commands.Context, amount: Optional[int]):
        amount = amount if amount or amount == 0 else 1
        if amount < 1:
            return await ctx.send('It must be at least one.')
        if amount > 80:
            return await ctx.send('The forest isn\'t that big:grimacing:')

        await ctx.send(amount * '<:LOG:767104818778341377>')

    @commands.command(aliases=['cat'])
    async def catloop(self, ctx: commands.Context):
        await ctx.send(files=[discord.File('media/catloop/cat1.gif'), discord.File('media/catloop/cat2.gif')])


def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
