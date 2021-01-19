import csv
from typing import Awaitable, Optional, TextIO
from io import BytesIO, TextIOWrapper

import discord
from discord.ext import commands
from interface import wait_for_reaction

from models import session_scope
from models.user import add_sticker
from models.xsi_reward import XsiReward, get_xsi_reward
from utils.permission import check_admin


EMOJI_OK = "🙆"


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

    @commands.command(name="보상")
    async def get_reward(self, ctx):
        xsi_prompt = self._check_and_give_xsi_reward(ctx)
        if xsi_prompt is not None:
            await wait_for_reaction(ctx, await xsi_prompt, EMOJI_OK)

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


def setup(bot):
    bot.add_cog(RewardManager(bot))
