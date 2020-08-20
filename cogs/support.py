import discord
from discord.ext import commands
from typing import Optional
from copy import copy
from datetime import datetime
import emoji
from .utils.formats import human_join


open_tickets = {}
closed_tickets = {}


class Ticket:
    def __init__(self, client):
        self.client = client
        self.channel = None
        self.channel_members = None
        self.opened_at = datetime.utcnow()
        self.closed_at = None
        self.closed_by = None
        self.close_message = None

    async def create_channel(self, ctx, category):
        self.channel = await category.create_text_channel(f'Ticket {self.client.id}', topic=f'Ticket of {self.client}. Status: open',
                                                          reason=f'Open support ticket with{self.client}.')
        self.channel_members = self.channel.members
        await self.channel.set_permissions(self.client, read_messages=True)
        self.channel_members.append(self.client)
        await self.channel.send(f'This is a channel where you, {self.client.mention}, can privately talk with staff. '
                                f'To end the conversation, use `{ctx.prefix}ticket close`.')
        await ctx.send(f'Successfully opened a new support ticket: {self.channel.mention}.')

    async def close_ticket(self, closer):
        await self.channel.set_permissions(self.client, overwrite=None)
        await self.channel.edit(name='Ticket closed', topic=f'Ticket of {self.client}. Status: closed',
                                reason=f'Close support ticket with {self.client}.')
        self.closed_at = datetime.utcnow()
        self.closed_by = closer
        self.close_message = await self.channel.send(f'This ticket with {self.client.mention} is now closed, '
                                                     f'to delete the channel, react to this message with :x:.')
        await self.close_message.add_reaction(emoji.emojize(':cross_mark:'))
        closed_tickets[self.channel.id] = copy(open_tickets[self.channel.guild.id][self.client.id])
        del (open_tickets[self.channel.guild.id][self.client.id])

    async def delete_channel(self):
        channel_id = self.channel.id
        await self.channel.delete(reason=f'Delete closed support ticket with {self.client}.')
        del (closed_tickets[channel_id])


class Support(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group()
    async def ticket(self, ctx: commands.Context):
        """A ticket tool to talk with staff."""
        if not ctx.invoked_subcommand:
            return await ctx.send(f'Use `{ctx.prefix}ticket open` to open a new support ticket.')

        if ctx.guild.id not in open_tickets.keys():
            open_tickets[ctx.guild.id] = {}

    @ticket.command()
    async def open(self, ctx: commands.Context):
        """Open a support ticket."""
        if not self.bot.server_configs[ctx.guild.id]['ticket_category']:
            return await ctx.send('The ticket tool is disabled on this server, find another way to contact staff.')

        if ctx.author.id in open_tickets[ctx.guild.id].keys():
            return await ctx.send(f'You already have an open ticket: {open_tickets[ctx.guild.id][ctx.author.id].channel.mention}.')

        open_tickets[ctx.guild.id][ctx.author.id] = Ticket(ctx.author)
        await open_tickets[ctx.guild.id][ctx.author.id].create_channel(ctx, self.bot.server_configs[ctx.guild.id]['ticket_category'])

    @ticket.command()
    async def close(self, ctx: commands.Context, user_id: Optional[int]):
        """Close a support ticket."""
        if not user_id and ctx.channel not in [ticket.channel for ticket in open_tickets[ctx.guild.id].values()]:
            return await ctx.send('You are not in an open ticket channel.')
        elif user_id and user_id not in open_tickets[ctx.guild.id].keys():
            return await ctx.send('There is no open ticket with this user.')

        async def cprompt():
            prompt_text = 'Are you sure you want to close this ticket?'
            confirm = await ctx.prompt(prompt_text, reacquire=False)
            if not confirm:
                return await ctx.send('Cancelled.')
            await ticket.close_ticket(ctx.author)

        for ticket in open_tickets[ctx.guild.id].values():
            if ticket.client.id == user_id:
                if ctx.author in ticket.channel_members:
                    await cprompt()
                    return
                else:
                    return await ctx.send('You do not have access to this ticket.')
            elif not user_id and ticket.channel == ctx.channel:
                await cprompt()
                return

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        for ticket in closed_tickets.values():
            if reaction.message.id == ticket.close_message.id and emoji.demojize(str(reaction)) == ':cross_mark:' and not user == self.bot.user:
                await ticket.delete_channel()
                return

    @ticket.command(aliases=['information', 'data'])
    async def info(self, ctx: commands.Context, user_id: Optional[int]):
        """Get all information about a support ticket."""
        if not user_id and ctx.channel not in [ticket.channel for ticket in open_tickets[ctx.guild.id].values()] + [ticket.channel for ticket in closed_tickets.values()]:
            return await ctx.send('You are not in a ticket channel.')
        elif user_id and user_id not in open_tickets[ctx.guild.id].keys():
            return await ctx.send('There is no open ticket with this user.')

        def make_message(ticket):
            """Creates the information embed for a ticket."""
            embed = discord.Embed(title=f'Ticket information', description=f'**Status:** *{"open" if not ticket.closed_at else "closed"}*')
            embed.set_thumbnail(url=ticket.client.avatar_url)
            embed.add_field(name='Opened at (UTC)', value=ticket.opened_at)
            if ticket.closed_at:
                embed.add_field(name='Closed at (UTC)', value=ticket.closed_at)
            embed.add_field(name='Client', value=ticket.client)
            if ticket.closed_by:
                embed.add_field(name='Closed by', value=ticket.closed_by)
            embed.add_field(name='Channel', value=ticket.channel.mention)
            embed.add_field(name='People with access', value=human_join([str(member) for member in ticket.channel_members], final='and'))
            return embed

        for ticket in open_tickets[ctx.guild.id].values():
            if ticket.client.id == user_id:
                if ctx.author in ticket.channel_members:
                    return await ctx.send(embed=make_message(ticket))
                else:
                    return await ctx.send('You do not have access to this ticket.')
            elif not user_id and ticket.channel == ctx.channel:
                return await ctx.send(embed=make_message(ticket))

        ticket = closed_tickets[ctx.channel.id]
        await ctx.send(embed=make_message(ticket))

    @commands.command(hidden=True)
    async def printotickets(self, ctx: commands.Context):
        """Print all open tickets."""
        if ctx.author.id in self.bot.admins:
            print(open_tickets)
            await ctx.send('Check the Python printer output for your results.')
        else:
            await ctx.send('You do not have access to this command.')

    @commands.command(hidden=True)
    async def printctickets(self, ctx: commands.Context):
        """Print all closed tickets"""
        if ctx.author.id in self.bot.admins:
            print(closed_tickets)
            await ctx.send('Check the Python printer output for your results.')
        else:
            await ctx.send('You do not have access to this command.')


def setup(bot: commands.Bot):
    bot.add_cog(Support(bot))
