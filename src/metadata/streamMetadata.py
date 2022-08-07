from typing import Optional

class StreamInfo:
    def __init__(self, type: str, pssh: str, key: str, id: str, bandwidth: Optional[str] = '', url: Optional[str] = '', numPeriods: Optional[int] = 1):
        self.type = type
        self.pssh = pssh
        self.key = key
        self.id = id
        self.bandwidth = bandwidth or None
        self.url = url or ''
        self.numPeriods = numPeriods

class VideoStreamInfo(StreamInfo):
    def __init__(self, id: str, 
        height: int, 
        width: int, 
        pssh: Optional[str] = '', 
        key: Optional[str] = '', 
        bandwidth: Optional[str] = '', 
        url: Optional[str] = '', 
        numPeriods: Optional[int] = 1,
        fileSizeBytes: Optional[int] = 0
    ):
        super().__init__(type = 'video', pssh=pssh, id = id, key = key, bandwidth = bandwidth, url = url, numPeriods = numPeriods)
        self.height = height
        self.width = width
        self.fileSizeBytes = fileSizeBytes or 0

class AudioStreamInfo(StreamInfo):
    def __init__(self, id: str, key: Optional[str] = '', pssh: Optional[str] = '', bandwidth: Optional[str] = '', url: Optional[str] = '', numPeriods: Optional[int] = 1):
        super().__init__(type = 'audio', key = key, pssh=pssh, id = id, bandwidth=bandwidth, url = url, numPeriods = numPeriods)

class StreamMetadata:
    def __init__(self):
        self.videoSets: list = []
        self.audioSets: list = []

class CaptionMetadata:
    def __init__(self, id: str, numPeriods: Optional[str] = 1):
        self.id = id
        self.numPeriods = numPeriods