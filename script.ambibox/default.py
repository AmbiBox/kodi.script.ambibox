#Modules General
import os
import sys
import mmap

# Modules XBMC
import xbmc
import xbmcgui
import xbmcaddon

# Modules AmbiBox
import AmbiBox

__addon__ = xbmcaddon.Addon()
__cwd__ = __addon__.getAddonInfo('path')
__scriptname__ = __addon__.getAddonInfo('name')
__settings__ = xbmcaddon.Addon("script.ambibox")
__language__ = __settings__.getLocalizedString

__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib'))

sys.path.append(__resource__)

from Media import *
media = Media()


def notification(text):
    text = text.encode('utf-8')
    info(text)
    if __settings__.getSetting("notification") == 'true':
        icon = __settings__.getAddonInfo("icon")
        smallicon = icon.encode("utf-8")
        xbmc.executebuiltin('Notification(AmbiBox,' + text + ',1000,' + smallicon + ')')

def debug(msg):
    xbmc.log("### [%s] - %s" % (__scriptname__, msg,), level=xbmc.LOGDEBUG)


def info(msg):
    xbmc.log("### [%s] - %s" % (__scriptname__, msg,), level=xbmc.LOGNOTICE)


class CapturePlayer(xbmc.Player):
    def __init__(self):
        self.inDataMap = None
        self.setProfile(__settings__.getSetting("default_enable"), __settings__.getSetting("default_profile"))

    def setProfile(self, enable, profile):
        ambibox.lock()
        if enable == 'true':
            notification(__language__(32033) % profile)
            ambibox.turnOn()
            ambibox.setProfile(profile)
        else:
            notification(__language__(32032))
            ambibox.turnOff()
        ambibox.unlock()

    def onPlayBackStarted(self):
        if self.isPlayingAudio():
            self.setProfile(__settings__.getSetting("audio_enable"), __settings__.getSetting("audio_profile"))

        if self.isPlayingVideo():
            self.setProfile(__settings__.getSetting("video_enable"), __settings__.getSetting("video_profile"))

            capture = xbmc.RenderCapture()

            infos = media.getInfos(self.getPlayingFile())
            width = infos[0]
            height = infos[1]
            ratio = infos[2]
            debug("%d => %dx%d" % (ratio, width, height))

            self.inDataMap = mmap.mmap(0, width * height * 4 + 11, 'AmbiBox_XBMC_SharedMem', mmap.ACCESS_WRITE)

            capture.capture(width, height, xbmc.CAPTURE_FLAG_CONTINUOUS)

            while self.isPlayingVideo():
                capture.waitForCaptureStateChangeEvent()
                if capture.getCaptureState() == xbmc.CAPTURE_STATE_DONE:
                    self.inDataMap.seek(0)
                    seeked = self.inDataMap.read_byte()
                    if ord(seeked) == 248:
                        # width
                        self.inDataMap[1] = chr(width & 0xff)
                        self.inDataMap[2] = chr((width >> 8) & 0xff)
                        # height
                        self.inDataMap[3] = (chr(height & 0xff))
                        self.inDataMap[4] = (chr((height >> 8) & 0xff))
                        # aspect ratio
                        self.inDataMap[5] = (chr(int(ratio * 100)))
                        # image format
                        fmt = capture.getImageFormat()
                        if fmt == 'RGBA':
                            self.inDataMap[6] = (chr(0))
                        elif fmt == 'BGRA':
                            self.inDataMap[6] = (chr(1))
                        else:
                            self.inDataMap[6] = (chr(2))
                        image = capture.getImage()
                        length = len(image)
                        # datasize
                        self.inDataMap[7] = (chr(length & 0xff))
                        self.inDataMap[8] = (chr((length >> 8) & 0xff))
                        self.inDataMap[9] = (chr((length >> 16) & 0xff))
                        self.inDataMap[10] = (chr((length >> 24) & 0xff))
                        # data
                        self.inDataMap[11:(11+length)] = str(image)
                        # write first byte to indicate we finished writing the data
                        self.inDataMap[0] = (chr(240))

            self.inDataMap.close()
            self.inDataMap = None

    def onPlayBackStopped(self):
        self.setProfile(__settings__.getSetting("default_enable"), __settings__.getSetting("default_profile"))
        if self.inDataMap is not None:
            self.inDataMap.close()
            self.inDataMap = None

    def close(self):
        ambibox.lock()
        ambibox.turnOff()
        ambibox.unlock()
        ambibox.disconnect()
        if self.inDataMap is not None:
            self.inDataMap.close()
            self.inDataMap = None

ambibox = AmbiBox.AmbiBox(__settings__.getSetting("host"), int(__settings__.getSetting("port")))
if ambibox.connect() == 0:
    notification(__language__(32030))
    player = CapturePlayer()
else:
    notification(__language__(32031))
    player = None

while not xbmc.abortRequested:
    if player is None:
        xbmc.sleep(1000)
        if ambibox.connect() == 0:
            notification(__language__(32030))
            player = CapturePlayer()
    else:
        xbmc.sleep(100)

if player is not None:
    # set off
    notification(__language__(32032))
    player.close()
    player = None
