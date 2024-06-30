# one file cog!

import asyncio
from urllib.parse import urlparse

import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, text_to_file


async def setup(bot: Red):
    ret = bot.add_cog(MOBAFire(bot))

    if ret is not None:  # red 3.5 compatibility
        await ret


class MOBAFire(commands.Cog):
    """
    Mobafire cog
    """

    def __init__(self, bot: Red):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    @commands.command(aliases=["mfextract"])
    async def mobafireextract(self, ctx: commands.Context, link: str):
        """
        Extract build data as JSON from MOBAFire
        """
        parsed = urlparse(link)

        if parsed.netloc != "www.mobafire.com":
            await ctx.send("Invalid link")
            return

        async with self.session.post(
            "https://www.binaryalien.net/buildcopier/api/mobafire",
            headers={"content-type": "application/json"},
            data=f'{{"output-title":"","url":"{parsed.geturl()}","build-index":"1"}}',
        ) as resp:
            try:
                data = await resp.text()
            except Exception:
                await ctx.send("Invalid link")
                return
            await ctx.send(files=[text_to_file(data, filename="build.json")])
