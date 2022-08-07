import aiohttp
import os, pickle
import urllib.parse
from dataclasses import dataclass
from config import Config

from http.cookiejar import MozillaCookieJar
import requests

from discoveryHttp.http import Http

class DiscoveryApi(Http):
    @dataclass
    class DiscoveryUrl:
        search: str = "https://us1-prod-direct.discoveryplus.com/cms/routes/search/result?include=default&decorators=viewingHistory,isFavorite,playbackAllowed&contentFilter[query]={searchTerm}&page[items.number]=1&page[items.size]=30"
        showMetadata: str = "https://us1-prod-direct.discoveryplus.com/cms/routes/show/{url_slug}?include=default"
        seasonMetadata: str = "https://us1-prod-direct.discoveryplus.com/cms/collections/89438300356657080631189351362572714453?include=default&decorators=viewingHistory,isFavorite,playbackAllowed&pf[seasonNumber]={season}&pf[show.id]={show_id}"
        showDownloadUrl: str = "https://www.discoveryplus.com/video/{urlSlug}"

    def __init__(self, config: Config):
        super().__init__(config)

    def _retrieveJsonData(self, url: str):
        data = self._session.get(url)
        return data.json()

    def getShowMetadata(self, urlSlug: str):
        url = self.DiscoveryUrl.showMetadata.format(url_slug = urlSlug)
        return self._retrieveJsonData(url)

    def getSeasonMetadata(self, urlSlug: str, showId: int, season: int):
        url = self.DiscoveryUrl.seasonMetadata.format(show_id = showId, season = season)
        return self._retrieveJsonData(url)

    async def getShowMetadataAsync(self, urlSlug: str):
        url = self.DiscoveryUrl.showMetadata.format(url_slug = urlSlug)
        return await self.getJsonAsync(url)

    async def getSeasonMetadataAsync(self, showId: int, season: int):
        url = self.DiscoveryUrl().seasonMetadata.format(show_id = showId, season = season)
        return await self.getJsonAsync(url)