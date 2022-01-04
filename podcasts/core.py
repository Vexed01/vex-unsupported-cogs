import asyncio

import discord
from lavalink.rest_api import Track
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.errors import CogLoadError
from podcasts.errors import NoResults

from .api import PodcastSearch

from logging import getLogger

try:
    from redbot.core import audio
except ImportError:
    raise CogLoadError("This cog requires the Audio API.")

log = getLogger("red.vex.podcasts.core")

class Podcasts(commands.Cog):
    """Listen to podcasts in Discord."""
    def __init__(self, bot: Red):
        self.bot = bot
        self.api = PodcastSearch()

        asyncio.create_task(self.async_init())

    async def async_init(self):
        await self.bot.wait_until_red_ready()
        await audio.initialize(self.bot, "Podcasts", 418078199982063626)
        # and just like that my audio journey begins

    async def shutdown(self):
        await audio.shutdown("Podcasts", 418078199982063626)
        await self.api.session.close()

    def cog_unload(self):
        asyncio.create_task(self.shutdown())

    @commands.bot_has_permissions(embed_links=True)
    @commands.group(aliases=["podcasts"])
    async def podcast(self, ctx: commands.Context):
        """My audio journey begins. Welcome to hell, me."""

    @podcast.command()
    async def latest(self, ctx: commands.Context, *, podcast: str):
        """Play the latest episode of a podcast."""
        player = audio.get_player(ctx.guild.id)
        if not player:
            if not ctx.author.voice.channel:
                await ctx.send("Connect to a voice channel first.")
                return
            player = await audio.connect(self.bot, ctx.author.voice.channel)

        try:
            show = await self.api.search_show(podcast)
            episode = (await self.api.get_episodes(show.feed_url))[0]
        except NoResults:
            embed = discord.Embed(title="Nothing found.", colour=await ctx.embed_colour())
            await ctx.send(embed=embed)
            return

        track: Track = (await player.get_tracks(episode.audio_url))[0][0]

        # most of the MP3 files this plays are missing the title and author, plus in terms of UI
        # having author as the title of the podcast looks good
        track.title = episode.name
        track.author = show.name

        log.debug(f"Got track {track}")

        await player.play(ctx.author, track=track)

        embed = discord.Embed(
            title="Track Enqueued",
            description=f"**[{track.title} - {track.author}]({track.uri})**",
            colour=await ctx.embed_colour(),
        )
        await ctx.send(embed=embed)

    @podcast.command()
    async def search(self, ctx: commands.Context, *, podcast: str):
        """View episodes of a podcast."""
        try:
            show = await self.api.search_show(podcast)
            episodes = await self.api.get_episodes(show.feed_url)
        except NoResults:
            embed = discord.Embed(title="Nothing found.", colour=await ctx.embed_colour())
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(title=show.name, colour=await ctx.embed_colour())

        for i, episode in enumerate(episodes):
            if i == 9:
                break

            embed.add_field(
                name=f"{i + 1}. {episode.name}",
                value=episode.published.strftime("%a %d %b %Y, %Z"),
                inline=False,
            )

        embed.set_footer(text=f"Click the reaction to play that episode.")

        message = await ctx.send(embed=embed)

        emojis = ReactionPredicate.NUMBER_EMOJIS[1 : len(embed.fields) + 1]
        start_adding_reactions(message, emojis)

        pred = ReactionPredicate.with_emojis(emojis, message, ctx.author)
        try:
            await self.bot.wait_for("reaction_add", check=pred, timeout=60)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            return

        episode = episodes[pred.result]

        log.debug(f"Chosen episode is {episode}")

        player = audio.get_player(ctx.guild.id)
        if not player:
            if not ctx.author.voice.channel:
                await ctx.send("Connect to a voice channel first.")
                return
            player = await audio.connect(self.bot, ctx.author.voice.channel)

        track: Track = (await player.get_tracks(episode.audio_url))[0][0]

        # most of the MP3 files this plays are missing the title and author, plus in terms of UI
        # having author as the title of the podcast looks good
        track.title = episode.name
        track.author = show.name

        log.debug(f"Got track {track}")

        await player.play(ctx.author, track=track)

        embed = discord.Embed(
            title="Track Enqueued",
            description=f"**[{track.title} - {track.author}]({track.uri})**",
            colour=await ctx.embed_colour(),
        )

        await ctx.send(embed=embed)
