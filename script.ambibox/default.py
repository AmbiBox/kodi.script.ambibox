# Modules XBMC
import xbmc
import xbmcgui
import xbmcaddon

#Modules Ambibox
import AmbiBox

__settings__ = xbmcaddon.Addon("script.ambibox")
__language__ = __settings__.getLocalizedString


ambibox = AmbiBox.AmbiBox(__settings__.getSetting("host"), int(__settings__.getSetting("port")))
ambibox.connect()
menu = ambibox.getProfiles()
menu.append(__language__(32021))
off = len(menu) - 1
end = False
while not end:
    selected = xbmcgui.Dialog().select(__language__(32020), menu)
    if selected != -1:
        ambibox.lock()
        if off == int(selected):
            ambibox.turnOff()
        else:
            ambibox.turnOn()
            ambibox.setProfile(menu[selected])
        ambibox.unlock()
    end = True
ambibox.disconnect()
