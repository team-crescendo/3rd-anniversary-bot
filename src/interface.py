import asyncio
from typing import List

import discord
from discord.ext import commands


async def is_confirmed(ctx: commands.Context, message: discord.Message) -> bool:
    emojis = ["⭕", "❌"]
    for emoji in emojis:
        await message.add_reaction(emoji)

    def _check(reaction, user):
        return reaction.message.id == message.id and user == ctx.author

    try:
        reaction, _ = await ctx.bot.wait_for("reaction_add", check=_check, timeout=60.0)
        return reaction.emoji == "⭕"
    except asyncio.TimeoutError:
        return False


async def wait_for_reaction(
    ctx: commands.Context, message: discord.Message, emoji: str
):
    await message.add_reaction(emoji)

    def _check(reaction, user):
        return (
            reaction.message.id == message.id
            and user == ctx.author
            and str(reaction) == emoji
        )

    await ctx.bot.wait_for("reaction_add", check=_check)


async def wait_for_multiple_reactions(
    ctx: commands.Context, message: discord.Message, emojis: List[str]
) -> str:
    await asyncio.gather(*[message.add_reaction(emoji) for emoji in emojis])

    def _check(reaction, user):
        return (
            reaction.message.id == message.id
            and user == ctx.author
            and str(reaction) in emojis
        )

    reaction, _ = await ctx.bot.wait_for("reaction_add", check=_check)
    return str(reaction)
