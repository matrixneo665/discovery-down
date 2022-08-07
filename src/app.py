import argparse
import api.api
import asyncio
import datetime
import os
import pathlib
import logging

from discoveryDownloader import DiscoveryDownloader
from discoveryDownloadQueue import DiscoveryDownloadQueue
from downloadData import DownloadData
from discoveryShowRetriever import DiscoveryShowRetriever
from fileWatcher.folderScanner import FolderScanner
from orm import sessionMaker, createTables
from orm.season import Season
from orm.episode import Episode, VideoData, AudioData, CaptionData, WvKeyCache
from orm.show import Show
from sqlalchemy import select
from typing import Optional
from api.apiDataRetriever import ApiDataRetriever

class DiscoveryDown:
    def __init__(self, config, getMpdDownloadUrl):
        self.scanner = FolderScanner(config.watch)
        self.scanner.onEpisodeDownloadRequested = self.downloadEpisode
        self.parser = DiscoveryShowRetriever(config, sessionMaker)
        self.downloader = DiscoveryDownloader(config, sessionMaker, getMpdDownloadUrl)
        self.queue = DiscoveryDownloadQueue(config, self.downloader)

    async def start(self):
        logging.info('scanner starting')
        self.scanner.start()
        logging.info('scanner started; starting queue')
        await self.queue.start()

    def updateShows(self):
        self.parser.updateAllShowData()

    async def forceDownloadEpisode(self, videoDataId, fileName, type):
        videoId = int(videoDataId)
        with sessionMaker() as session:
            data = DownloadData(fileName, videoId, type = type)
            await self.downloader.downloadEpisode(data)

    def downloadEpisode(self, videoDataId, fileName, type):
        videoId = int(videoDataId)
        data = DownloadData(fileName, videoId, type)

        self.queue.addDownload(data)

    def addShow(self, url: str, tvdbId: Optional[str]):
        show = self.parser.retrieveShowData(url, tvdbId)

        if (not show):
            return "Something went wrong"

        return "Success"

async def main():

    logging.basicConfig(level = logging.INFO)

    logging.info('starting app')

    parser = argparse.ArgumentParser()
    parser.add_argument("-cookie", "-c", default='/config/cookie.txt')
    parser.add_argument("-download", "-d", default="/downloads")
    parser.add_argument("-temp", "-t", default='/temp')
    parser.add_argument("-watch", "-w", default='/pickup')
    parser.add_argument("-api", "-a", default='')
    parser.add_argument("-mpdDir", "-m", default="/config/mpd")
    parser.add_argument("--nowatch", default=False, action="store_true")
    parser.add_argument("--nolog", default=False, action="store_true")

    wvApi = os.environ.get("WV_API_KEY") or None

    config = parser.parse_args()

    if (not config.nolog):
        logging.basicConfig(filename = '/config/down.log', level = logging.INFO)

    if (not config.api or config.api == ''):
        if (wvApi and wvApi != ''):
            config.api = wvApi

    logging.info('Creating sqlite tables')

    createTables()

    logging.info('Created sqlite tables; Configuring data')

    loop = asyncio.get_running_loop()
    down = DiscoveryDown(config, api.api.getMpdDownloadUrl)
    api.api.addShowToDatabase = down.addShow
    api.api.updateShows = down.updateShows
    api.api.apiDataRetriever = ApiDataRetriever(sessionMaker, api.api.getDownloadUrl, config.mpdDir)
    api.api.forceDownload = down.forceDownloadEpisode
    logging.info('Configured data; starting scanner, queue, and API')

    try:
        downloaderTask = loop.create_task(down.start())

        apiServerTask = loop.run_in_executor(None, api.api.start)

        await asyncio.gather(*[downloaderTask, apiServerTask])
        
    except Exception as ex:
        logging.error(f'Error occurred starting app {ex}')
    

asyncio.run(main())