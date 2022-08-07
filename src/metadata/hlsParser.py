import m3u8

from metadata.streamMetadata import StreamMetadata, VideoStreamInfo, AudioStreamInfo

class HlsParser:
    def __init__(self):
        pass

    def parseHlsData(self, url: str, episodeId: str):
        manifest = m3u8.load(url)

        data = StreamMetadata()

        videos = self._getVideoStreamInfo(manifest)
        audios = self._getAudioStreamInfo(manifest)

        data.videoSets.extend(videos)
        data.audioSets.extend(audios)

        return data

    def _getAudioStreamInfo(self, manifest):
        data = []

        for media in filter(lambda m: m.type == 'AUDIO' ,manifest.media):
            data.append(
                AudioStreamInfo(f'{media.language}-{media.channels}', url = media.absolute_uri)
            )

        return data

    def _getVideoStreamInfo(self, manifest):
        retrievedHeights = {}

        for playlist in manifest.playlists:
            streamInfo = playlist.stream_info

            resolution = streamInfo.resolution
            bandwidth = streamInfo.bandwidth
            avgBandwidth = streamInfo.average_bandwidth

            stableId = streamInfo.stable_variant_id
            programId = streamInfo.program_id
            pathwayId = streamInfo.pathway_id
            url = playlist.absolute_uri

            width = resolution[0]
            height = resolution[1]

            #make the ID = height since the m3u8 is unique per resolution
            id = str(height)

            matchHeight = retrievedHeights.get(height)

            if (matchHeight and matchHeight.bandwidth > avgBandwidth):
                continue

            info = VideoStreamInfo(id = id, height = int(height), width = int(width), bandwidth = avgBandwidth, url = url)

            retrievedHeights[height] = info

        return retrievedHeights.values()