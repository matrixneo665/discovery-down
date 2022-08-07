import datetime
import os
from aiohttp import ClientSession
from aiohttp import CookieJar

from requests import Session
from requests.adapters import HTTPAdapter

from http.cookiejar import MozillaCookieJar
from requests.packages.urllib3.util.retry import Retry

class AsyncHttp:
    def __init__(self, config):
        cookie = config.cookie

        cj = MozillaCookieJar(cookie)
        cj.load(ignore_discard=True, ignore_expires=True)

        cookies = {}

        for line in cj:
            cookies[line.name] = line.value

        self.cookies = cookies

        self.client = ClientSession(cookies = self.cookies)

    async def getAsync(self, url: str):
        return await self.client.get(url)

    async def getJsonAsync(self, url: str):
        async with self.getAsync(url) as r:
            return await r.json()

    async def getTextAsync(self, url: str):
        async with self.getAsync(url) as r:
            return await r.text()



class Http:
    def __init__(self, config):
        cookie = config.cookie
        if (not os.path.exists(cookie)):
            raise "Error - cookie file does not exist"
            
        self.cookiePath = cookie

        self._cj = MozillaCookieJar(self.cookiePath)
        self._cj.load(ignore_discard=True, ignore_expires=True)

        self.retry = Retry(connect = 3, backoff_factor=0.5)
        self.adapter = HTTPAdapter(max_retries=self.retry)
        s = Session()
        s.mount('http://', self.adapter)
        s.mount('https://', self.adapter)
        s.headers = {
            'x-disco-client': 'TVOS:12.0:dplus_us:16.2.0',
        }
        
        s.cookies = self._cj
        self._session = s

        cookies = {}

        for line in self._cj:
            cookies[line.name] = line.value

        self.cookies = cookies

        self._client = ClientSession(cookies = self.cookies)

    def convertToDate(self, value):
        return datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')

    async def getAsync(self, url: str):
        return await self.client.get(url)

    async def getJsonAsync(self, url: str):
        async with self.getAsync(url) as r:
            return await r.json()

    async def getTextAsync(self, url: str):
        async with self.getAsync(url) as r:
            return await r.text()