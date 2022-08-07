from flask import Flask, url_for, send_file
from flask import Response, request

from typing import Optional

from api.apiDataRetriever import ApiDataRetriever
from mako.template import Template


import pathlib
import asyncio

from orm.common import Base, engine, sessionMaker

from orm.show import Show
from orm.episode import Episode
from orm.season import Season

import urllib.parse

import os
import logging

api = Flask(__name__)


def getDownloadUrl(videoDataId):
    return urllib.parse.urljoin(request.host_url, url_for('retrieveNzb', videoDataId = videoDataId))

def getMpdDownloadUrl(episodeId):
    with api.app_context():
        logging.info(f'Getting MPD url for {episodeId}')
        u = f'http://127.0.0.1:8985/mpd/{episodeId}' #urllib.parse.urljoin('http://127.0.0.1:8985', url_for('getMpd', episodeId = episodeId))
        logging.info(f'URL for {episodeId} is {u}')
        return u

apiDataRetriever = None

addShowToDatabase = None
updateShows = None

forceDownload = None

def setApiDataRetriever(mpdDir: str):
    apiDataRetriever = ApiDataRetriever(sessionMaker, getDownloadUrl, mpdDir)

@api.route('/test/download/<int:videoDataId>', methods=['GET'], strict_slashes=False)
def testDownload(videoDataId: int):
    if (not forceDownload):
        return Response('Force Download is not set', 500)

    forceDownload(videoDataId, f'Testing')


    return Response('Success', 200)

@api.route('/show/update', methods=['GET'], strict_slashes=False)
def updateShowData():
    if (not updateShows):
        return Response('Fail', 500)

    updateShows()
    return Response('Success', 200)

@api.route('/show', methods=["POST"], strict_slashes=False)
def addShow():
    data = request.form
    url = data.get('dUrl') or None
    tvdbId = data.get('tvdbId') or None

    if (not addShowToDatabase):
        return "addShowToDatabase is null"
        
    result = addShowToDatabase (url, tvdbId)

    return result

@api.route('/show', methods=['GET'], strict_slashes=False)
def getAddShowPage():
    postUrl = urllib.parse.urljoin(request.host_url, url_for('addShow'))

    result = apiDataRetriever.retrieveShowData(postUrl)

    return result


@api.route('/api', methods=['GET'], strict_slashes=False)
def search():

    queryData = request.args.to_dict()

    result = apiDataRetriever.retrieveData(queryData)

    r = Response(response=result, status=200, mimetype="application/rss+xml")
    r.headers["Content-Type"] = "text/xml; charset=utf-8"
    return r

@api.route('/mpd/<int:episodeId>', methods=['GET'], strict_slashes = False)
def getMpd(episodeId: int):
    mpd = apiDataRetriever.retrieveMpd(episodeId)
    r = Response(response = mpd, status = 200)

    return r

@api.route('/data/<int:videoDataId>', methods=['GET'], strict_slashes = False)
def retrieveNzb(videoDataId: int):

    nzb = apiDataRetriever.retrieveNzb(videoDataId)

    r = Response(response=nzb, status=200)

    r.headers['Content-Type'] = 'application/x-nzb'
    r.headers['X-DNZB-Name'] = 'test'
    r.headers['X-DNZB-Category'] = 'TV'
    r.headers['Content-Disposition'] = 'attachment; filename="{ep}.nzb"'.format(ep = videoDataId)
    return r

@api.route('/api/show/search/<term>', methods=['GET'], strict_slashes = False)
def showSearch(term):
    return ''


def start(port: Optional[str] = '8985'):
    api.run(host='0.0.0.0', port=port)