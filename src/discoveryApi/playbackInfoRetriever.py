import jsonpickle
import os

from discoveryApi.playbackInfo import PlaybackInfo
from metadata.mpdParser import MpdParser
from metadata.hlsParser import HlsParser
from metadata.streamMetadata import StreamMetadata
from discoveryHttp.http import Http
from time import sleep
from typing import Optional
from widevine.getwvkeys import GetwvCloneApi
from widevine.widevineArgs import WidevineArgs
from pathlib import Path

class EpisodeInfo:
    def __init__(self, 
        licenseUrl: str, 
        drmToken: str, 
        streamMetadata: StreamMetadata, 
        drmEnabled: bool
    ):
        self.licenseUrl = licenseUrl
        self.drmToken = drmToken
        self.streamMetadata = streamMetadata
        self.drmEnabled = drmEnabled

class PlaybackInfoRetriever(Http):
    def __init__(self, config):
        super().__init__(config)
        self.mpdDir = config.mpdDir
        self.auth = config.api


    def retrieveEpisodePlaybackInfo(self, episodeId, getManifestData: Optional[bool] = True) -> EpisodeInfo:
        info = PlaybackInfo(str(episodeId))

        jsonInfo = jsonpickle.encode(info, unpicklable=False)

        sleep(3)

        playbackInfoRes = self._session.post('https://us1-prod-direct.discoveryplus.com/playback/v3/videoPlaybackInfo', data = jsonInfo)

        playbackInfo = playbackInfoRes.json()

        return self._parseEpisodeInfo(playbackInfo, episodeId, getManifestData)

    def _parseEpisodeInfo(self, playbackInfo, episodeId, getManifestData: bool):
        data = playbackInfo.get('data')
        if (not data):
            return None

        attr = data.get('attributes')
        if (not attr):
            return None
        
        streaming = attr.get('streaming')

        if (not streaming):
            return None

        for stream in streaming:
            url = stream.get('url')

            protection = stream.get('protection')
            if (protection):
                drmToken = protection.get('drmToken') or ''
                drmEnabled = protection.get('drmEnabled') or False
                licenseUrl = self._getLicenseUrl(protection) or ''

        if (url and getManifestData):
            if (url.__contains__('.mpd')):
                streamMetadata = self._getShowMpdData(url, episodeId, drmToken, licenseUrl)
            elif (url.__contains__('.m3u8')):
                streamMetadata = self._parseHlsManifest(url, episodeId)
            else:
                raise Exception(f"Could not determine manifest type from {url}")
        else:
            streamMetadata = None


        return EpisodeInfo(drmToken = drmToken, licenseUrl = licenseUrl, streamMetadata = streamMetadata, drmEnabled = drmEnabled)

    def _parseHlsManifest(self, url: str, episodeId: str):
        return HlsParser().parseHlsData(url, episodeId)

    def _getLicenseUrl(self, protection):
        schemes = protection.get('schemes')
        if (not schemes):
            return None

        widevine = schemes.get('widevine')
        if (not widevine):
            return None

        return widevine.get('licenseUrl')

    def _getShowMpdData(self, url: str, episodeId, drmToken, licenseUrl):
        data = self._downloadData(url, episodeId, 'mpd')

        return MpdParser(licenseUrl = licenseUrl, drmToken = drmToken, auth = self.auth).parseMpd(data)
    
    def _downloadData(self, url: str, episodeId: int, extension: str): 
        data = self._session.get(url).text

        Path(self.mpdDir).mkdir(parents=True, exist_ok=True)

        fileName = os.path.join(self.mpdDir, f"{episodeId}.{extension}")

        with open(fileName, 'w') as f:
            f.write(data)

        return data