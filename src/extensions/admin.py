import os
from datetime import datetime

import psutil
from discord.ext import commands

from interface import is_confirmed


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(brief="Hot-load specific modules.")
    async def reload(self, ctx, path):
        self.bot.reload_extension(f"extensions.{path}")
        await ctx.send(f"Successfully reloaded `{path}`!")

    @commands.command(brief="Check the server uptime and the bot uptime.")
    async def uptime(self, ctx):
        now = datetime.now()
        server_uptime = now - datetime.fromtimestamp(psutil.boot_time())
        python_uptime = now - datetime.fromtimestamp(
            psutil.Process(os.getpid()).create_time()
        )

        await ctx.send(
            f"**Server Uptime** {server_uptime}\n" + f"**Bot Uptime** {python_uptime}"
        )

    @commands.command(brief="Shutdown the bot.")
    async def shutdown(self, ctx):
        prompt = await ctx.send("Are you really want to shutdown this bot?")
        if await is_confirmed(ctx, prompt):
            await ctx.send("OK, bye!")
            await ctx.bot.logout()


def setup(bot):
    bot.add_cog(Admin(bot))
