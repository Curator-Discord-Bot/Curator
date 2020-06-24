import discord
from discord.ext import commands


class Learning(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.author.id in [261156531989512192, 314792415733088260] or await self.bot.is_owner(ctx.author)

    @commands.command()
    async def hi(self, ctx: commands.Context):
        await ctx.send('Hello, ' + ctx.author.mention + '!')

    @commands.command()
    async def oi(self, ctx: commands.Context):
        await ctx.send('G\'day, ' + ctx.author.name + '!')

    @commands.command()
    async def add(self, ctx: commands.Context, first: int, second: int, name: int):
        await ctx.send(str(first) + ' + ' + str(second) + ' + ' + str(name) + ' = ' + str(first + second + name))

    @commands.command()
    async def greet(self, ctx: commands.Context):
        await ctx.send('Hey, Ruucas!')

    @commands.command()
    async def user(self, ctx: commands.Context, user: discord.User):
        await ctx.send(user.mention)

    @commands.command()
    async def member(self, ctx: commands.Context, member: discord.Member):
        await ctx.send(member.mention)

    @commands.command()
    async def teste(self, ctx: commands.Context):
        await ctx.send(2 == 2 == 2 != 3)

    @commands.command()
    async def authorof(self, ctx: commands.Context, message_link):
        IDs = message_link.split('/')[-2:]
        message = await self.bot.get_channel(int(IDs[0])).fetch_message(int(IDs[1]))
        await ctx.send(message.author.id)
        print(message.author.id)


def setup(bot: commands.Bot):
    bot.add_cog(Learning(bot))
