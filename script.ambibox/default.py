#Modules General
import os
import sys
import mmap
import time

# import rpdb2
# rpdb2.start_embedded_debugger('pw')

# Modules XBMC
import xbmc
import xbmcgui
import xbmcaddon

# Modules AmbiBox
import AmbiBox

from xml.etree import ElementTree    #Added

__addon__ = xbmcaddon.Addon()
__cwd__ = __addon__.getAddonInfo('path')
__scriptname__ = __addon__.getAddonInfo('name')
__settings__ = xbmcaddon.Addon("script.ambibox")
__language__ = __settings__.getLocalizedString
__data__ = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'data'))    #Added
__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib'))

sys.path.append(__resource__)
sys.path.append(__data__)  #Added

from Media import *
media = Media()

ambibox = AmbiBox.AmbiBox(__settings__.getSetting("host"), int(__settings__.getSetting("port")))

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
        xbmc.Player.__init__(self)
        self.inDataMap = None

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

    def showmenu(self):
        menu = ambibox.getProfiles()
        menu.append(__language__(32021))
        menu.append(__language__(32022))
        off = len(menu)-2
        on = len(menu)-1
        quit = False
        time.sleep(1)
        selected = xbmcgui.Dialog().select(__language__(32020), menu)
        while not quit:
            if selected != -1:
                ambibox.lock()
                if (off == int(selected)):
                    ambibox.turnOff()
                elif (on == int(selected)):
                    ambibox.turnOn()
                else:
                    ambibox.turnOn()
                    self.setProfile('true', menu[selected])
                ambibox.unlock()
            quit = True

    def onPlayBackStarted(self):
        ambibox.connect()
        infos = media.getInfos(self.getPlayingFile())
        __settings = xbmcaddon.Addon("script.ambibox")
        if self.isPlayingAudio():
            self.setProfile(__settings.getSetting("audio_enable"), __settings.getSetting("audio_profile"))

        if self.isPlayingVideo():
            videomode = __settings.getSetting("video_choice")
            try:
                videomode = int(videomode)
            except:
                videomode = 2

            if videomode == 0:    #Use Default Video Profile
                self.setProfile('true', __settings.getSetting("video_profile"))
            elif videomode == 1:  #Autoswitch
                DAR = infos[3]
                if DAR <> 0:
                    SetAbxProfile(DAR)
                else:
                    info("Error retrieving DAR from video file")
            elif videomode == 2:   #Show menu
                show_menu = int(__settings.getSetting("show_menu"))
                if (show_menu == 1):
                    self.showmenu()
            elif videomode == 3:   #Turn off
                ambibox.lock()
                ambibox.turnOff()
                ambibox.unlock()

            if __settings.getSetting("directXBMC_enable") == 'true':   #Added

                capture = xbmc.RenderCapture()

                width = infos[0]
                height = infos[1]
                ratio = infos[2]
                if (width <> 0 and height <> 0 and ratio <> 0):

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
                else:
                    info("Error retrieving video file dimensions")

    def onPlayBackEnded(self):
        ambibox.connect()
        __settings = xbmcaddon.Addon("script.ambibox")
        self.setProfile(__settings.getSetting("default_enable"), __settings.getSetting("default_profile"))
        if self.inDataMap is not None:
            self.inDataMap.close()
            self.inDataMap = None
        ambibox.lock()
        ambibox.turnOff()
        ambibox.unlock()


    def onPlayBackStopped(self):
        ambibox.connect()
        __settings = xbmcaddon.Addon("script.ambibox")
        self.setProfile(__settings.getSetting("default_enable"), __settings.getSetting("default_profile"))
        if self.inDataMap is not None:
            self.inDataMap.close()
            self.inDataMap = None
        ambibox.lock()
        ambibox.turnOff()
        ambibox.unlock()


    def close(self):
        ambibox.connect()
        ambibox.lock()
        ambibox.turnOff()
        ambibox.unlock()
        ambibox.disconnect()
        __settings = None
        if self.inDataMap is not None:
            self.inDataMap.close()
            self.inDataMap = None


# Added functions
def SetAbxProfile(dar):
    __settings = xbmcaddon.Addon("script.ambibox")
    ambibox = AmbiBox.AmbiBox(__settings.getSetting("host"), int(__settings.getSetting("port")))
    ret = ""
    if ambibox.connect() == 0:
        pfls = ambibox.getProfiles()
        pname = GetProfileName(pfls, dar)
        player.setProfile('true', pname)
    return ret


def GetProfileName(pfls, DisplayAspectRatio):
    __settings = xbmcaddon.Addon("script.ambibox")
    fname = __data__ + '\\dardata.xml'
    if os.path.isfile(fname):
        try:
            doc = ElementTree.parse(fname)
        except:
            ret = __settings.getSetting("default_profile")
            return ret
        root = doc.getroot()
        apfls = root.findall('profile')
        ret = ""
        for apfl in apfls:
            aname =  apfl.find('AmbiboxName').text
            strll = apfl.find('LowerLmt').text
            strul = apfl.find('UpperLmt').text
            ll = float(strll)
            ul = float(strul)
            if (DisplayAspectRatio >=ll) and (DisplayAspectRatio <= ul):
                ret = aname
                break
        if ret in pfls:
            return ret
        else:
            info("profile in xml not found by Ambibox")
            ret = __settings.getSetting("default_profile")
            return ret
    else:
        info("dardata.xml is missing")
        ret = __settings.getSetting("default_profile")
        return ret

# End of additional functions


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
