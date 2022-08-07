import asyncio
import aiohttp
import subprocess
import shutil

from typing import Optional

from widevine.getwvkeys import GetwvCloneApi
from widevine.widevineArgs import WidevineArgs

from asyncio import Queue, create_task

from orm.episode import VideoData, Episode, AudioData
from sqlalchemy import select
from downloadData import DownloadData

import os
from pathlib import Path

import logging

class DiscoveryDownloader:
    def __init__(self, config, sessionMaker, getDownloadUrl: callable, getShowMpd: bool = True):
        self.max_concurrent_downloads = 4
        self.cookiePath = config.cookie
        self.tempPath = config.temp
        self.downloadPath = config.download
        self.getShowMpd = getShowMpd
        self._getDownloadUrl = getDownloadUrl
        self.api = config.api
        self._sessionMaker = sessionMaker

    async def downloadEpisode(self, data: DownloadData):
        logging.info(f'Starting to download episode')
        fileName = data.fileName
        videoId = data.videoId
        type = data.type

        videoData = None
        episode = None
        audioData = None
        numPeriods = 1
        
        with self._sessionMaker() as database:
            logging.info('Selecting video data')
            videoData = database.scalars(select(VideoData).where(VideoData.id == videoId)).first()
            logging.info('Found video data')

            episode = videoData.episode

            numPeriods = videoData.numPeriods

            if (len(episode.audioData) > 0):
                audioData = episode.audioData[0]

        tempDir = os.path.join(self.tempPath, fileName)

        if (not episode.drmEnabled):
            logging.info(f'Downloading unprotected video into {tempDir}')
            await self._downloadUnProtected(videoData.streamUrl, audioData.streamUrl, fileName, tempDir, type)
        else:
            await self._downloadEncrypted(episode, videoData, audioData, fileName, tempDir, type)

        logging.info(f'Cleaning artifact directory {tempDir}')
        shutil.rmtree(tempDir)
        logging.info(f'Finished downloading {fileName} ({videoId})')

    async def _downloadEncrypted(self, episode: Episode, videoData: VideoData, audioData: AudioData, fileName: str, tempDir: str, type: str):
        numPeriods = videoData.numPeriods
        logging.info('Getting url')
        url = self._getDownloadUrl(episode.id)
        logging.info('Found url')

        videoEncPath = os.path.join(tempDir, "enc", "video")
        audioEncPath = os.path.join(tempDir, "enc", "audio")

        #subtitleDir = os.path.join(tempDir, "dec", "subtitle")

        videoDownload = self._downloadEncryptedStream(videoEncPath, url, videoData.streamId, numPeriods)
        audioDownload = self._downloadEncryptedStream(audioEncPath, url, audioData.streamId, numPeriods)

        #subtitleDownload = self._downloadSubtitles(subtitleDir, url)

        await asyncio.gather(*[videoDownload, audioDownload])

        subtitlePath = None

        #subtitlePath = await subtitleDownload

        videoDecPath = os.path.join(tempDir, "dec", "video")
        audioDecPath = os.path.join(tempDir, "dec", "audio")

        videoDec = self._decryptData(videoEncPath, videoDecPath, videoData.key)
        audioDec = self._decryptData(audioEncPath, audioDecPath, audioData.key)

        await asyncio.gather(*[videoDec, audioDec])            

        videoFile, suffix = await self._mergePath(videoDecPath, tempDir, fileName)
        audioFile, _ = await self._mergePath(audioDecPath, tempDir, fileName)

        finalOutput = os.path.join(self.downloadPath, type, f"{fileName}{suffix}")

        await self._mergeVideoAudio(
            videoPath = videoFile, 
            audioPath = audioFile, 
            subtitlePath = subtitlePath,
            finalPath = finalOutput
        )

    async def _downloadSubtitles(self, outputPath: str, url: str):
        path = Path(outputPath)
        path.mkdir(parents=True, exist_ok=True)

        logging.info(f'Downloading subtitles {url} to {outputPath}')

        args = ["--external-downloader", "aria2c", 
                    "--no-warnings", 
                    "--allow-unplayable-formats", 
                    "--no-check-certificate", 
                    #"--list-subs",
                    #"--simulate",
                    "-o",
                    os.path.join(outputPath, "%(title)s.%(ext)s"),
                    url
                ]
        
        downloadProc = await asyncio.create_subprocess_exec("yt-dlp", *args)
        await downloadProc.communicate()

        files = path.glob("*")

        for file in files:
            os.rename(file, f"{file}.vtt")
            return f"{file}.vtt"

        return None

    async def _downloadEncryptedStream(self, outputPath: str, url: str, streamId: str, numPeriods: int):
        Path(outputPath).mkdir(parents=True, exist_ok=True)

        logging.info(f'Downloading encrypted data from {url} to {outputPath}')

        args = ["--external-downloader", "aria2c", 
                    "--no-warnings", 
                    "--allow-unplayable-formats", 
                    "--no-check-certificate", 
                    #"--write-sub",
                    "-v",
                ]

        formats = []

        if (numPeriods == 1):
            formats.append(streamId)
        else:
            for x in range(numPeriods):
                formats.append(f"{streamId}-{x}")

        videoArgs = ["-f", ",".join(formats), "-P", outputPath, "-o", f"%(format_id)s.%(ext)s"]

        videoArgs.extend(args)

        videoArgs.append(url)
        
        videoProc = await asyncio.create_subprocess_exec("yt-dlp", *videoArgs)
        await videoProc.communicate()
        
    async def _decryptData(self, path: str, destPath: str, key: str):
        Path(destPath).mkdir(parents=True, exist_ok=True)

        logging.info(f'Decrypting data from {path} to {destPath}')

        files = Path(path).glob("*")

        decryptProcs = []

        for file in files:
            encFile = os.path.join(path, file.name)
            destFile = os.path.join(destPath, file.name)

            args = [encFile, destFile, "--key", key, "--show-progress"]

            decryptProcs.append((await asyncio.create_subprocess_exec("mp4decrypt", *args)).communicate())

        await asyncio.gather(*decryptProcs)

        logging.info(f'Finished decrypting from {path}')

    async def _mergePath(self, pathToMerge: str, outputPath: str, fileName: str):
            logging.info(f'Merging files in {pathToMerge}')

            files = Path(pathToMerge).glob("*")
            allFiles = os.path.join(pathToMerge, 'all.txt')
            fileList = []
            for file in filter(lambda x: x.suffix != '.txt', files):
                fileList.append(f"file '{str(file)}'")

            with open(allFiles, 'w') as f:
                    f.write("\n".join(fileList))

            mergedFile = os.path.join(outputPath, f"{fileName}{file.suffix}")

            args = ["-f", "concat", "-safe", "0", "-i", allFiles, "-c", "copy", mergedFile]

            proc = await asyncio.create_subprocess_exec("ffmpeg", *args)

            await proc.communicate()
            
            logging.info(f'Merged files in {pathToMerge}')

            return (mergedFile, file.suffix)

    async def _downloadUnproctectedStream(self, url: str, outputFile: str):
        args = ["--hls-prefer-ffmpeg",
                "--extractor-retries", 
                "10", 
                "--ignore-config", 
                "-N50", 
                "-o",
                outputFile,
                url
            ]

        return await asyncio.create_subprocess_exec("yt-dlp", *args)

    async def _downloadUnProtected(self, videoUrl: str, audioUrl: str, fileName: str, tempDir: str, type: str):

        videoOutputFile = os.path.join(tempDir, f"video-{fileName}.mp4")
        audioOutputFile = os.path.join(tempDir, f"audio-{fileName}.m4a")
        finalOutput = os.path.join(self.downloadPath, type, f"{fileName}.mp4")

        logging.info('Downloading video and audio streams')
        videoProc = await self._downloadUnproctectedStream(videoUrl, videoOutputFile)
        audioProc = await self._downloadUnproctectedStream(audioUrl, audioOutputFile)

        await asyncio.gather(*[videoProc.communicate(), audioProc.communicate()])

        logging.info('merging video and audio streams')
        await self._mergeVideoAudio(videoOutputFile, audioOutputFile, finalOutput)

    async def _mergeVideoAudio(self, videoPath: str, audioPath: str, finalPath: str, subtitlePath: Optional[str] = None):
        logging.info(f'Merging video and audio ({videoPath}, {audioPath}) to {finalPath}')

        paths = ["-i", videoPath, "-i", audioPath]
        copies = ["-c:v", "copy", "-c:a", "copy"]

        #if (subtitlePath):
        #    paths.extend(["-i", subtitlePath])
        #    copies.extend(["-c:s", "copy"])

        mergeArgs = []
        mergeArgs.extend(paths)
        mergeArgs.extend(copies)

        mergeArgs.append(finalPath)
        mergeProc = await asyncio.create_subprocess_exec("ffmpeg", *mergeArgs)

        await mergeProc.communicate()