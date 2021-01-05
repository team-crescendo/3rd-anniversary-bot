from typing import Optional
import discord
from discord.ext import commands

from models import session_scope
from models.rule import Rule, get_rule, list_all_rules
from utils.permission import is_admin


class RuleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        return is_admin(ctx)

    @commands.command(name="규칙목록")
    async def list_rules(self, ctx):
        with session_scope() as session:
            content = "\n".join(repr(rule) for rule in list_all_rules(session))
            if not content:
                await ctx.send("규칙 없음")
                return

            await ctx.send(content, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(name="규칙추가", brief="<이름> <#채널명> <:이모지:> [스티커 개수] [@보상 역할]")
    async def add_rule(
        self,
        ctx,
        name: str,
        channel: discord.TextChannel,
        emoji: str,
        reward_sticker: Optional[int],
        reward_role: Optional[discord.Role],
    ):
        with session_scope() as session:
            rule = Rule(
                name=name, by_admin=True, channel_id=channel.id, emoji=str(emoji)
            )

            if reward_sticker is not None:
                rule.reward_sticker = reward_sticker

            if reward_role is not None:
                rule.reward_role_id = reward_role.id

            session.add(rule)
            session.commit()
            await ctx.send(f"규칙 #{rule.id} 추가됨!")

    @commands.command(name="규칙삭제")
    async def remove_rule(self, ctx, rule_id: int):
        with session_scope() as session:
            rule = get_rule(session, rule_id)
            if rule is None:
                await ctx.send(f"규칙 #{rule_id} 찾을 수 없습니다.")
                return

            session.delete(rule)
            await ctx.send(f"규칙 #{rule.id} 삭제함!")


def setup(bot):
    bot.add_cog(RuleManager(bot))
