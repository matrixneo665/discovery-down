from dataclasses import dataclass

@dataclass
class DownloadData:
    fileName: str = ''
    videoId: int = -1
    type: str = ''