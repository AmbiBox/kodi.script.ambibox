#Modules General
import os
import time
from sys import argv

import AmbiBox


# Modules XBMC
import xbmc, xbmcgui, xbmcaddon

__settings__ = xbmcaddon.Addon("script.ambibox")
__language__ = __settings__.getLocalizedString


def notification(text):
    import os.path

    text = text.encode('utf-8')
    icon = __settings__.getAddonInfo("icon")
    smallicon = icon.encode("utf-8")
    if __settings__.getSetting("notification") == 'true':
        xbmc.executebuiltin('Notification(AmbiBox,' + text + ',3000,' + smallicon + ')')


def setProfile(enable, profile):
    if enable == 'true':
        notification(__language__(32032) % profile)
        ambibox.turnOn()
        ambibox.setProfile(profile)
    else:
        notification(__language__(32031))
        ambibox.turnOff()


print "service AmbiBox"
notification(__language__(32030))
print "service AmbiBox connect"
ambibox = AmbiBox.AmbiBox(__settings__.getSetting("host"), int(__settings__.getSetting("port")))
ambibox.connect()
oldstatus = -1
while not xbmc.abortRequested:
    newstatus = 0
    player = xbmc.Player()
    audioIsPlaying = player.isPlayingAudio()
    videoIsPlaying = player.isPlayingVideo()
    if videoIsPlaying:
        newstatus = 1
    if audioIsPlaying:
        newstatus = 2
    if oldstatus != newstatus:
        oldstatus = newstatus
        ambibox.lock()
        if newstatus == 0:
            setProfile(__settings__.getSetting("default_enable"), __settings__.getSetting("default_profile"))
        if newstatus == 1:
            setProfile(__settings__.getSetting("video_enable"), __settings__.getSetting("video_profile"))
        if newstatus == 2:
            setProfile(__settings__.getSetting("audio_enable"), __settings__.getSetting("audio_profile"))
        ambibox.unlock()
    time.sleep(1)

# set off
notification(__language__(32031))
print "set status off for AmbiBox"
ambibox.lock()
ambibox.turnOff()
ambibox.unlock()
ambibox.disconnect()
