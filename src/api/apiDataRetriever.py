from typing import List

from api.result import ResultSet, Result, Category

from mako.template import Template
from mako import exceptions

from orm.show import Show
from orm.episode import Episode, VideoData
from orm.season import Season

from sqlalchemy import func, desc, select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import contains_eager

import pathlib
import os

absPath = str(pathlib.Path(__file__).parent.absolute())

parentPath = str(absPath)
templatePath = os.path.join(parentPath, "templates")

RESULT_TEMPLATE = Template(filename = os.path.join(templatePath, 'searchresult.template.mako'))
CAPS_TEMPLATE = Template(filename = os.path.join(templatePath, 'caps.template.mako'))
NZB_TEMPLATE = Template(filename = os.path.join(templatePath, 'nzb.template.mako'))
ADD_SHOW_TEMPLATE = Template(filename = os.path.join(templatePath, 'addShow.template.mako'))

class ShowResult:
    def __init__(self, title: str, seasonCount: int, episodeCount: int):
        self.title = title
        self.seasonCount = seasonCount
        self.episodeCount = episodeCount

class ApiDataRetriever:
    def __init__(self, dbSessionMaker, urlRetriever, mpdDir):
        self.dbSessionMaker = dbSessionMaker
        self.urlRetriever = urlRetriever
        self.mpdDir = mpdDir

    def retrieveShowData(self, postUrl: str):
        shows = []
        with self.dbSessionMaker() as session:
            data = list(session.query(Show))

            for show in data:
                title = show.title
                seasonCount = 0
                episodeCount = 0

                for season in show.seasons:
                    seasonCount = seasonCount + 1

                    for episode in season.episodes:
                        episodeCount = episodeCount + 1
                
                shows.append(ShowResult(title, seasonCount, episodeCount))

        result = ADD_SHOW_TEMPLATE.render(**{'postUrl': postUrl, 'showData': shows})
        return result

    def retrieveMpd(self, episodeId: int):
        if (episodeId < 1):
            return ''
            
        fileName = os.path.join(self.mpdDir, f'{episodeId}.mpd')

        with open(fileName, 'r') as f:
            return f.read()

        return ''

    def retrieveData(self, queryData):
        type = queryData.get('t')

        if (type == "caps"):
            return self.retrieveCaps()

        if (type == "tvsearch"):
            return self.retrieveQuery(queryData)

        return ''
    
    def retrieveNzb(self, videoDataId: int):
        data = {'videoDataId': videoDataId}

        return NZB_TEMPLATE.render(**data)

    def retrieveCaps(self):
        data = {"app_version": "1", "api_version": "1", "email": "test@test.com"}

        category = Category(id = 5000, name = "TV")
        category.children.append(Category(id = 5010, name = "TV/WEB-DL"))
        category.children.append(Category(id = 5020, name = "TV/Foreign"))
        category.children.append(Category(id = 5030, name = "TV/SD"))
        category.children.append(Category(id = 5040, name = "TV/HD"))
        category.children.append(Category(id = 5045, name = "TV/UHD"))
        category.children.append(Category(id = 5050, name = "TV/Other"))
        category.children.append(Category(id = 5060, name = "TV/Sport"))
        category.children.append(Category(id = 5080, name = "TV/Documentary"))

        data["categories"] = [category]

        result = CAPS_TEMPLATE.render(**data)

        return result

    def retrieveQuery(self, queryData):

        with self.dbSessionMaker() as db:
            query = db.query(Episode).join(Season, Season.id == Episode.seasonId).join(Show, Show.id == Season.showId)

            season = queryData.get('season')
            episode = queryData.get('ep')
            q = queryData.get('q')
            tvdbId = queryData.get('tvdbid')

            if (episode):
                query = query.filter(Episode.num == int(episode))

            if (season):
                query = query.filter(Season.num == int(season))

            if (tvdbId):
                query = query.filter(Show.tvdbId == tvdbId)

            query = query.order_by(Episode.publishDate.desc())

            total = query.count()

            data = list(query)

            result = self._convertToResults(data, total)

            return result

    def _convertToResults(self, data: List[Show], total: int):
        
        dataset = ResultSet(total = total)

        episodes = data
        for episode in episodes:
            title = "{show} S{season:0>2d}E{episode:0>2d} {title}".format(show = episode.season.show.title, season = episode.season.num, episode = episode.num, title = episode.title)

            for videoData in filter(lambda v: v.height >= 420, episode.videoData):

                result = Result(id = videoData.id, 
                            episode = episode.num, 
                            added = episode.airDate, 
                            posted = episode.publishDate, 
                            season = episode.season.num, 
                            title = title, 
                            resolution = videoData.width or 0,
                            tvdbid = episode.season.show.tvdbId or '')
                dataset.releases.append(result)

        try:
            d = vars(dataset)

            d['get_url'] = self.urlRetriever

            return RESULT_TEMPLATE.render(**d)
        except Exception as ex:
            return None