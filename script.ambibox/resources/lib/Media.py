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
        nfile = self.smbToUNC(file)
        self.mi.Open(nfile)
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
            dar = float(0)

        return [width, height, 1, dar] #mod to return dar
    def smbToUNC(self, smbFile):
        testFile = smbFile[0:3]
        newFile = ""
        if testFile == "smb":
            for i in xrange(0,len(smbFile)):
                if smbFile[i] == "/":
                    newFile = newFile + "\\"
                else:
                    newFile = newFile + smbFile[i]
            retFile = newFile[4:]
        else:
            retFile = smbFile
        return retFile

