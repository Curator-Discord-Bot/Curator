import discord
from discord.ext import commands
from bot import Curator
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


def factorize(n):
    last = 2
    while n > 1:
        for i in range(last, n + 1):
            if n % i == 0:
                n //= i
                last = i
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
    def __init__(self, bot: Curator):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def math(self, ctx: commands.Context):
        """Math and number commands."""
        await ctx.send(f'A collection of useful math commands! See `{ctx.prefix}help math`.')

    @math.command(usage='<number>')
    async def primes(self, ctx: commands.Context, number: int):
        """Compute all the prime numbers up to the input value."""
        if number > 10000:
            await ctx.send('There\'s a limit at 10000.')
        else:
            await ctx.send(human_join([str(i) for i in primes(number)], final='and'))

    @math.command(aliases=['factorise'], usage='<number>')
    async def factorize(self, ctx: commands.Context, number: int):
        """Computes the prime factors of a number."""
        if number > 100000:
            await ctx.send('There\'s a limit at 100000.')
        else:
            await ctx.send(human_join([str(i) for i in factorize(number)], final='and'))

    @math.command(usage='<digits>')
    async def pi(self, ctx: commands.Context, digits: Optional[int]):
        """Displays pi with a given number of digits."""
        if digits is None or digits < 1:
            digits = 100
        elif digits > 1999:
            digits = 1999

        await ctx.send(pi(digits))


def setup(bot: Curator):
    bot.add_cog(Math(bot))
