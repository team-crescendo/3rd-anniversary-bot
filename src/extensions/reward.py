import csv
import os
import string
from datetime import datetime, timedelta
from io import BytesIO, TextIOWrapper
from math import ceil
from random import choice
from typing import Awaitable, Optional
from urllib import parse

import discord
from discord.ext import commands
from interface import wait_for_multiple_reactions, wait_for_reaction

from models import session_scope
from models.user import add_sticker, count_formlinks, get_user, search_by_formlink
from models.xsi_reward import XsiReward, get_xsi_reward
from utils.forte import ForteError, give_forte_point
from utils.permission import check_admin


EMOJI_OK = "🙆"
EMOJI_KEYCAP_1 = "1️⃣"
EMOJI_KEYCAP_2 = "2️⃣"

forte_embed = discord.Embed(
    title="포르테 상점 안내",
    description="[FORTE 소개](https://cafe.naver.com/teamcrescendocafe/book5101938/699)\n"
    "[상점 방문하기](https://forte.team-crescendo.me/login/discord)",
)

FORMLINK_MAX = 100


def timedelta_to_string(td: timedelta) -> str:
    if td.total_seconds() < 60:
        return f"{td.total_seconds():.1f}초"

    minutes, seconds = divmod(ceil(td.total_seconds()), 60)
    if minutes < 60:
        return f"{minutes}분 {seconds}초"

    hours, minutes = divmod(minutes, 60)
    return f"{hours}시간 {minutes}분 {seconds}초"


def make_random_string(size: int = 6) -> str:
    return "".join(choice(string.ascii_lowercase) for _ in range(size))


class RewardManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="크시보상업뎃")
    @commands.check(check_admin)
    async def load_xsi_rewards(self, ctx):
        buffer = BytesIO()
        text_file = TextIOWrapper(buffer, encoding="utf-8")
        await ctx.message.attachments[0].save(buffer)

        instances = [
            XsiReward(id=int(id), sticker=int(num)) for id, num in csv.reader(text_file)
        ]
        with session_scope() as session:
            session.add_all(instances)
            await ctx.send(f"`{len(instances)}`개 데이터를 추가했습니다.")

        buffer.close()

    @commands.command(name="보상현황")
    async def reward_status(self, ctx):
        with session_scope() as session:
            await ctx.send(
                f"{ctx.author.mention}, {count_formlinks(session)}명이 **현물 스티커 교환**을 신청했습니다."
            )

    @commands.command(name="유저검색")
    @commands.check(check_admin)
    async def reward_test(self, ctx, formlink: str):
        with session_scope() as session:
            user = search_by_formlink(session, formlink)
            if user is None:
                await ctx.send(f"{ctx.author.mention}, 해당하는 사용자를 찾지 못했습니다.")
                return

            await ctx.send(f"{ctx.author.mention}, {user}")

    @commands.command(name="보상검색")
    @commands.check(check_admin)
    async def search_reward(self, ctx, discord_user: discord.User):
        with session_scope() as session:
            user = get_user(session, discord_user.id)
            if user is None or user.formlink is None:
                await ctx.send(f"{ctx.author.mention}, 해당 사용자는 현물 교환 신청을 안 했습니다.")
                return

            url = os.getenv("STICKER_FORM_URL").format(parse.quote(user.get_info()))
            await ctx.send(f"{ctx.author.mention}, {discord_user.mention}: {url}")

    @commands.command(name="보상")
    async def get_reward(self, ctx):
        xsi_prompt = self._check_and_give_xsi_reward(ctx)
        if xsi_prompt is not None:
            await wait_for_reaction(ctx, await xsi_prompt, EMOJI_OK)

        with session_scope() as session:
            user = get_user(session, ctx.author.id)
            if user is None:
                await ctx.send(f"{ctx.author.mention}, 이벤트에 참여한 기록이 없습니다.")
                return

            if user.formlink is not None:
                await self.send_formlink(ctx, user.get_info())
                return

            if user.get_reward:
                await ctx.send(f"{ctx.author.mention}, 이미 보상을 선택했습니다.")
                return

            sticker = user.sticker
            if sticker < 5:
                await ctx.send(
                    f"{ctx.author.mention}, 아쉽지만 보상은 스티커 5장 이상부터 받을 수 있습니다. (현재 `{sticker}장` 보유)"
                )
                return

        emojis = [EMOJI_KEYCAP_1]
        description = f"{EMOJI_KEYCAP_1} 포르테 포인트로 교환 (스티커 보유 개수 ✕ 5P)\n"

        if sticker >= 10:
            remaining_time = (
                datetime.fromisoformat("2021-01-20T21:00:00") - datetime.now()
            )
            if remaining_time > timedelta(0):
                description += (
                    "🔒 **현물 스티커로 교환** (국내 한정 우편 발송)"
                    f" : `{timedelta_to_string(remaining_time)}` 남음"
                )
            else:
                description += f"{EMOJI_KEYCAP_2} **현물 스티커로 교환** (국내 한정 우편 발송)"
                emojis.append(EMOJI_KEYCAP_2)

        assert sticker <= 20

        prompt = await ctx.send(
            f"{ctx.author.mention}, 보상을 교환할 방법을 선택해주세요.\n"
            "⚠️ **__`한 번 선택하면 다시 바꿀 수 없습니다!!`__**",
            embed=discord.Embed(
                title=f"보유한 스티커: {sticker}장", description=description.strip()
            ),
        )
        selection = await wait_for_multiple_reactions(ctx, prompt, emojis)

        with session_scope() as session:
            user = get_user(session, ctx.author.id)
            if user.formlink is not None:
                await self.send_formlink(ctx, user.get_info())
                return

            if user.get_reward:
                await ctx.send(f"{ctx.author.mention}, 이미 보상을 선택했습니다.")
                return

            if selection == EMOJI_KEYCAP_1:
                user.get_reward = True
                session.commit()

                try:
                    receipt_id = await give_forte_point(ctx.author.id, 5 * sticker)
                    self.bot.logger.info(
                        f"reward {ctx.author.id} - point {5 * sticker}, receipt_id {receipt_id}"
                    )
                except ForteError as e:
                    user.get_reward = False
                    self.bot.logger.warning(f"reward {ctx.author.id} - forte_fail {e}")
                    if e.status == 404:
                        await ctx.send(
                            f"{ctx.author.mention}, 포르테 상점에서 디스코드로 로그인 한 뒤 다시 시도하세요.",
                            embed=forte_embed,
                        )
                        return

                    await ctx.send(
                        f"{ctx.author.mention}, 알 수 없는 에러로 포르테 포인트 지급에 실패했습니다. 나중에 다시 시도해주세요."
                    )
                    return

                await ctx.send(
                    f"{ctx.author.mention}, {5 * sticker}<:fortepoint:737564157473194014>를 드렸습니다!",
                    embed=forte_embed,
                )
            elif selection == EMOJI_KEYCAP_2:
                if count_formlinks(session) >= FORMLINK_MAX:
                    await ctx.send(
                        f"{ctx.author.mention}, 선착순 {FORMLINK_MAX}명이 다 차서 현물 스티커 신청은 마감되었습니다. 불편을 드려 죄송합니다."
                    )
                    return

                user.get_reward = True
                user.formlink = make_random_string() + str(user.id)[-4:]
                self.bot.logger.info(
                    f"reward {ctx.author.id} - make_link {user.formlink}"
                )
                session.commit()

                await self.send_formlink(ctx, user.get_info())

    def _check_and_give_xsi_reward(self, ctx) -> Optional[Awaitable[discord.Message]]:
        """성공시, 사용자에게 반환할 디스코드 메시지를 반환합니다."""
        with session_scope() as session:
            xsi_reward = get_xsi_reward(session, ctx.author.id)
            if xsi_reward is None:
                return None

            sticker_before, sticker_after = add_sticker(
                session, ctx.author.id, xsi_reward.sticker
            )
            xsi_reward.is_received = True
            session.commit()

            self.bot.logger.info(
                f"xsi_reward {xsi_reward} - user sticker {sticker_before} -> {sticker_after}"
            )
            return ctx.send(
                f"{ctx.author.mention}, **크시봇 3주년 기념 이벤트** 보상을 확인해주세요!",
                embed=discord.Embed(
                    title=f"{xsi_reward.sticker}장 추가 획득!",
                    description=f"스티커 `{sticker_before}장` ➡️ `{sticker_after}장`",
                ).set_footer(
                    text="1/13~1/15 동안 크시 호감도를 50 올릴 때마다 스티커 1장이 지급됩니다. (최대 5장)"
                ),
            )

    async def send_formlink(self, ctx, user_info: str):
        url = os.getenv("STICKER_FORM_URL").format(parse.quote(user_info))
        try:
            await ctx.send(
                f"{ctx.author.mention}, 스티커 현물 교환 신청이 완료되었습니다.\n"
                + "DM이 오지 않는 경우 관리자에게 문의해주세요."
            )
            await ctx.author.send(
                embed=discord.Embed(
                    title="스티커 받으러 가기", description=f"[클릭해서 구글 폼으로 이동]({url})"
                )
            )
        except discord.Forbidden:
            await ctx.send(
                f"{ctx.author.mention}, 이 서버에서 멤버가 보내는 개인 메시지를 허용한 뒤 다시 `ㅋ 보상` 명령어를 입력하세요."
            )


def setup(bot):
    bot.add_cog(RewardManager(bot))
