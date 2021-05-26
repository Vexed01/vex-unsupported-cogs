from typing import Optional
from redbot.core import commands
from redbot.core.utils.chat_formatting import box
import aiohttp
import random
import asyncio

from urllib.parse import urlencode

from .langs import LANGS

ARROW = " → "

class ForbiddenExc(Exception):
    pass

BASE = "https://clients5.google.com/translate_a/t?"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
}

async def get_translation(ctx, session: aiohttp.ClientSession, sl, tl, q) -> str:
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
    return as_json["sentences"][0]["trans"]


class MadTranslate(commands.Cog):
    """Translate stuff like mad."""

    def __init__(self):
        # wew, nothing to do!
        pass

    @commands.command(aliases=["mtranslate", "mtrans"])
    async def madtranslate(self, ctx: commands.Context, count: Optional[int] = 15, *, text_to_translate: str):
        """Translate something into lots of languages, then back to English!

        Examples:

        `[p]mtrans 10 I like food.`
        `[p]mtrans I like food.`
        `[p]mtrans 25 I like food.`
        """
        if count > 50:
            return await ctx.send("That's a bit big... How about a lower number?")
        q = text_to_translate
        session = aiohttp.ClientSession(headers=HEADERS)
        langs = random.sample(LANGS, k=count)
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
        await ctx.send(
            "Original text: " + box(text_to_translate) + "Translated text: " + box(q) +
            "Languages: " + box(ARROW.join(i[0] for i in langs))
        )

    @commands.command()
    async def mtransfull(self, ctx: commands.Context, count: Optional[int] = 15, *, text_to_translate: str):
        """See the full path of a translation.

        Examples:

        `[p]mtransfull 10 I like food.`
        `[p]mtransfull I like food.`
        `[p]mtransfull 25 I like food.`
        """
        if count > 50:
            return await ctx.send("That's a bit big... How about a lower number?")
        q = text_to_translate
        session = aiohttp.ClientSession(headers=HEADERS)
        langs = random.sample(LANGS, k=count)
        langs.append(("English", "en"))
        sl = "auto"  # auto detect
        text_store = [q]
        async with ctx.typing():
            for _, tl in langs:
                try:
                    det_lang, q = await get_translation(session, sl, tl, q)
                except ForbiddenExc:
                    return await ctx.send("Something went wrong.")
                sl = tl
                text_store.append(q)

        await session.close()
        texts = "\n".join(langs[i][0] + ": " + text_store[i] for i in range(count + 2))
        await ctx.send(texts)
