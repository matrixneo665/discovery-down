from dataclasses import dataclass
from typing import List

@dataclass
class DiscoveryShow:
    id: int
    slug: str
    title: str
    tvdbid: str = None

class DiscoveryShowParser:
    def parseToDiscoveryShow(self, jsonResult: dict) -> List[DiscoveryShow]:
        results: List[DiscoveryShow] = []

        included = jsonResult.get('included') or None

        if (not included):
            return results

        includedShows = filter(lambda x: x.get('type') == 'show', included)

        results.extend(map(self._createShow, includedShows))

        return results
    
    def _createShow(self, jsonShow: dict) -> DiscoveryShow:
        attr = jsonShow.get('attributes')

        title = attr.get('name')
        slug = attr.get('alternateId')
        id = jsonShow.get('id')

        return DiscoveryShow(id = id, slug = slug, title = title)