import discord
from discord.ext import commands


class Tictactoe(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(aliases=['noughts&crosses', 'ttt', 'ox'], invoke_without_command=True)
    async def tictactoe(self, ctx: commands.Context):
        await ctx.send(f'`{ctx.prefix}tictactoe start <user>` to challenge another player to a game of tic-tac-toe')

    @tictactoe.command()
    async def start(self, ctx: commands.Context, p2: discord.User):
        #await ctx.send(f'{p2.mention}, do you accept the challenge? Replay with :white_check_mark: if you do, or with '
        #               f':x: if you don\'t, this invitation expires in 15 minutes.')
        #await ctx.channel.last_message.add_reaction('✅')
        #await ctx.channel.last_message.add_reaction('❌')

        prompt_text = f'Testing a feature'
        confirm = await ctx.prompt(prompt_text, reacquire=False)
        await ctx.send(confirm)


def setup(bot: commands.Bot):
    bot.add_cog(Tictactoe(bot))
