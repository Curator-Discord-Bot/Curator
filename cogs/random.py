from typing import Optional

import discord
from discord.ext import commands
from numpy import random


class RNG(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def random(self, ctx: commands.Context):
        await ctx.send(f'See {ctx.prefix}help random')

    @random.command()
    async def member(self, ctx: commands.Context):
        m = random.choice(ctx.guild.members)
        await ctx.send(str(m))

    @commands.command(name='8ball', aliases=('8', 'eightball', '🎱'))
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

        await ctx.send(random.choice(answers))

    @commands.command()
    async def choice(self, ctx: commands.Context, *options):
        if len(options) < 1:
            await ctx.send('You gave me nothing to choose from. :weary:')
        else:
            await ctx.send(random.choice(options).replace('@', 'AT'))

    @commands.command()
    async def dice(self, ctx: commands.Context, number: Optional[int]):
        number = number or 1
        s = str(random.randint(low=1, high=6, size=number))
        await ctx.send(s.replace('[', '').replace(']', ''))


def setup(bot: commands.Bot):
    bot.add_cog(RNG(bot))
