WHITE = 0xFFFFFF
LIGHT_GREY = 0xE4E4E4
DARK_GREY = 0x888888
BLACK = 0x222222
PINK = 0xFFA7D1
RED = 0xE50000
ORANGE = 0xE59500
BROWN = 0xA06A42
YELLOW = 0xE5D900
LIGHT_GREEN = 0x94E044
GREEN = 0x02BE01
LIGHT_BLUE = 0x00D3DD
DARK_BLUE = 0x0083C7
BLUE = 0x0000EA
LIGHT_PURPLE = 0xCF6EE4
PURPLE = 0x820080
COLOR_NAMES = ["WHITE", "LIGHT_GREY", "DARK_GREY", "BLACK", "PINK", "RED", "ORANGE", "BROWN", "YELLOW", "LIGHT_GREEN",
               "GREEN", "LIGHT_BLUE", "DARK_BLUE", "BLUE", "LIGHT_PURPLE", "PURPLE"]
COLORS = [WHITE, LIGHT_GREY, DARK_GREY, BLACK, PINK, RED, ORANGE, BROWN, YELLOW, LIGHT_GREEN, GREEN, LIGHT_BLUE,
          DARK_BLUE, BLUE, LIGHT_PURPLE, PURPLE]
COLOR_MAP = dict(zip(COLOR_NAMES, COLORS))


def get_red(color):
    return (color >> 16) & 0xFF


def get_green(color):
    return (color >> 8) & 0xFF


def get_blue(color):
    return color & 0xFF


def get_pallete(colors):
    palette = []
    for color in colors:
        palette.append(get_red(color))
        palette.append(get_green(color))
        palette.append(get_blue(color))
    return palette
