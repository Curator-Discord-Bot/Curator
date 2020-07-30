import asyncio
from asyncio import sleep as slp
import discord
from discord.ext import commands
from typing import Optional, Union, List


class TileType:
    name: str
    emoji: Optional[discord.Emoji]

    def __init__(self, name: str, emoji: str):
        self.name = name
        self.emoji = emoji


class Player:
    discord_id: int
    tile: TileType

    def __init__(self, discord_id: int, tile: TileType):
        self.discord_id = discord_id
        self.tile = tile


class FIAR:
    winner: Player
    WIDTH: int = 7
    HEIGHT: int = 6

    def __init__(self, empty: TileType, player_one: Player, player_two: Player):
        self.columns = [[empty for _ in range(FIAR.HEIGHT)] for _ in range(FIAR.WIDTH)]
        self.fullness = [0 for _ in range(FIAR.WIDTH)]
        self.turn = 0
        self.player_one = player_one
        self.player_two = player_two
        self.winner = None

    def is_full(self):
        return self.turn >= 42

    def current_player(self):
        return self.player_one if self.turn % 2 == 0 else self.player_two

    def other_player(self):
        return self.player_one if self.turn % 2 == 1 else self.player_two

    def insert(self, column: int):
        target = column % FIAR.WIDTH
        if self.fullness[target] < FIAR.HEIGHT and not self.is_full():
            self.columns[target][
                self.fullness[target]] = self.current_player().tile
            self.fullness[target] += 1

            if self.get_size(column, self.fullness[target] - 1) >= 4:
                self.winner = self.current_player()

            self.turn += 1
            return True
        return False

    def get_tile(self, column: int, height: int):
        target_c = column % FIAR.WIDTH
        target_h = height % FIAR.HEIGHT
        return self.columns[target_c][target_h]

    def get_size(self, column: int, height: int):
        target_c = column % FIAR.WIDTH
        target_h = height % FIAR.HEIGHT
        tile = self.get_tile(target_c, target_h)

        left = range(target_c - 1, -1, -1)
        right = range(target_c + 1, FIAR.WIDTH)
        horizontal = 1
        for c in left:
            if self.get_tile(c, target_h) == tile:
                horizontal += 1
            else:
                break
        for c in right:
            if self.get_tile(c, target_h) == tile:
                horizontal += 1
            else:
                break

        down = range(target_h - 1, -1, -1)
        up = range(target_h + 1, FIAR.HEIGHT)
        vertical = 1
        for h in down:
            if self.get_tile(target_c, h) == tile:
                vertical += 1
            else:
                break
        for h in up:
            if self.get_tile(target_c, h) == tile:
                vertical += 1
            else:
                break

        nw = range(1, min(FIAR.HEIGHT - target_h, target_c + 1))
        se = range(1, min(target_h + 1, FIAR.WIDTH - target_c))
        nw_se = 1
        for offset in nw:
            if self.get_tile(target_c - offset, target_h + offset) == tile:
                nw_se += 1
            else:
                break
        for offset in se:
            if self.get_tile(target_c + offset, target_h - offset) == tile:
                nw_se += 1
            else:
                break

        ne = range(1, min(FIAR.HEIGHT - target_h, FIAR.WIDTH - target_c))
        sw = range(1, min(target_h + 1, target_c + 1))
        ne_sw = 1
        for offset in ne:
            if self.get_tile(target_c + offset, target_h + offset) == tile:
                ne_sw += 1
            else:
                break
        for offset in sw:
            if self.get_tile(target_c - offset, target_h - offset) == tile:
                ne_sw += 1
            else:
                break
        return max(horizontal, vertical, nw_se, ne_sw)

    def __str__(self):
        simple_game = '\n'.join(
            [''.join(self.columns[x][5 - y].name[0] for x in range(FIAR.WIDTH)) for y in range(FIAR.HEIGHT)])
        return f'Four In A Row:\n1234567\n{simple_game}\n1234567'

    def emoji_board(self):
        emoji_game = '\n'.join(
            [''.join(str(self.columns[x][5 - y].emoji) for x in range(FIAR.WIDTH)) for y in range(FIAR.HEIGHT)])
        return emoji_game


class FourInARow(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.empty_tile = TileType('Empty', bot.get_emoji(738068784211820612))
        self.blue_tile = TileType('Blue', bot.get_emoji(738070670583398480))
        self.red_tile = TileType('Red', bot.get_emoji(738070670243790919))
        self.green_tile = TileType('Green', bot.get_emoji(738324385534050346))
        self.orange_tile = TileType('Orange', bot.get_emoji(738324385626324997))
        self.pink_tile = TileType('Pink', bot.get_emoji(738324385622130699))
        self.purple_tile = TileType('Purple', bot.get_emoji(738324385856749568))
        self.aqua_tile = TileType('Aqua', bot.get_emoji(738324385865400361))
        self.color_tiles = [self.blue_tile, self.red_tile, self.green_tile, self.orange_tile, self.pink_tile, self.purple_tile, self.aqua_tile]

        self.column_reactions = {
            '1️⃣': 0,
            '2️⃣': 1,
            '3️⃣': 2,
            '4️⃣': 3,
            '5️⃣': 4,
            '6️⃣': 5,
            '7️⃣': 6
        }
        self.inverse_column_reactions = {
            0: '1️⃣',
            1: '2️⃣',
            2: '3️⃣',
            3: '4️⃣',
            4: '5️⃣',
            5: '6️⃣',
            6: '7️⃣'
        }

    @commands.group(invoke_without_command=True,
                    aliases=['connectfour', 'connect4', 'fourup', 'plotfour', 'findfour', 'fourinaline', 'dropfour',
                             'gravitrips'])
    async def fourinarow(self, ctx: commands.Context):
        """The base command for four in a row"""
        await ctx.send(f'This is the base command. See `{ctx.prefix}help fourinarow` for help on other commands.')

    @fourinarow.command()
    async def start(self, ctx: commands.Context, target: Optional[discord.User]):
        """Starts a game of four in a row"""
        message: discord.Message = await ctx.send('Starting a game of Four In A Row!\nReact below to select a color.')
        tiles: List[TileType] = [t for t in self.color_tiles]

        for tile in tiles:
            await message.add_reaction(tile.emoji)

        def check(reaction: discord.reaction.Reaction, user: Union[discord.Member, discord.User]) -> bool:
            if user.bot or message.id != reaction.message.id:
                return False

            for tile in tiles:
                if tile.emoji == reaction.emoji:
                    return True
            return False

        player_one = None
        player_two = None

        try:
            reaction: discord.reaction.Reaction
            user: Union[discord.Member, discord.User]
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await message.edit(
                content=f'{ctx.author.name} wanted to start a game of Four In A Row, but it timed out...')
        else:
            tile = None
            for t in tiles:
                if t.emoji == reaction.emoji:
                    tile = t
                    tiles.remove(t)

            player_one = Player(user.id, tile)
            await message.edit(content=message.content + f'\n{user.name} picked {tile.name}{tile.emoji}.')
            await message.clear_reaction(reaction.emoji)

            try:
                reaction: discord.reaction.Reaction
                user: Union[discord.Member, discord.User]
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await message.edit(
                    content=f'{ctx.author.name} wanted to start a game of Four In A Row, but it timed out...')
                await message.clear_reactions()
                return
            else:
                tile = None
                for t in tiles:
                    if t.emoji == reaction.emoji:
                        tile = t
                        tiles.clear()
                player_two = Player(user.id, tile)
                await message.edit(
                    content=message.content + f'\n{user.name} picked {tile.name}{tile.emoji}.\nThe game is now ready to start!')
                await message.clear_reactions()
                await slp(5)

        await self.start_game(message, player_one, player_two)

    async def start_game(self, message: discord.Message, player_one: Player, player_two: Player):
        if not (message and player_one and player_two):
            return

        game = FIAR(self.empty_tile, player_one, player_two)

        def check(reaction: discord.reaction.Reaction, user: Union[discord.Member, discord.User]) -> bool:
            if user.id != game.current_player().discord_id or message.id != reaction.message.id:
                return False
            key = str(reaction)
            if key in self.column_reactions.keys() and game.fullness[self.column_reactions[key]] < FIAR.HEIGHT:
                return True
            return False

        while not game.is_full():
            numbers = ''.join(self.column_reactions.keys())
            await message.edit(
                content=f'**Turn {game.turn + 1}**\n{game.current_player().tile.emoji}<@{game.current_player().discord_id}>\'s turn.\n{numbers}\n{game.emoji_board()}\n{numbers}')

            for i in range(min(len(self.column_reactions.keys()), FIAR.WIDTH)):
                if game.fullness[i] < FIAR.HEIGHT:
                    await message.add_reaction(self.inverse_column_reactions[i])

            try:
                reaction: discord.reaction.Reaction
                user: Union[discord.Member, discord.User]
                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await message.edit(
                    content=f'**Game Ended on turn {game.turn + 1}.**\n{game.emoji_board()}\n<@{game.current_player().discord_id}> took too long to move, so the game goes to <@{game.other_player().discord_id}>\nThanks for playing!')
                await message.clear_reactions()
                return
            else:
                game.insert(self.column_reactions[str(reaction)])
                await message.clear_reactions()

                if game.winner:
                    await message.edit(
                        content=f'**<@{game.winner.discord_id}> won in {game.turn} turns!**\n{game.emoji_board()}\nThanks for playing!')
                    return

        await message.edit(content=f'**No winner...**\n{game.emoji_board()}\n Thanks for playing {game.player_one.discord_id} and {game.player_two.discord_id}!')


def setup(bot: commands.Bot):
    bot.add_cog(FourInARow(bot))
