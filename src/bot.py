import json
import logging
import logging.config
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

with open("logging.json") as f:
    logging.config.dictConfig(json.load(f))


load_dotenv()


class DiscordBot(commands.Bot):
    extension_list = ["extensions.admin", "extensions.sticker", "extensions.rule"]

    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user}")

    async def on_error(self, event, *args, **kwargs):
        self.logger.exception("")

    @property
    def guild(self) -> discord.Guild:
        return self.get_guild(int(os.getenv("GUILD")))

    def __init__(self, logger):
        super().__init__(commands.when_mentioned_or("ㅋ "))
        self.logger = logger
        for ext in self.extension_list:
            self.load_extension(ext)


bot = DiscordBot(logger=logging.getLogger("bot"))


bot.run(os.getenv("BOT_TOKEN"))
