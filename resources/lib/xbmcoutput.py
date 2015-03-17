#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 KenV99
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import sys

import xbmc
import xbmcaddon
import xbmcgui
__settings__ = xbmcaddon.Addon("script.ambibox")

def notification(text, *silence):
    """
    Display an XBMC notification box, optionally turn off sound associated with it
    @type text: str
    @type silence: bool
    """
    scriptname = xbmcaddon.Addon().getAddonInfo('name')
    simul = 'Kodi' not in sys.executable
    if not simul:
        if __settings__.getSetting('notification') == 'false':
            return
        text = text.encode('utf-8')
        info(text)
        if ((scriptname == 'script.ambibox') and (xbmcaddon.Addon().getSetting('notification') ==
                                                  'true')) or (scriptname != 'script.ambibox'):
            icon = xbmcaddon.Addon().getAddonInfo("icon")
            smallicon = icon.encode("utf-8")
            # xbmc.executebuiltin('Notification(AmbiBox,' + text + ',1000,' + smallicon + ')')
            dialog = xbmcgui.Dialog()
            if silence:
                dialog.notification(scriptname, text, smallicon, 1000, False)
            else:
                dialog.notification(scriptname, text, smallicon, 1000, True)
    else:
        print text


def debug(txt):
    scriptname = xbmcaddon.Addon().getAddonInfo('name')
    simul = 'Kodi' not in sys.executable
    if isinstance(txt, str):
        txt = txt.decode("utf-8")
    message = u"### [%s] - %s" % (scriptname, txt)
    if not simul:
        xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)
    else:
        print message


def info(txt):
    scriptname = xbmcaddon.Addon().getAddonInfo('name')
    simul = 'Kodi' not in sys.executable
    if isinstance(txt, str):
        txt = txt.decode("utf-8")
    message = u"### [%s] - %s" % (scriptname, txt)
    if not simul:
        xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGNOTICE)
    else:
        print message
