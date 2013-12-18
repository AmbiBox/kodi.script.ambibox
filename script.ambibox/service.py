
#Modules General
import os,AmbiBox
from sys import argv

# Modules XBMC
import xbmc, xbmcgui, xbmcaddon

__settings__ = xbmcaddon.Addon( "script.ambibox" )
__language__ = __settings__.getLocalizedString
#########################################################################################################
## BEGIN
#########################################################################################################
ambibox = AmbiBox.AmbiBox(__settings__.getSetting("host"), int(__settings__.getSetting("port")))
ambibox.connect() 
menu = ambibox.getProfiles()
menu.append(__language__(32021))  
menu.append(__language__(32022))
off = len(menu)-2 
on = len(menu)-1
quit = False
while not quit:
    selected = xbmcgui.Dialog().select(__language__(32020), menu)
    if selected != -1:
        ambibox.lock()
        if (off == int(selected)):
            ambibox.turnOff() 
        elif (on == int(selected)):
            ambibox.turnOn() 
        else:
            ambibox.turnOn()
            ambibox.setProfile(menu[selected])
        ambibox.unlock
    quit = True
ambibox.disconnect()
