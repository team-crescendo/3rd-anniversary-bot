import os

from typing import List, Optional
import discord
from discord.ext import commands

from models import session_scope
from models.rule import Rule, get_rule, list_all_rules
from models.user import User, get_or_create_user
from utils.permission import is_admin


class RuleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def update_channel(self) -> discord.TextChannel:
        return self.bot.get_channel(int(os.getenv("UPDATE_CHANNEL")))

    def cog_check(self, ctx):
        return is_admin(ctx.author)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return

        if payload.guild_id != self.bot.guild.id:
            return

        with session_scope() as session:
            attacher = await self.bot.guild.fetch_member(payload.user_id)
            if is_admin(attacher):
                channel = await self.bot.fetch_channel(payload.channel_id)
                recipient = (await channel.fetch_message(payload.message_id)).author
                await self.apply_rules(
                    await self.get_rules_by_admin_reaction(
                        session, recipient.id, payload.channel_id, str(payload.emoji)
                    ),
                    get_or_create_user(session, recipient.id),
                    recipient,
                )

            await self.apply_rules(
                await self.get_rules_by_self_reaction(
                    session, attacher.id, payload.message_id, str(payload.emoji)
                ),
                get_or_create_user(session, attacher.id),
                attacher,
            )

    async def get_rules_by_admin_reaction(
        self, session, user_id: int, channel_id: int, emoji: str
    ) -> List[Rule]:
        return (
            session.query(Rule)
            .filter_by(by_admin=True, channel_id=channel_id, emoji=emoji)
            .filter(~Rule.users.any(id=user_id))
            .all()
        )

    async def get_rules_by_self_reaction(
        self, session, user_id: int, message_id: int, emoji: str
    ) -> List[Rule]:
        return (
            session.query(Rule)
            .filter_by(by_admin=False, message_id=message_id, emoji=emoji)
            .filter(~Rule.users.any(id=user_id))
            .all()
        )

    async def apply_rules(
        self, rules: List[Rule], recipient: User, author: discord.User
    ):
        sticker_sum = 0
        for rule in rules:
            recipient.rules.append(rule)
            sticker_sum += rule.reward_sticker
            if rule.reward_role_id is not None:
                await author.add_roles(
                    self.update_channel.guild.get_role(rule.reward_role_id)
                )

        if sticker_sum == 0:
            return

        old_sticker = recipient.sticker
        recipient.sticker = min(old_sticker + sticker_sum, 20)

        if old_sticker == 0:
            content = (
                f"{author.mention}, **팀 크레센도 3주년 이벤트**에 참여하신 것을 환영합니다!\n"
                + "이 채널에서 `ㅋ 스티커` 명령어로 스티커 개수를 확인할 수 있어요."
            )
        elif old_sticker + sticker_sum > recipient.sticker:
            content = (
                f"{author.mention}, 스티커 {sticker_sum}장을 받았습니다!\n"
                + "현재 스티커를 `20`장 (**최대 장수**) 갖고 있습니다."
            )
        else:
            content = (
                f"{author.mention}, 스티커 {sticker_sum}장을 받았습니다!\n"
                + f"현재 스티커를 `{recipient.sticker}`장 갖고 있습니다."
            )

        await self.update_channel.send(content)

    @commands.command(name="규칙목록")
    async def list_rules(self, ctx):
        with session_scope() as session:
            content = "\n".join(repr(rule) for rule in list_all_rules(session))
            if not content:
                await ctx.send("규칙 없음")
                return

            await ctx.send(content, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(name="규칙추가", brief="<이름> <#채널명> <:이모지:> [스티커 개수] [@보상 역할]")
    async def add_rule_by_admin(
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
            self.bot.logger.info("rule add: " + repr(rule))
            await ctx.send(f"규칙 #{rule.id} 추가됨!")

    @commands.command(name="반응추가", brief="<이름> <메시지URL> <:이모지:> [스티커개수] [@보상 역할]")
    async def add_rule_by_self(
        self,
        ctx,
        name: str,
        message: discord.Message,
        emoji: str,
        reward_sticker: Optional[int],
        reward_role: Optional[discord.Role],
    ):
        with session_scope() as session:
            rule = Rule(
                name=name, by_admin=False, message_id=message.id, emoji=str(emoji)
            )

            if reward_sticker is not None:
                rule.reward_sticker = reward_sticker

            if reward_role is not None:
                rule.reward_role_id = reward_role.id

            session.add(rule)
            session.commit()
            self.bot.logger.info("rule add: " + repr(rule))
            await message.add_reaction(emoji)
            await ctx.send(f"규칙 #{rule.id} 추가됨!")

    @commands.command(name="규칙삭제")
    async def remove_rule(self, ctx, rule_id: int):
        with session_scope() as session:
            rule = get_rule(session, rule_id)
            if rule is None:
                await ctx.send(f"규칙 #{rule_id} 찾을 수 없습니다.")
                return

            session.delete(rule)
            self.bot.logger.info("rule delete: " + repr(rule))
            await ctx.send(f"규칙 #{rule.id} 삭제함!")


def setup(bot):
    bot.add_cog(RuleManager(bot))
