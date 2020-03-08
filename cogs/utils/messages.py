from random import choice
from discord.ext.commands import Context


def on_ready() -> str:
    return choice(('Hey there:smirk:', 'Hey!:smiley:', 'G\'day people:wave:', 'Hi, I\'m alive!', 'Hi, how are ya?',
                   'Thanks for giving me life!:smiling_face_with_3_hearts:', 'Feels good to be back!'))


def on_load(ctx: Context) -> str:
    return ':mechanical_arm:'


def on_reload(ctx: Context) -> str:
    return ':arrows_counterclockwise:'


def on_unload(ctx: Context) -> str:
    return choice((':flushed:', 'Ouch!'))


def on_logout(ctx: Context) -> str:
    return choice((':dizzy_face:', ':head_bandage:', ':dagger:', f'Et tu, {ctx.author.name}?'))
