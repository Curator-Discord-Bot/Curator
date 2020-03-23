from random import choice
from discord.ext.commands import Context


def on_ready() -> str:
    return choice(('Hey there:smirk:', 'Hey!:smiley:', 'G\'day people:wave:', 'Hi, I\'m alive!', 'Hi, how are ya?', 'Thanks for giving me life!:smiling_face_with_3_hearts:', 'Feels good to be back!'))


def on_load() -> str:
    return choice((':mechanical_arm:', 'Growing stronger!'))


def on_reload() -> str:
    return choice((':arrows_counterclockwise:', ':arrows_clockwise:', 'Updated this part.'))


def on_unload() -> str:
    return choice((':flushed:', 'Ouch!', 'You psychopath!'))


def refuse_logout() -> str:
    return choice(('No!<:diamond_sword:495592395631493130>', 'Not today, my friend:smiling_imp:', 'How about no?', 'That\'s not happening I\'m afraid'))


def on_logout(ctx: Context) -> str:
    return choice((':dizzy_face:', ':head_bandage:', ':dagger:', f'Et tu, {ctx.author.name}?', 'Murderer!'))


def logout_log() -> str:
    return choice(('Logged out', 'I\'m out!', 'I was successfully killed', 'Terminated'))


def collect(ctx: Context) -> str:
    return choice(('There you go.', f'Happy now, {ctx.author.name}?', 'Stop being so greedy!'))
