import discord
from discord.ext import commands
from random import choice
import requests


class Silly(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx: commands.Context):
        author: discord.Member = ctx.author
        role: str = choice(list(map(str, author.roles[1:])))
        await ctx.send(
            choice(('Hey', 'Hello', 'Hi', 'Ey', 'Yo', 'Sup', ':wave:', 'Good to see you', 'Greetings', 'Peace')) + ', ' + choice((ctx.author.name, 'dude', 'buddy', 'mate', choice(('bro', 'brother')), 'man', 'there', 'silly', 'you', 'master', 'traveler', 'fancypants', 'human', (role if len(role) > 0 else 'nobody'))) + '!')

    @commands.command()
    async def echo(self, ctx: commands.Context, *, message):
        m: discord.Message = ctx.message
        await m.delete()
        await ctx.send(message)

    @commands.command()
    async def yesno(self, ctx: commands.Context):
        r = requests.get('https://yesno.wtf/api')
        j = r.json()
        embed = discord.Embed(title=j['answer'])
        embed.set_image(url=j['image'])
        await ctx.send(embed=embed)

    @commands.command(name='8ball', aliases=('8', 'eightball'))
    async def eight_ball(self, ctx: commands.Context):
        answers = (
            'It is certain.',
            'It is decidedly so.',
            'Without a doubt.',
            'Yes - definitely.',
            'You may rely on it.',
            'As I see it, yes.',
            'Most likely.',
            'Outlook good.',
            'Yes.',
            'Signs point to yes.',
            'Reply hazy, try again.',
            'Ask again later.',
            'Better no tell you now.',
            'Cannot predict now.',
            'Concentrate and ask again.',
            'Don\'t count on it.',
            'My reply is no.',
            'My sources say no.',
            'Outlook not so good.',
            'Very doubtful.'
        )

        await ctx.send(choice(answers))


def setup(bot: commands.Bot):
    bot.add_cog(Silly(bot))
