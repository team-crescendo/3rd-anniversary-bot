import asyncio
import json
import os
from typing import List, Set, Optional, Tuple

import discord
from discord.ext import commands

from models import session_scope
from models.user import add_sticker
from utils.permission import is_admin


EMOJI_O = "⭕"
EMOJI_X = "❌"


async def get_response(message: discord.Message) -> Tuple[Set[int], Set[int]]:
    reactions = {EMOJI_O: [], EMOJI_X: []}
    for r in message.reactions:
        reactions[str(r.emoji)] = {u.id async for u in r.users()}

    return (
        reactions[EMOJI_O] - reactions[EMOJI_X],
        reactions[EMOJI_X] - reactions[EMOJI_O],
    )


class OXManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ox_channel_id = int(os.getenv("OX_CHANNEL"))

        with open("src/resources/ox.json", encoding="utf-8") as f:
            self.questions = json.load(f)
        self.waiting_message = None
        self.interrupt = False

    @property
    def ox_channel(self) -> discord.TextChannel:
        return self.bot.get_channel(self.ox_channel_id)

    def cog_check(self, ctx):
        return is_admin(ctx.author)

    @commands.command(name="ox준비")
    async def ready_ox(self, ctx):
        self.waiting_message = await self.send_prompt(
            f"OX 퀴즈에 참여하려면 {EMOJI_O} 이모지**만** 추가해주세요."
        )
        await ctx.send("`crsd ox시작` 명령어로 시작할 수 있습니다.")

    @commands.command(name="ox시작")
    async def start_ox(self, ctx, index: Optional[int] = 0):
        m = await self.ox_channel.fetch_message(self.waiting_message.id)
        o, x = await get_response(m)
        if not o:
            return

        with session_scope() as session:
            for user_id in o:
                add_sticker(session, user_id, 1)

            await self.ox_channel.send(
                "**< 참여자 명단 - 전원에게 스티커 `1`장 지급! >**\n"
                + " ".join([f"<@!{user_id}>" for user_id in o])[:1000]
            )

        self.interrupt = False
        await self.run_ox(o, self.questions[index:])

    @commands.command(name="ox종료")
    async def stop_ox(self, ctx):
        self.interrupt = True
        await ctx.send("ox퀴즈 종료 예약 요청을 진행했습니다.")

    async def run_ox(self, survivors: Set[int], questions: List[dict]):
        for index, data in enumerate(questions):
            m = await self.send_prompt(f"`#{index + 1}` {data['question']}")
            await self.wait(m)
            m = await self.ox_channel.fetch_message(m.id)
            o, x = await get_response(m)

            answer_emoji = {"o": EMOJI_O, "x": EMOJI_X}[data["answer"]]
            await self.ox_channel.send(f"정답 : {answer_emoji}")
            new_survivors = survivors.intersection({"o": o, "x": x}[data["answer"]])
            if not new_survivors:
                await self.ox_channel.send("정답을 맞춘 사람이 없어 탈락시키지 않습니다.")
            else:
                survivors = new_survivors

            await self.ox_channel.send(
                "**< 생존자 명단 >**\n"
                + " ".join([f"<@!{user_id}>" for user_id in survivors])[:1000]
            )

            if len(survivors) == 1:
                await self.ox_channel.send("최후의 생존자가 남아 게임을 종료합니다!")
                return

            if self.interrupt:
                await self.ox_channel.send("관리자에 의해 퀴즈 게임을 종료합니다!")
                return

            await asyncio.sleep(10)

        await self.ox_channel.send("모든 문제를 소진했습니다!")

    async def wait(self, message: discord.Message):
        content = message.content

        remaining_time = 20
        for time in [4, 5, 5, 2, 1, 1, 1]:
            await asyncio.sleep(time)
            remaining_time -= time
            asyncio.create_task(
                message.edit(content=content + f" (`{remaining_time - 1}초` 남음)")
            )

        await asyncio.sleep(remaining_time)

    async def send_prompt(self, content: str) -> discord.Message:
        m = await self.ox_channel.send("> ...")
        await asyncio.gather(m.add_reaction(EMOJI_O), m.add_reaction(EMOJI_X))
        await m.edit(content="> " + content)
        return m


def setup(bot):
    bot.add_cog(OXManager(bot))
