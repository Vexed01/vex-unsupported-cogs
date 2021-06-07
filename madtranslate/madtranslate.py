from typing import List, Optional, Tuple
import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
import aiohttp
import random
import asyncio
from time import monotonic

from urllib.parse import urlencode

from .langs import LANGS

ARROW = " → "

class ForbiddenExc(Exception):
    pass

BASE = "https://clients5.google.com/translate_a/t?"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}

async def get_translation(ctx: commands.Context, session: aiohttp.ClientSession, sl, tl, q) -> str:
    query = {
        'client': 'dict-chrome-ex',
        'sl'    : sl,
        'tl'    : tl,
        'q'     : q,
    }
    resp = await session.get(BASE + urlencode(query))
    if resp.status == 403:
        raise ForbiddenExc

    as_json = await resp.json()
    if sl == "auto":
        await ctx.send(f"I've detected the input language as {as_json['src']}")
        asyncio.sleep(0.1)
        await ctx.trigger_typing()
    return as_json["sentences"][0]["trans"]

def gen_langs(count: int, seed: Optional[int] = None) -> Tuple[str, List[Tuple[str, str]]]:
    if seed is None:
        seed = random.randrange(100_000, 999_999)
    gen = random.Random(seed)

    count_seed_par = f"{count}-{seed}"
    return count_seed_par, gen.sample(LANGS, k=count)


class MadTranslate(commands.Cog):
    """**Deprecated cog. Moved to main repo at https://github.com/Vexed01/Vex-Cogs**"""

    def __init__(self, bot: Red):
        self.bot = bot
        config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        config.register_global(notified=False)
        self.config = config

        asyncio.create_task(self.maybe_notify())

    async def maybe_notify(self):
        notified = await self.config.notified()
        if notified is False:
            await self.bot.send_to_owners(
                "Hey there! The `madtranslate` cog from Vex's unsupported repo is now on my main, supported repo!\n\n"
                "You can now install it from the repo at https://github.com/Vexed01/Vex-Cogs.\n\n"
                "Please note that the version of this cog on the unsupported repo is now deprecated and will no longer recieve updates.\n\n"
                "This message will only be sent once."
            )
            await self.config.notified.set(True)

    @commands.command(aliases=["mtranslate", "mtrans"])
    async def madtranslate(self, ctx: commands.Context, count: Optional[int] = 15, *, text_to_translate: str):
        """Translate something into lots of languages, then back to English!

        **Examples:**
            - `[p]mtrans This is a sentence.`
            - `[p]mtrans 25 Here's another one.`

        At the bottom of the output embed is a count-seed pair. You can use this with
        the `mtransseed` command to use the same language set.
        """
        if count > 50:
            return await ctx.send("That's a bit big... How about a lower number?")
        q = text_to_translate
        session = aiohttp.ClientSession(headers=HEADERS)
        count_seed, langs = gen_langs(count)
        langs.append(("English", "en"))
        sl = "auto"
        async with ctx.typing():
            for _, tl in langs:
                try:
                    q = await get_translation(ctx, session, sl, tl, q)
                except ForbiddenExc:
                    return await ctx.send("Something went wrong.")
                sl = tl

        await session.close()

        embed = discord.Embed(colour=await ctx.embed_color(), title=f"Translation through {count} languages")
        embed.add_field(name="Original text", value=box(text_to_translate), inline=False)
        embed.add_field(name="Translated text", value=box(q), inline=False)
        embed.add_field(name="Languages", value=box(ARROW.join(i[0] for i in langs)), inline=False)
        embed.set_footer(text=f"count-seed pair: {count_seed}")
        await ctx.send(embed=embed)

    @commands.command()
    async def mtransseed(self, ctx: commands.Context, seed: str, *, text_to_translate: str):
        """Use a count-seed pair to (hopefully) get reproducible results.

        They may be unreproducible if Google Translate changes its translations.

        The count-seed pair is obtained from the main command, `mtrans`, in the embed footer.

        **Examples:**
            - `[p]mtrans 15-111111 This is a sentence.`
            - `[p]mtrans 25-000000 Here's another one.`
        """
        split = seed.split("-")
        if len(split) != 2 or not split[0].isdigit() or not split[1].isdigit() or len(split[0]) > 50 or len(split[1]) != 6:
            return await ctx.send("That count-seed pair doesn't look valid.")
        count, seed = int(split[0]), int(split[1])
        q = text_to_translate
        session = aiohttp.ClientSession(headers=HEADERS)
        count_seed, langs = gen_langs(count, seed)
        langs.append(("English", "en"))
        sl = "auto"
        async with ctx.typing():
            for _, tl in langs:
                try:
                    q = await get_translation(ctx, session, sl, tl, q)
                except ForbiddenExc:
                    return await ctx.send("Something went wrong.")
                sl = tl

        await session.close()

        embed = discord.Embed(colour=await ctx.embed_color(), title=f"Translation through {count} languages")
        embed.add_field(name="Original text", value=box(text_to_translate), inline=False)
        embed.add_field(name="Translated text", value=box(q), inline=False)
        embed.add_field(name="Languages", value=box(ARROW.join(i[0] for i in langs)), inline=False)
        embed.set_footer(text=f"Seed: {count_seed}")
        await ctx.send(embed=embed)
