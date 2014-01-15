
#Modules General
import AmbiBox
import os
import sys
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
showmenu = int(__settings__.getSetting("show_menu"))
menu = ambibox.getProfiles()
menu.append(__language__(32021))  
menu.append(__language__(32022))
if (showmenu == 0): 
    menu.append(__language__(32023))
else:
    menu.append(__language__(32024))

off = len(menu)-3 
on = len(menu)-2
show = len(menu)-1
quit = False
selected = xbmcgui.Dialog().select(__language__(32020), menu) 
if selected != -1: 
    if (show == int(selected)):        
        if (showmenu == 0):
            __settings__.setSetting("show_menu", "1")
        else:
            __settings__.setSetting("show_menu", "0")
    else:
        ambibox.lock()
        if (off == int(selected)):
            ambibox.turnOff() 
        elif (on == int(selected)):
            ambibox.turnOn() 
        else:
            #ambibox.turnOn()
            ambibox.setProfile(menu[selected])
        ambibox.unlock()
ambibox.disconnect()   

