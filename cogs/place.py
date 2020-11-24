import discord
from discord.ext import commands
from PIL import Image, ImagePalette
from cogs.utils import color
from cogs.utils import formats
from io import BytesIO

size = 100
PLACE = Image.new('RGB', (size, size), color=(255, 255, 255))


class Place(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, name='place')
    async def base(self, ctx: commands.Context):
        """The base command for place"""
        await ctx.send(f'This is the base Place command. See `{ctx.prefix}help place` for help on other commands.')

    @base.command()
    async def pixel(self, ctx: commands.Context, pixel_color: str, x: int, y: int):
        upper_color = pixel_color.upper()
        if upper_color not in color.COLOR_NAMES:
            await ctx.send(f'Color must be be on of {formats.human_join(color.COLOR_NAMES)}.')
            return
        if not 0 <= x < size:
            await ctx.send(f'X must be be in range 0-{size - 1}, you supplied {x}.')
            return
        if not 0 <= y < size:
            await ctx.send(f'Y must be be in range 0-{size - 1}, you supplied {y}.')
            return
        pixel_rgb = color.COLOR_MAP[upper_color]
        if PLACE.getpixel((x, y)) == pixel_rgb:
            await ctx.send(f'That pixel is already {upper_color}.')
            return
        PLACE.putpixel((x, y), pixel_rgb)
        await ctx.send(f'Changed pixel at (x:{x},y:{y}) to {upper_color}.')

    @base.command()
    async def image(self, ctx: commands.Context):
        with BytesIO() as buffer:
            PLACE.save('place.png', 'PNG')
            PLACE.save(buffer, 'PNG')
            buffer.seek(0)
            await ctx.send(file=discord.File(fp=buffer, filename='place.png'))


def setup(bot: commands.Bot):
    bot.add_cog(Place(bot))


def teardown():
    """Code to be executed when the cog unloads. Cannot be a coroutine. This function is not required."""
