from dataclasses import dataclass

from discoveryHttp.http import Http
from orm.show import Show
from orm.season import Season
from orm.episode import Episode, VideoData, AudioData

from sqlalchemy import select
from typing import Optional
from urllib.parse import urljoin

import datetime
import json
import jsonpickle
import os
import pathlib
import re
import requests

from discoveryApi.playbackInfoRetriever import PlaybackInfoRetriever

class DiscoveryShowRetriever(Http):
    def __init__(self, config, dbSessionMaker):
        super().__init__(config)
        self._dbSessionMaker = dbSessionMaker
        self.mpdDir = config.mpdDir
        self.infoRetriever = PlaybackInfoRetriever(config)

    def updateShowData(self, showId = None, episodeId = None):
        shows = []

        with self._dbSessionMaker() as database:
            res = list(database.query(Show))

            for result in res:
                if (showId):
                    if (not result.id == showId):
                        continue
                shows.append({'slug': result.slug, 'tvdbId': result.tvdbId})

        for show in shows:
            self._getShowMetadata(show.get('slug'), show.get('tvdbId'), episodeId)
    
    def retrieveShowData(self, url: str, tvdbId: Optional[str] = None):
        url_slug_regex = '^.*\/show\/(.*)$'

        result = re.match(url_slug_regex, url)

        if (not result):
            return None

        url_slug = result.group(1)

        return self._getShowMetadata(url_slug, tvdbId)

    def _getShowMetadata(self, url_slug, tvdbId, episodeId = None):

        with self._dbSessionMaker() as database:
            show_data = self._retrieveShowMetadata(url_slug, tvdbId, database, episodeId)

            database.commit()
            database.flush()

            return show_data


    def _retrieveShowMetadata(self, url_slug, tvdbId, database, episodeId = None):
        result = self._session.get(f"https://us1-prod-direct.discoveryplus.com/cms/routes/show/{url_slug}?include=default")

        result_data = result.json()
        
        return self._parseShowMetadata(result_data, url_slug, tvdbId, database, episodeId)

    def _parseShowMetadata(self, result_data, url_slug, tvdbId, database, episodeId = None):

        show = database.scalars(select(Show).where(Show.slug == url_slug)).first()

        if (not show):
            show = Show(slug = url_slug)
            database.add(show)

        if (show.tvdbId != tvdbId and tvdbId != None):
            show.tvdbId = tvdbId

        included = result_data['included']

        show_id = None

        season_count = 0

        filtered = []

        def valid(i):
            
            attr = i.get('attributes')
            if (not attr):
                return False

            currentType = attr.get('type')

            if (not currentType):
                return True

            return currentType != 'image'
        
        filtered.extend(filter(valid, included))


        #videoType == 'STANDALONE'

        for include in filtered:
            attributes = include.get('attributes') or None

            if (not attributes):
                continue

            includedType = include.get('type') or None

            if (includedType == "page"):
                show.title = attributes.get('title')

            if (not 'component' in attributes):
                continue

            component = attributes['component']

            if (not show_id):
                show_id = self._getShowId(component)

            season_result = self._getSeasonResult(component)

            if (season_result):
                season_count = max(season_count, season_result)
           
        show.id = show_id

        self._retrieveAllSeasonData(show, season_count, database, episodeId)

        return show

    def _getShowId(self, component):
        show_id_regex = '.*pf\[show\.id\]=(\d+).*'
        show_entry_regex = ".*pf\[show\.id\].*"

        if (not 'mandatoryParams' in component):
            return None

        mandatoryParams = component['mandatoryParams']

        result = re.match(show_entry_regex, mandatoryParams)

        if (not result):
            return None

        show_id_match = re.match(show_id_regex, mandatoryParams)

        if (not show_id_match):
            return None

        return show_id_match.group(1)

    def _getSeasonResult(self, component):
        max_season = 0
        season_num_regex = '.*pf\[seasonNumber\]=\d+.*'

        if (not 'filters' in component):
            return 0

        filters = component['filters']

        if (len(filters) == 0):
            return 0

        first_filter = filters[0]

        if (not 'options' in first_filter):
            return 0

        options = first_filter['options']

        for option in options:
            if (re.match(season_num_regex, option['parameter'])):
                max_season = max(int(option['value']), max_season)

        return max_season

    def _retrieveAllSeasonData(self, show, season_count, database, episodeId = None):
        show_id = show.id

        allSeasons = show.seasons

        numSeasons = len(allSeasons)

        start = 0

        if (numSeasons > 0):
            if (numSeasons < season_count):
                start = season_count
            else:
                start = numSeasons

        for season in range(start, season_count + 1):

            discSeason = next(filter(lambda s: s.num == season, show.seasons), None)

            if (not discSeason):
                discSeason = Season(num = season)
                show.seasons.append(discSeason)

            season_url = f"https://us1-prod-direct.discoveryplus.com/cms/collections/89438300356657080631189351362572714453?include=default&decorators=&pf[seasonNumber]={season}&pf[show.id]={show_id}"

            response = self._session.get(season_url)

            data = response.json()

            self._parseEpisodeData(data, discSeason, database, episodeId)        

    def _parseEpisodeData(self, data, season, database, episodeId = None):
        included = data.get('included')

        if (not included):
            return

        for include in included:
            attributes = include.get('attributes')

            if (not attributes):
                continue
                            
            url_slug = attributes.get('path')

            if (not url_slug):
                continue

            id = include.get('id')

            if (episodeId and str(episodeId) != id):
                continue

            airDate = attributes.get('airDate')

            publishDate = attributes.get('publishStart')

            episodeNum = attributes.get('episodeNumber')

            ad = self.convertToDate(airDate)
            pd = self.convertToDate(publishDate)

            episode = database.scalars(select(Episode).where(Episode.id == id).where(Episode.seasonId == season.id)).first()

            if (not episode):
                episode = Episode(id = id, num = episodeNum, title = attributes.get('name'), airDate = ad, publishDate = pd)
                season.episodes.append(episode)
            
            self._setEpisodeStreamData(episode)

            database.commit()
            database.flush()
    
    def _setEpisodeStreamData(self, episode: Episode):
        info = self.infoRetriever.retrieveEpisodePlaybackInfo(episode.id)

        if (episode.drmToken != info.drmToken):
            episode.drmToken = info.drmToken
        
        if (episode.licenseUrl != info.licenseUrl):
            episode.licenseUrl = info.licenseUrl

        if (episode.drmEnabled != info.drmEnabled):
            episode.drmEnabled = info.drmEnabled

        if (not info.streamMetadata):
            return
        
        self._setEpisodeVideoData(episode, info.streamMetadata.videoSets)
        self._setEpisodeAudioData(episode, info.streamMetadata.audioSets)

    def _setEpisodeVideoData(self, episode: Episode, videoData: list):
        if (not videoData):
            return

        for video in videoData:
            matching = next(filter(lambda v: v.streamId == video.id, episode.videoData), None)

            if (matching):
                matching.pssh = video.pssh
                matching.key = video.key
                matching.streamUrl = video.url
                continue

            episode.videoData.append(
                VideoData(
                    streamId = video.id, 
                    bandwidth = video.bandwidth, 
                    pssh = video.pssh,
                    key = video.key,
                    width = video.width,
                    height = video.height,
                    streamUrl = video.url,
                    numPeriods = video.numPeriods
                )
            )

    def _setEpisodeAudioData(self, episode: Episode, audioData: list):
        if (not audioData):
            return

        for audio in audioData:
            matching = next(filter(lambda a: a.streamId == audio.id, episode.audioData), None)

            if (matching):
                matching.pssh = audio.pssh
                matching.key = audio.key
                matching.streamUrl = audio.url
                continue

            episode.audioData.append(
                AudioData(
                    streamId = audio.id,
                    streamUrl = audio.url,
                    bandwidth = audio.bandwidth, 
                    pssh = audio.pssh,
                    key = audio.key
                )
            )
    
    

    