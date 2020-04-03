from random import choice
from discord.ext.commands import Context


def on_ready() -> str:
    return choice(('Hey there:smirk:', 'Hey!:smiley:', 'G\'day people:wave:', 'Hi, I\'m alive!', 'Hi, how are ya?',
                   'Thanks for giving me life!:smiling_face_with_3_hearts:', 'Feels good to be back!'))


def on_load() -> str:
    return choice((':mechanical_arm:', 'Growing stronger!', 'I can feel the power!'))


def on_reload() -> str:
    return choice((':arrows_counterclockwise:', ':arrows_clockwise:', 'Updated this part.'))


def on_unload() -> str:
    return choice((':flushed:', 'Ouch!', 'You psychopath!', 'Aaah, my arm!'))


def refuse_logout() -> str:
    return choice(('No!<:diamond_sword:495592395631493130>', 'Not today, my friend:smiling_imp:', 'How about no?',
                   'That\'s not happening I\'m afraid'))


def on_logout(ctx: Context) -> str:
    return choice((':dizzy_face:', ':head_bandage:', ':dagger:', f'Et tu, {ctx.author.name}?', 'Murderer!',
                   'Noooooooooooooooo...', f'Okay, master {ctx.author.name}'))


def logout_log(bot_name) -> str:
    return choice(
        ('Logged out', 'I\'m out!', 'I was successfully killed', 'Terminated', f'{bot_name} has left the chat.'))


def hello(ctx: Context) -> str:
    role: str = choice(list(map(str, ctx.author.roles[1:])))
    return choice(('Hey', 'Hello', 'Hi', 'Ey', 'Yo', 'Sup', ':wave:', 'Good to see you', 'Greetings', 'Peace')) + ', ' \
           + choice((ctx.author.name, 'dude', 'buddy', 'mate', choice(('bro', 'brother')), 'man', 'there', 'silly',
                     'you', 'master', 'traveler', 'fancypants', 'human', (role if len(role) > 0 else 'nobody'))) + '!'


def collect(ctx: Context) -> str:
    return choice(('There you go.', f'Happy now, {ctx.author.name}?', 'Stop being so greedy!'))
