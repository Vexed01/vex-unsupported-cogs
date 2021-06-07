from redbot.core.bot import Red
from .madtranslate import MadTranslate


def setup(bot: Red):
    bot.add_cog(MadTranslate(bot))