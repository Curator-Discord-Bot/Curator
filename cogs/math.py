import discord
from discord.ext import commands
import math
from .utils.formats import human_join
from typing import Optional


def primes(n):
    if n <= 2:
        return []
    sieve = [True] * (n + 1)
    for x in range(3, int(n ** 0.5) + 1, 2):
        for y in range(3, (n // x) + 1, 2):
            sieve[(x * y)] = False

    return [2] + [i for i in range(3, n, 2) if sieve[i]]


def factors(n):
    while n > 1:
        for i in range(2, n + 1):
            if n % i == 0:
                n //= i
                yield i
                break


def continued_fraction(a, b, base=10):
    """Generate digits of continued fraction a(0)+b(1)/(a(1)+b(2)/(...)."""
    (p0, q0), (p1, q1) = (a(0), 1), (a(1) * a(0) + b(1), a(1))
    k = 1
    while True:
        (d0, r0), (d1, r1) = divmod(p0, q0), divmod(p1, q1)
        if d0 == d1:
            yield d1
            p0, p1 = base * r0, base * r1
        else:
            k = k + 1
            x, y = a(k), b(k)
            (p0, q0), (p1, q1) = (p1, q1), (x * p1 + y * p0, x * q1 + y * q0)


def pi(digits=10):
    cf = continued_fraction(lambda k: 0 if k == 0 else 2 * k - 1,
                                lambda k: 4 if k == 1 else (k - 1) ** 2, 10)
    a = ''
    for k, digit in zip(range(0, digits), cf):
        a += str(digit)
    return '3.' + a[1:]


class Math(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def math(self, ctx: commands.Context):
        await ctx.send(f'A collection of useful math commands! See `{ctx.prefix}help math`.')

    @math.command()
    async def primes(self, ctx: commands.Context, number: int):
        await ctx.send(human_join([str(i) for i in primes(number)], final='and'))

    @math.command(aliases=['factorize', 'factorise'])
    async def factors(self, ctx: commands.Context, number: int):
        await ctx.send(human_join([str(i) for i in factors(number)], final='and'))

    @math.command()
    async def pi(self, ctx: commands.Context, digits: Optional[int]):
        if digits is None or digits < 1:
            digits = 100
        elif digits > 1999:
            digits = 1999

        await ctx.send(pi(digits))


def setup(bot: commands.Bot):
    bot.add_cog(Math(bot))
