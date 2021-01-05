import os

from discord.ext.commands import Context


def is_admin(ctx: Context) -> bool:
    admin_role_id = int(os.getenv("ADMIN_ROLE"))
    return any(role.id == admin_role_id for role in ctx.author.roles)
