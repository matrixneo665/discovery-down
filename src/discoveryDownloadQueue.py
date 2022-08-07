from discoveryDownloader import DiscoveryDownloader
from downloadData import DownloadData

import asyncio
from asyncio import Queue

import logging

class DiscoveryDownloadQueue:
    def __init__(self, config, downloader: DiscoveryDownloader):
        self.max_concurrent_downloads = 4
        self.downloader = downloader
        self._loop = asyncio.get_event_loop()
        self._consumers = []

    async def start(self):
        logging.info('Starting queue monitor')
        loop = self._loop
        self.queue = Queue(maxsize=0)
        logging.info('Loop and queue initialized')

        try:
        
            for _ in range(self.max_concurrent_downloads):
                self._consumers.append(asyncio.create_task(self._monitorQueue(self.queue)))
        except Exception as ex:
            logging.error(ex)
        
        logging.info('Queue monitor events created')

        await asyncio.wait(self._consumers, return_when=asyncio.ALL_COMPLETED)

        logging.info('Queue monitor events stopped')

    def addDownload(self, data : DownloadData):
        if (data.videoId < 0):
            raise Exception('VideoId is less than zero')

        try:
            logging.info(f'Adding {data.videoId}({data.fileName}) to queue')
            self._loop.call_soon_threadsafe(self.queue.put_nowait, data)
            logging.info(f'Added')
        except Exception as ex:
            logging.error(ex)

    async def _monitorQueue(self, queue: Queue):
        while True:
            logging.info('Waiting for element in the queue')
            data = await queue.get()
            try:
                logging.info(f'Retrieved {data.videoId}({data.fileName}) from queue')
                await self.downloader.downloadEpisode(data)
            except Exception as ex:
                raise

            queue.task_done()