#Modules General
#import time
#import mmap

# Modules XBMC
import xbmc
import xbmcgui
import xbmcaddon

# Modules AmbiBox
import AmbiBox

__settings__ = xbmcaddon.Addon("script.ambibox")
__language__ = __settings__.getLocalizedString


def notification(text):
    text = text.encode('utf-8')
    icon = __settings__.getAddonInfo("icon")
    smallicon = icon.encode("utf-8")
    if __settings__.getSetting("notification") == 'true':
        xbmc.executebuiltin('Notification(AmbiBox,' + text + ',3000,' + smallicon + ')')


class CapturePlayer(xbmc.Player):
    def __init__(self):
        print "service AmbiBox connect"
        self.ambibox = AmbiBox.AmbiBox(__settings__.getSetting("host"), int(__settings__.getSetting("port")))
        self.ambibox.connect()

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

    def onPlayBackStopped(self):
        self.ambibox.lock()
        self.setProfile(__settings__.getSetting("default_enable"), __settings__.getSetting("default_profile"))
        self.ambibox.unlock()

    def close(self):
        self.ambibox.lock()
        self.ambibox.turnOff()
        self.ambibox.unlock()
        self.ambibox.disconnect()


print "service AmbiBox"
notification(__language__(32030))

player = CapturePlayer()
while not xbmc.abortRequested:
    xbmc.sleep(1000)

# set off
notification(__language__(32031))
print "set status off for AmbiBox"
player.close()
player = None
