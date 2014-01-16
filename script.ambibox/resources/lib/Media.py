from MediaInfoDLL import MediaInfo, Stream

import xbmc
import xbmcaddon

import unicodedata

__addon__ = xbmcaddon.Addon()
__cwd__ = __addon__.getAddonInfo('path')
__scriptname__ = __addon__.getAddonInfo('name')


def info(msg):
    xbmc.log("### [%s] - %s" % (__scriptname__, msg,), level=xbmc.LOGNOTICE)


class Media:

    def __init__(self):
        self.mi = MediaInfo()

    def getInfos(self, file):
        self.mi.Open(file)
        width = self.mi.Get(Stream.Video, 0, "Width")
        height = self.mi.Get(Stream.Video, 0, "Height")
        ratio = self.mi.Get(Stream.Video, 0, "PixelAspectRatio")
        dar = self.mi.Get(Stream.Video, 0, "DisplayAspectRatio") #added to get dar
        self.mi.Close()
        try:
            width = int(float(width))
            height = int(float(height))
        except:
            width = int(0)
            height = int(0)
        try:
            dar = float(dar)
        except:
            dat = float(0)

        return [width, height, 1, dar] #mod to return dar
