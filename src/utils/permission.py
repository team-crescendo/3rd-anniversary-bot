import os

import discord
from discord.ext.commands import Context

admin_role_id = int(os.getenv("ADMIN_ROLE"))


def is_admin(member: discord.Member) -> bool:
    return any(role.id == admin_role_id for role in member.roles)


def check_admin(ctx: Context) -> bool:
    return is_admin(ctx.author)
