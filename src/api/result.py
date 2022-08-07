from typing import Optional, List
from datetime import datetime

class ResultSet:
    def __init__(self, offset: int = 0, total:int = 0):
        self.releases: List[Result] = []
        self.offset: int = offset
        self.total: int = total

class Result:
    def __init__(self, 
                added: Optional[datetime] = None, 
                posted: Optional[datetime] = None, 
                id: Optional[int] = 0, 
                grabs:Optional[int] = 0, 
                size:Optional[int] = 0, 
                season:Optional[int] = 0, 
                episode: Optional[int] = 0, 
                title: Optional[str] = "", 
                tvdbid: Optional[str] = "", 
                resolution: Optional[int] = 0):

        self.added: datetime = added
        self.posted: datetime = posted
        self.id: int = id
        self.group: ReleaseGroup = ReleaseGroup()
        self.category: Category = Category()
        self.tvshow: TvShow = TvShow()
        self.movie = None
        self.grabs: int = grabs
        self.size: int = size
        self.search_name: str = ""
        self.posted_by: str = "MatrixNeo665"
        self.season: int = season
        self.episode: int = episode
        self.title: str = title
        self.tvdbid: str = tvdbid
        self.resolution: int = resolution

class ReleaseGroup:
    def __init__(self):
        self.name:str = "MatrixNeo665"

class TvShow:
    def __init__(self):
        self.ids = []

class Category:
    def __init__(self, id: Optional[int] = 0, name: Optional[str] = ''):
        self.children: List[Category] = []
        self.id: int = id
        self.name: str = name
        self.parent_id = None