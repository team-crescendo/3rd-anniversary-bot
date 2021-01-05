import discord
from discord.ext import commands

from models import session_scope
from models.user import add_sticker, get_user
from utils.permission import check_admin


class Sticker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="스티커")
    async def show_sticker(self, ctx):
        with session_scope() as session:
            user = get_user(session, ctx.author.id)
            if user is None:
                await ctx.send("아직 스티커를 받지 않았습니다.")
                return

            await ctx.send(f"스티커를 `{user.sticker}`장 보유하셨습니다.")

    @commands.command(name="지급")
    @commands.check(check_admin)
    async def give_sticker(self, ctx, member: discord.Member, amount: int):
        with session_scope() as session:
            add_sticker(session, member.id, amount)
            await ctx.send(f"{member}님께 스티커 `{amount}`장을 지급했습니다.")


def setup(bot):
    bot.add_cog(Sticker(bot))
