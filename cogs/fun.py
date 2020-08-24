import string

import discord
from asyncio import sleep as slp
from discord.ext import commands
from typing import Optional
from random import choice, randint
import requests
import matplotlib.pyplot as plt
from io import BytesIO
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

    @commands.command()
    async def deleteme(self, ctx: commands.Context):
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

    @commands.command()
    async def randomizer(self, ctx: commands.Context, iterations: Optional[int]):
        """A randomizer that bases its chances on it's previous results."""
        if iterations > 10000:
            return await ctx.send('Try a lower number. (The max will be changed after testing)')
        
        results = ["red", "blue"]
        red_percentages = [50]
        for i in range(iterations if iterations else 100):
            results.append(choice(results))
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




def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
