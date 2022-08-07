import requests
import xml.etree.ElementTree as ET

from lxml import etree

from time import sleep
from metadata.streamMetadata import VideoStreamInfo, AudioStreamInfo, StreamMetadata

from widevine.getwvkeys import GetwvCloneApi
from widevine.widevineArgs import WidevineArgs

from pathlib import Path

class MpdParser:
    contentProtectionNs: str = '{urn:mpeg:dash:schema:mpd:2011}'
    cencNs: str = "{urn:mpeg:cenc:2013}"
    def __init__(self, licenseUrl, drmToken, auth):
        self.licenseUrl = licenseUrl
        self.drmToken = drmToken or ''
        self.auth = auth
        self.retrievedKeys = {}

    def _retrieveWvKey(self, pssh: str):
        if (not pssh or pssh == ''):
            return ''

        sleep(1)
        cachedKey = self.retrievedKeys.get(pssh)

        if (cachedKey):
            return cachedKey

        args = WidevineArgs(
                    pssh = pssh, 
                    url = self.licenseUrl, 
                    preAuthToken = self.drmToken, 
                    verbose = False, 
                    headers = {"accept": "*/*"}, 
                    cache = False, 
                    auth = self.auth
                )

        retriever = GetwvCloneApi(args)

        results = retriever.main()

        if (results and len(results) > 0):
            self.retrievedKeys[pssh] = results[0]
        else:
            self.retrievedKeys[pssh] = ''

        return self.retrievedKeys[pssh] or ''

    def parseMpd(self, mpd_string: str):
        root = ET.XML(mpd_string)

        data = StreamMetadata()

        data.videoSets.extend( self._getVideoAdaptationSets(root))
        data.audioSets.extend(self._getAudioAdaptationSets(root))
        
        return data

    def _getAudioAdaptationSets(self, root):
        adaptationSets = root.findall(f".//{self.contentProtectionNs}AdaptationSet[@contentType='audio']")

        if (len(adaptationSets) < 1):
            return None

        bestAudioSet = adaptationSets[0]
        setPssh = self._getPsshFromAdaptationSet(bestAudioSet)

        representations = bestAudioSet.findall(f"./{self.contentProtectionNs}Representation")

        for representation in representations:

            audioRepresentations = self._getRepresentations(representation, setPssh, self._createAudioAdaptationSet)

        return [audioRepresentations]

    def _getVideoAdaptationSets(self, root):
        adaptationSets = root.findall(f".//{self.contentProtectionNs}AdaptationSet[@contentType='video']")

        sets = {}

        for adaptationSet in adaptationSets:
            setPssh = self._getPsshFromAdaptationSet(adaptationSet)

            representations = adaptationSet.findall(f"./{self.contentProtectionNs}Representation")

            for representation in representations:
                height = representation.attrib.get('height')
                width = representation.attrib.get('width')
                bandwidthBitsps = float(respresentation.attrib.get('bandwidth'))

                segmentTemplate = representation.findall(f"./{self.contentProtectionNs}SegmentTemplate")

                fileSizeBytes = 0

                if (len(segmentTemplate) > 0):
                    template = segmentTemplate[0]

                    durationMs = float(template.attrib.get('duration'))
                    durationS = durationMs / 1000.0

                    fileSizeBits = bandwidthBitsps * durationS
                    fileSizeBytes = fileSizeBits / 8

                set = sets.get(width)

                if (set):
                    set.fileSize = set.fileSize + fileSizeBytes
                    set.numPeriods = set.numPeriods + 1
                    continue

                videoRepresentation = self._getRepresentations(representation, setPssh, self._createVideoAdaptationSet)
                videoRepresentation.fileSizeBytes = fileSizeBytes

                sets[width] = videoRepresentation

        return sets.values()
    
    def _getRepresentations(self, representation, pssh, createAdaptationSet):
        node = representation

        key = self._retrieveWvKey(pssh)

        attrib = node.attrib

        bandwidth = attrib.get('bandwidth')
        id = attrib.get('id')

        return createAdaptationSet(attrib, bandwidth, id, pssh, key)

    def _createVideoAdaptationSet(self, attributes, bandwidth, id, pssh, key):
        height = attributes.get('height')
        width = attributes.get('width')

        return VideoStreamInfo(id = id, pssh = pssh, height = int(height), width = int(width), bandwidth = bandwidth, key = key)

    def _createAudioAdaptationSet(self, attributes, bandwidth, id, pssh, key):
        return AudioStreamInfo(id = id, pssh = pssh, bandwidth = bandwidth, key = key)

    def _getPsshFromAdaptationSet(self, adaptationSet):
        schemeIdUri = 'urn:uuid:EDEF8BA9-79D6-4ACE-A3C8-27DCD51D21ED'
    
        protections = adaptationSet.findall(f".//{self.contentProtectionNs}ContentProtection[@schemeIdUri='{schemeIdUri}']")
        if (len(protections) < 1):
            protections = adaptationSet.findall(f".//{self.contentProtectionNs}ContentProtection[@schemeIdUri='{schemeIdUri.lower()}']")
            if (len(protections) < 1):
                return None
        
        protection = protections[0]
        cecs = protection.findall(f".//{self.cencNs}pssh")

        if (len(cecs) < 1):
            return None

        return cecs[0].text
