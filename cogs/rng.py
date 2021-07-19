import discord
from discord.ext import commands
from bot import Curator
from numpy import random
import matplotlib.pyplot as plt
from io import BytesIO
from typing import Optional


class RNG(commands.Cog):
    def __init__(self, bot: Curator):
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

    @commands.command()
    async def randomizer(self, ctx: commands.Context, iterations: Optional[int]):
        """A randomizer that bases its chances on it's previous results.

        You can provide the number of iterations, default is 100, max is currently 10000.
        """
        if iterations and iterations > 10000:
            return await ctx.send('Try a lower number. (The max will be changed after testing)')

        results = ["red", "blue"]
        red_percentages = [50]
        for i in range(iterations if iterations else 100):
            results.append(random.choice(results))
            red_percentages.append(results.count("red") / len(results) * 100)

        try:
            await ctx.send(f'```List of percentages: {red_percentages}```')
        except discord.HTTPException:
            await ctx.send('The list of percentages is too long to send, go enjoy the graph.')
        plt.figure()
        plt.plot(red_percentages, color="red")
        plt.title('Percentages of red over time')
        plt.xlabel('Iterations')
        plt.ylabel('Percentage')
        buf = BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        await ctx.send(file=discord.File(buf, 'line.png'))

        try:
            await ctx.send(f'```List of results: {results}```')
        except discord.HTTPException:
            await ctx.send('The list of results is too long to send, go enjoy the graph.')
        plt.figure()
        plt.bar(1, results.count("red"), color=["red"])
        plt.bar(2, results.count("blue"), color=["blue"])
        plt.title('Colour selection amounts.')
        plt.ylabel('Selections')
        plt.xticks([1, 2], ["Red", "Blue"])
        buf = BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        await ctx.send(file=discord.File(buf, 'bars.png'))


def setup(bot: Curator):
    bot.add_cog(RNG(bot))
