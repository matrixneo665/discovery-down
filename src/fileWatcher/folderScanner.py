from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from watchdog.events import FileCreatedEvent
from fileWatcher.discoveryNzbParser import DiscoveryNzbParser

from dataclasses import dataclass
from pathlib import Path

import logging
import os

class FolderScanner:
    def __init__(self, path: str):
        self.path = path
        self.eventHandler = PatternMatchingEventHandler(patterns=["*.nzb"], 
                                            ignore_patterns=[],
                                            ignore_directories=True)

        self.eventHandler.on_created = self.on_created
        self.observer = Observer()
        self.observer.schedule(self.eventHandler, self.path, recursive = True)
        self.fileParser = DiscoveryNzbParser()
        self.onEpisodeDownloadRequested = None

    def start(self):
        self.observer.start()
        #self._initialScan()


    def stop(self):
        self.observer.stop()
        self.observer.join()

    def _initialScan(self):
        search = Path(self.path).glob('**/*.nzb')

        for name in search:
            src_path = os.path.join(self.path, name.name)
            self.eventHandler.dispatch(FileCreatedEvent(src_path = src_path))

    def on_created(self, event):
        logging.info(f'File {event.src_path} was picked up')
        path = event.src_path

        file = os.path.basename(path)

        fileName = os.path.splitext(file)[0]

        parts = Path(path).parts

        type = parts[-2]

        videoId = self.fileParser.retrieveVideoId(path)

        if (self.onEpisodeDownloadRequested):
            self.onEpisodeDownloadRequested(videoId, fileName, type)
        
        os.remove(path)