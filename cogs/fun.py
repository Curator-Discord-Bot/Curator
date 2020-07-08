import discord
from discord.ext import commands
from random import choice
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

    @commands.command()
    async def jokalize(self, ctx: commands.Context, *, text):
        if len(text) == 0:
            text = "There is no text."
        new_text = ''
        for letter in text:
            new_text += choice([letter.lower(), letter.upper()])
        await ctx.send(new_text.replace('@', 'AT'))

    @commands.command()
    async def secret(self, ctx: commands.Context):
        e = discord.Embed(title='**Top Secret**', description='[Don\' tell me you didn\'t ask for it.](https://www.youtube.com/watch?v=dQw4w9WgXcQ)')
        await ctx.send(embed=e)


def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
