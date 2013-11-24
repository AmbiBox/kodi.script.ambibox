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


LENGTHDATAMAP = 8294400


def notification(text):
    text = text.encode('utf-8')
    icon = __settings__.getAddonInfo("icon")
    smallicon = icon.encode("utf-8")
    if __settings__.getSetting("notification") == 'true':
        xbmc.executebuiltin('Notification(AmbiBox,' + text + ',1000,' + smallicon + ')')


def debug(msg):
    xbmc.log("### [%s] - %s" % (__scriptname__, msg,), level=xbmc.LOGDEBUG)


def info(msg):
    xbmc.log("### [%s] - %s" % (__scriptname__, msg,), level=xbmc.LOGNOTICE)


class CapturePlayer(xbmc.Player):
    def __init__(self):
        debug("service AmbiBox connect")
        self.ambibox = AmbiBox.AmbiBox(__settings__.getSetting("host"), int(__settings__.getSetting("port")))
        self.ambibox.connect()
        self.inDataMap = mmap.mmap(0, LENGTHDATAMAP, 'AmbiBox_XBMC_SharedMem', mmap.ACCESS_WRITE)

    def setProfile(self, enable, profile):
        if enable == 'true':
            notification(__language__(32032) % profile)
            self.ambibox.turnOn()
            self.ambibox.setProfile(profile)
        else:
            notification(__language__(32031))
            self.ambibox.turnOff()

    def onPlayBackStarted(self):
        if self.isPlayingAudio():
            self.ambibox.lock()
            self.setProfile(__settings__.getSetting("audio_enable"), __settings__.getSetting("audio_profile"))
            self.ambibox.unlock()

        if self.isPlayingVideo():
            self.ambibox.lock()
            self.setProfile(__settings__.getSetting("video_enable"), __settings__.getSetting("video_profile"))
            self.ambibox.unlock()

            capture = xbmc.RenderCapture()

            infos = media.getInfos(self.getPlayingFile())
            width = infos[0]
            height = infos[1]
            ratio = infos[2]
            notification("%d => %dx%d" % (ratio, width, height))

            capture.capture(width, height, xbmc.CAPTURE_FLAG_CONTINUOUS)

            while self.isPlayingVideo():
                capture.waitForCaptureStateChangeEvent()
                if capture.getCaptureState() == xbmc.CAPTURE_STATE_DONE:
                    self.inDataMap.seek(0)
                    seeked = self.inDataMap.read_byte()
                    if ord(seeked) == 248:
                        # self.inDataMap.seek(1)
                        # # width
                        # self.inDataMap.write_byte(chr((width >> 8) & 0xff))
                        # self.inDataMap.write_byte(chr(width & 0xff))
                        # # height
                        # self.inDataMap.write_byte(chr((height >> 8) & 0xff))
                        # self.inDataMap.write_byte(chr(height & 0xff))
                        # # aspect ratio
                        # self.inDataMap.write_byte(chr(int(ratio * 100)))
                        # # image format
                        # fmt = capture.getImageFormat()
                        # if fmt == 'RGBA':
                        #     self.inDataMap.write_byte(chr(0))
                        # elif fmt == 'BGRA':
                        #     self.inDataMap.write_byte(chr(1))
                        # else:
                        #     self.inDataMap.write_byte(chr(2))
                        # image = capture.getImage()
                        # length = len(image)
                        # # datasize
                        # self.inDataMap.write_byte(chr((length >> 24) & 0xff))
                        # self.inDataMap.write_byte(chr((length >> 16) & 0xff))
                        # self.inDataMap.write_byte(chr((length >> 8) & 0xff))
                        # self.inDataMap.write_byte(chr(length & 0xff))
                        # # data
                        # for b in image:
                        #     self.inDataMap.write_byte(chr(b))
                        # self.inDataMap.seek(0)
                        # self.inDataMap.write_byte(chr(240))

                        # self.inDataMap.seek(1)
                        # width
                        self.inDataMap[1] = chr((width >> 8) & 0xff)
                        self.inDataMap[2] = chr(width & 0xff)
                        # height
                        self.inDataMap[3] = (chr((height >> 8) & 0xff))
                        self.inDataMap[4] = (chr(height & 0xff))
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
                        self.inDataMap[7] = (chr((length >> 24) & 0xff))
                        self.inDataMap[8] = (chr((length >> 16) & 0xff))
                        self.inDataMap[9] = (chr((length >> 8) & 0xff))
                        self.inDataMap[10] = (chr(length & 0xff))
                        # data
                        self.inDataMap[11:] = image

                        self.inDataMap[0] = (chr(240))

    def onPlayBackStopped(self):
        self.ambibox.lock()
        self.setProfile(__settings__.getSetting("default_enable"), __settings__.getSetting("default_profile"))
        self.ambibox.unlock()

    def close(self):
        self.ambibox.lock()
        self.ambibox.turnOff()
        self.ambibox.unlock()
        self.ambibox.disconnect()


debug("service AmbiBox")
notification(__language__(32030))

player = CapturePlayer()
while not xbmc.abortRequested:
    xbmc.sleep(1000)

# set off
notification(__language__(32031))
debug("set status off for AmbiBox")
player.close()
player = None
