from redbot.core.bot import Red

from podcasts.core import Podcasts



async def setup(bot: Red):
    cog = Podcasts(bot)
    await cog.async_init()
    bot.add_cog(cog)
