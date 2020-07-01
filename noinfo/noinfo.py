from redbot.core import commands

class NoInfo(commands.Cog):
    """This is a local cog, used for testing."""
    @commands.command()
    async def noinfocom(self, ctx):
        """This is a local cog, used for testing."""
        await ctx.send("This is a local cog, used for testing.")