import xml.etree.ElementTree as ET


class DiscoveryNzbParser:
    def retrieveVideoId(self, filePath: str):
        elementTree = ET.parse(filePath)
        root = elementTree.getroot()
        metaVideoIds = root.findall(".//{0}meta[@type='videoDataId']".format("{http://www.newzbin.com/DTD/2003/nzb}"))

        if (len(metaVideoIds) == 1):
            return metaVideoIds[0].text

        return None
