import asyncio
from aiopyarr.models.host_configuration import PyArrHostConfiguration
from aiopyarr.sonarr_client import SonarrClient


class ShowSearcher:
    def __init__(self, sonarrIp: str, port: int, sonarrApiKey: str):
        self.hostConfig = PyArrHostConfiguration(ipaddress = sonarrIp, port = port, api_token = sonarrApiKey)

    async def searchShow(self, term: str):
        async with SonarrClient(host_configuration=self.hostConfig) as client:
            data = await client.async_lookup_series(term = term)

        return data

    def searchShowDPlus(self, term: str):

        return None

        #https://us1-prod-direct.discoveryplus.com/cms/routes/search/result?include=default&decorators=viewingHistory,isFavorite,playbackAllowed&contentFilter[query]=hell's&page[items.number]=1&page[items.size]=30