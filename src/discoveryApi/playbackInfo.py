class DeviceInfo:
    def __init__(self):
        self.adBlocker = False
        self.drmSupported = True
        self.hdrCapabilities = ["SDR","HDR10","DOLBY_VISION"]
        self.hwDecodingCapabilities = ["H264","H265"]
        self.player = {"width": 3840, "height": 2160}
        self.screen = {"width": 3840, "height": 2160}
        self.soundCapabilities = ["STEREO","DOLBY_DIGITAL","DOLBY_DIGITAL_PLUS"]

class StreamProvider:
    def __init__(self):
        self.version = "1.0.0"
        self.hlsVersion = 7
        self.suspendBeaconing = 1
        self.pingConfig = 1

class WisteriaDeviceInfo:
    def __init__(self):
        self.player = PlayerInfo()
        self.make = "AppleTV"
        self.model = "AppleTV"
        self.os = "tvOS"
        self.osVersion = "12.0"
        self.type = "appleTV"
        self.language = "en"

class PlayerInfo:
    def __init__(self):
        self.name = "Discovery Player tvOS native"
        self.version = "16.2.0"

class WisteriaInfo:
    def __init__(self):
        self.adDebug = ""
        self.siteId = "dplus_us"
        self.product = "dplus_us"
        self.platform = "tvos"
        self.appBundle = "com.discovery.mobile.discoveryplus"
        self.gdpr = 0
        self.streamProvider = StreamProvider()
        self.device = WisteriaDeviceInfo()
        self.playbackId = "562C00EB-E816-4DA5-A2AF-A6D6D88C87F6"
        self.config = {}
        self.sessionId = "B0C26417-49D1-4713-9680-992A070F076C"


class PlaybackInfo:
    def __init__(self, videoId):
        self.deviceInfo = DeviceInfo()
        self.videoId: str = videoId
        self.wisteriaProperties = WisteriaInfo()