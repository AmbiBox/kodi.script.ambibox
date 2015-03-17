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
import xbmc
import json

def get_installedversion():
    # retrieve current installed version
    json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Application.GetProperties", "params": {"properties": ["version", "name"]}, "id": 1 }')
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_query = json.loads(json_query)
    version_installed = []
    if json_query.has_key('result') and json_query['result'].has_key('version'):
        version_installed  = json_query['result']['version']
    return version_installed

def gotham_abortloop(timeout, monitor_instance=None):
    ret = xbmc.abortRequested
    if ret is False:
        xbmc.sleep(timeout)
    return ret

def helix_abortloop(timeout, monitor_instance=None):
    if monitor_instance is None:
        monitor_instance = xbmc.Monitor()
    return monitor_instance.waitForAbort(timeout/1000.0)

# from gotham2helix import get_installedversion
# ver = get_installedversion()
# if int(ver['major']) > 13:
#     from gotham2helix import helix_abortloop as abortloop
# else:
#     from gotham2helix import gotham_abortloop as abortloop
