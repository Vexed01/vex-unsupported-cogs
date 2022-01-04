import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List

import aiohttp
import feedparser
from asyncache import cached
from cachetools import TTLCache
from dateutil.parser import parse as parse_date

from .errors import NoResults

log = logging.getLogger("red.vex.podcasts.api")


@dataclass
class Show:
    name: str
    artwork: str
    feed_url: str
    itunes_id: int


@dataclass
class Episode:
    name: str
    audio_url: str
    published: datetime


class PodcastSearch:
    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()

    @cached(cache=TTLCache(maxsize=128, ttl=86400))  # 1 day
    async def search_show(self, query: str) -> Show:
        """Search for a podcast by name."""
        url = f"https://itunes.apple.com/search?term={query}&media=podcast&entity=podcast&limit=1"

        async with self.session.get(url) as resp:
            data = await resp.text()  # it is json but not .json() able
            jdata = json.loads(data)

        if jdata["resultCount"] == 0:
            raise NoResults("No search results found")

        feed_url = jdata["results"][0]["feedUrl"]
        artwork = jdata["results"][0]["artworkUrl100"]
        name = jdata["results"][0]["collectionName"]
        itunes_id = jdata["results"][0]["collectionId"]

        show = Show(name=name, artwork=artwork, feed_url=feed_url, itunes_id=itunes_id)
        log.debug(f"Found show {show}")
        return show

    @cached(cache=TTLCache(maxsize=128, ttl=86400))  # 1 day
    async def lookup_show(self, itunes_id: str) -> Show:
        """Search for a podcast by iTunes ID."""
        url = f"https://itunes.apple.com/lookup?id={itunes_id}"

        async with self.session.get(url) as resp:
            data = await resp.text()  # it is json but not .json() able
            jdata = json.loads(data)

        if jdata["resultCount"] == 0:
            raise NoResults("No search results found")

        feed_url = jdata["results"][0]["feedUrl"]
        artwork = jdata["results"][0]["artworkUrl100"]
        name = jdata["results"][0]["collectionName"]
        itunes_id = jdata["results"][0]["collectionId"]

        show = Show(name=name, artwork=artwork, feed_url=feed_url, itunes_id=itunes_id)
        log.debug(f"Found show {show}")
        return show

    @cached(cache=TTLCache(maxsize=128, ttl=60 * 15))  # 15 min
    async def get_episodes(self, feed: str) -> List[Episode]:
        """Get all the episodes from a podcast feed."""
        async with self.session.get(feed) as resp:
            rdata = await resp.text()
            data = feedparser.parse(rdata)

        episodes = []
        for episode in data["entries"]:
            try:
                episodes.append(
                    Episode(
                        name=episode["title"],
                        audio_url=episode["enclosures"][0]["href"],
                        published=parse_date(episode["published"]),
                    )
                )
            except Exception as e:
                log.debug(f"Could not parse an episode:\n{episode}", exc_info=e)

        if len(episodes) == 0:  # all eps failed
            raise NoResults("No episodes found")

        return episodes
