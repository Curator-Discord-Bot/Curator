import discord
from discord.ext import commands
from aio_timers import Timer
import emoji


running_games = {}


def make_message(data):
    field_message = ''
    for i in range(len(data)):
        field_message += data[i]
        if (i + 1) % 3 == 0:
            field_message += '\n'
    return field_message


def check(f):
    return f[0] == f[1] == f[2] != ':heavy_minus_sign:' or f[3] == f[4] == f[5] != ':heavy_minus_sign:' or \
           f[6] == f[7] == f[8] != ':heavy_minus_sign:' or f[0] == f[3] == f[6] != ':heavy_minus_sign:' or \
           f[1] == f[4] == f[7] != ':heavy_minus_sign:' or f[2] == f[5] == f[8] != ':heavy_minus_sign:' or \
           f[0] == f[4] == f[8] != ':heavy_minus_sign:' or f[6] == f[4] == f[2] != ':heavy_minus_sign:'


class TTTGame:
    def __init__(self, channel, p1, p2):
        self.channel = channel
        self.field = [':heavy_minus_sign:' for i in range(9)]
        self.game_message = None
        self.turn_message = None
        self.p1 = p1
        self.p2 = p2
        self.on_turn = p1
        self.timeout = None

    async def begin(self):
        self.game_message = await self.channel.send(make_message(self.field))
        for i in range(1, 10):
            await self.game_message.add_reaction(f'{i}️⃣')
        self.turn_message = await self.channel.send(f'{self.on_turn.display_name} is playing.')
        self.timeout = Timer(60, self.timedout)
        await self.timeout.wait()

    async def play(self, number, player, reaction_object):
        if number.isdigit():
            number = int(number) - 1
        if number in range(9):
            if player == self.on_turn:
                self.timeout.cancel()
                value_here = self.field[number]
                if value_here == ':heavy_minus_sign:':
                    self.field[number] = ':x:' if player == self.p1 else ':o:'
                    await self.game_message.edit(content=make_message(self.field))
                    if check(self.field):
                        await self.turn_message.edit(content=f'{self.on_turn.display_name} has won!')
                        del (running_games[self.channel.id])
                        return
                    elif ':heavy_minus_sign:' not in self.field:
                        await self.turn_message.edit(content='It\'s a tie. :neutral_face:')
                        del (running_games[self.channel.id])
                        return
                    self.on_turn = self.p2 if self.on_turn == self.p1 else self.p1
                    await self.turn_message.edit(content=f'{self.on_turn.display_name} is playing.')
                    self.timeout = Timer(60, self.timedout)
                    await self.timeout.wait()
                else:
                    await self.channel.send('This field is already taken, choose another one.')
            else:
                await self.channel.send(f'It is not your turn, {player.display_name}.' if player in [self.p1, self.p2]
                                        else f"You are not in this game, {player.display_name}.")
            await reaction_object.remove(player)

    async def timedout(self):
        await self.turn_message.edit(content='The game timed out.')
        del (running_games[self.channel.id])


class Tictactoe(commands.Cog):
    """A game of Tic Tac Toe."""

    def __init__(self, bot: commands.bot):
        self.bot = bot

    @commands.group(aliases=['noughts&crosses', 'ttt', 'ox'], invoke_without_command=True)
    async def tictactoe(self, ctx: commands.Context):
        """Commands for tictactoe!"""
        await ctx.send(f'`{ctx.prefix}tictactoe start <user>` to challenge another player to a game of tic-tac-toe!')

    @tictactoe.command(aliases=['begin', 'challenge'])
    async def start(self, ctx: commands.Context, p2: discord.Member):
        """Start a game of Tic Tac Toe.

        Ping the person you want to challenge or give the user ID.
        """
        if ctx.channel.id in running_games.keys():
            return await ctx.send('A game is already going on in this channel.')
        p1 = ctx.author
        if p1 == p2:
            return await ctx.send('You can\'t start a game with yourself.')
        running_games[ctx.channel.id] = None

        prompt_text = f'{p2.mention if p2 not in ctx.message.mentions else p2.display_name}, ' \
                      f'do you accept this challenge of Tic Tac Toe? The invitation expires in 5 minutes. ' \
                      f'Be sure to pay attention to the reply, {p1.display_name}.'
        confirm = await ctx.prompt(prompt_text, timeout=300.0, reacquire=False, author_id=p2.id)
        if not confirm:
            del (running_games[ctx.channel.id])
            return await ctx.send(
                f'{p1.mention}, {p2.display_name} didn\'t take on the challenge or didn\'t reply in time.')
        await ctx.send(f'{p1.mention}, {p2.display_name} has accepted your challenge!')

        running_games[ctx.channel.id] = TTTGame(ctx.channel, p1, p2)
        await running_games[ctx.channel.id].begin()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.channel.id in running_games.keys():
            game = running_games[reaction.message.channel.id]
            if game:
                if reaction.message.id == game.game_message.id and user != self.bot.user:
                    await game.play(emoji.demojize(str(reaction))[-2], user, reaction)

    @commands.command(hidden=True)
    async def printtttgames(self, ctx: commands.Context):
        """Print the currently running games of Tic Tac Toe."""
        if ctx.author.id in [261156531989512192, 314792415733088260] or await self.bot.is_owner(ctx.author):
            print(running_games)
            await ctx.send('Check the Python printer output for your results.')
        else:
            await ctx.send('You do not have access to this command.')


def setup(bot: commands.Bot):
    bot.add_cog(Tictactoe(bot))
