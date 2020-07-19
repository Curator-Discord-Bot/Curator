import string

import discord
from asyncio import sleep as slp
from discord.ext import commands
from random import choice, randint
import requests
from .utils.messages import hello, collect


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

    @commands.command(aliases=['deleteme'])
    async def delete(self, ctx: commands.Context):
        name = ctx.author.display_name

        if 'bot' in name.lower():
            await ctx.send(f'I don\'t take commands from bots. Hehe.')
        else:
            r = randint(0, 1)

            if r == 0:
                e = discord.Embed(description='The action can\'t be completed because the file is open in Curator.\n\nClose the file and try again.')
                e.set_footer(text='\u02C4 Fewer details')
                e.set_thumbnail(url=self.bot.user.avatar_url)
                e.set_author(name='File In Use')
                e.add_field(name='Curator.bot', value='File type: BOT File\nSize: 1.38 TB\nBans: 3.7K')
                e.add_field(name=':wink:', value='[T__r__y Again](https://www.youtube.com/watch?v=dQw4w9WgXcQ)', inline=False)
                e.add_field(name=':innocent:', value='[Cancel](https://www.youtube.com/watch?v=dQw4w9WgXcQ)', inline=True)
                await ctx.send(embed=e)

            elif r == 1:
                if ctx.message.guild is None:
                    await ctx.send('There\'s no one here to delete.')
                    return
                if ctx.message.guild.owner is not None and ctx.author.id == ctx.message.guild.owner.id:
                    await ctx.send('I couldn\'t possibly delete the server owner...')
                    return
                if 'deleted' in name.lower():
                    await ctx.send('You are already deleted... Why are you here?')
                    return
                
                await ctx.send(f'Deleting {name}.')
                letters = 'abcdef'
                numbers = '0123456789'
                tag = ''.join(choice(numbers) for i in range(4)) + ''.join(choice(letters) for i in range(2)) + ''.join(choice(numbers) for i in range(2))

                await ctx.author.edit(nick=(f'Deleted User {tag}'))
                await ctx.send(f'Successfully deleted {name}.')
                await slp(60)
                await ctx.author.edit(nick=name)


def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
