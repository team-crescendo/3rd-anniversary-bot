from typing import Optional

from discord.ext import commands

from models import session_scope
from models.user import User


def get_user(session, user_id) -> Optional[User]:
    return session.query(User).filter(User.id == user_id).one_or_none()


class Sticker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="스티커")
    async def show_sticker(self, ctx):
        with session_scope() as session:
            user = get_user(session, ctx.author.id)
            sticker = user.sticker if user is not None else 0

            await ctx.send(f"스티커를 `{sticker}`장 보유하셨습니다.")


def setup(bot):
    bot.add_cog(Sticker(bot))
