import json
import os
import re
from io import BytesIO
from random import choice

import discord
from discord.ext import commands

from models import session_scope
from models.quiz import Quiz, get_current_quiz, select_random_quiz
from models.user import add_sticker
from utils.permission import is_admin


CHOSUNG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"


def mask_name(name: str) -> str:
    result = ""
    for char in name:
        if "가" <= char <= "힣":
            result += CHOSUNG[(ord(char) - ord("가")) // 588]
            continue

        if char == " ":
            result += " "
            continue

        result += "?"

    return result


def to_embed(quiz: Quiz) -> discord.Embed:
    return discord.Embed(title=quiz.hint, description="펫 외관의 이름을 맞춰보세요!").set_image(
        url=quiz.image
    )


class QuizManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quiz_channel_id = int(os.getenv("QUIZ_CHANNEL"))

    @commands.command(name="퀴즈업뎃")
    async def load_quiz(self, ctx):
        io = BytesIO()
        await ctx.message.attachments[0].save(io)

        with session_scope() as session:
            instances = [Quiz(**instance) for instance in json.load(io)]
            session.add_all(instances)

        await ctx.send(f"`{len(instances)}`개 데이터를 추가했습니다.")

    @property
    def quiz_channel(self) -> discord.TextChannel:
        return self.bot.get_channel(self.quiz_channel_id)

    def cog_check(self, ctx):
        return is_admin(ctx.author)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != self.quiz_channel_id:
            return

        with session_scope() as session:
            quiz = get_current_quiz(session)
            if quiz is None:
                return

            if message.content == quiz.answer:
                await message.channel.send(
                    f"{message.author.mention}, 정답! **{quiz.answer}**\n"
                    + "스티커 `1`장을 지급합니다."
                )
                add_sticker(session, message.author.id, 1)
                quiz.display = False
                return

            if len(message.content) != len(quiz.answer):
                return

            new_hint = ""
            for i in range(len(message.content)):
                if quiz.answer[i] == quiz.hint[i]:
                    new_hint += quiz.answer[i]
                    continue

                if quiz.answer[i] == message.content[i]:
                    new_hint += quiz.answer[i]
                    continue

                new_hint += quiz.hint[i]

            if new_hint != quiz.hint:
                quiz.hint = new_hint

                prompt = await self.quiz_channel.fetch_message(quiz.message_id)
                await prompt.edit(embed=to_embed(quiz))
                await message.channel.send(
                    f"{message.author.mention}, 근접했습니다! **{quiz.hint}**"
                )

    @commands.command(name="퀴즈추가")
    async def new_quiz(self, ctx):
        with session_scope() as session:
            old_quiz = get_current_quiz(session)
            if old_quiz is not None:
                old_quiz.display = False

            quiz = select_random_quiz(session)
            quiz.hint = mask_name(quiz.answer)
            quiz.message_id = (await self.quiz_channel.send(embed=to_embed(quiz))).id

    @commands.command(name="힌트추가")
    async def new_hint(self, ctx):
        with session_scope() as session:
            quiz = get_current_quiz(session)

            candidates = []
            for i in range(len(quiz.answer)):
                if quiz.hint[i] == quiz.answer[i]:
                    continue

                candidates.append(quiz.hint[:i] + quiz.answer[i] + quiz.hint[i + 1 :])

            if len(candidates) < 2:
                return

            quiz.hint = choice(candidates)
            prompt = await self.quiz_channel.fetch_message(quiz.message_id)
            await prompt.edit(embed=to_embed(quiz))


def setup(bot):
    bot.add_cog(QuizManager(bot))
