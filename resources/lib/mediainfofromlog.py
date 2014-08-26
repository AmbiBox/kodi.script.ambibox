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


def get_log_mediainfo():
    """
    Retrieves dimensions and framerate information from XBMC.log
    Will likely fail if XBMC in debug mode - could be remedied by increasing the number of lines read
    Props: http://stackoverflow.com/questions/260273/most-efficient-way-to-search-the-last-x-lines-of-a-file-in-python
    @return: dict() object with the following keys:
                                'pwidth' (int)
                                'pheight' (int)
                                'par' (float)
                                'dwidth' (int)
                                'dheight' (int)
                                'dar' (float)
                                'fps' (float)
    @rtype: dict()
    """
    logfn = xbmc.translatePath(r'special://home\XBMC.log')
    xbmc.sleep(250)  # found originally that it wasn't written yet
    if is_xbmc_debug():
        lookbacksize = 6144
        lookbacklines = 60
    else:
        lookbacksize = 1024
        lookbacklines = 10
    with open(logfn, "r") as f:
        f.seek(0, 2)           # Seek @ EOF
        fsize = f.tell()        # Get Size
        f.seek(max(fsize - lookbacksize, 0), 0)  # Set pos @ last n chars
        lines = f.readlines()       # Read to end
    lines = lines[-lookbacklines:]    # Get last n lines
    ret = None
    for line in lines:
        if 'fps:' in line:
            start = line.find('fps:')
            sub = line[start:].rstrip('\n')
            tret = dict(item.split(":") for item in sub.split(","))
            ret = {}
            for key in tret:
                tmp = key.strip()
                try:
                    if tmp == 'fps':
                        ret['fps'] = float(tret[key])
                    else:
                        ret[tmp] = int(tret[key])
                except ValueError:
                    pass
            if ret['pheight'] != 0:
                ret['par'] = float(ret['pwidth'])/float(ret['pheight'])
            if ret['dheight'] != 0:
                ret['dar'] = float(ret['dwidth'])/float(ret['dheight'])
    return ret


def is_xbmc_debug():
    json_query = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Settings.getSettings", "params":'
                                     ' { "filter":{"section":"system", "category":"debug"} } }')
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_response = json.loads(json_query)

    if json_response.has_key('result') and json_response['result'].has_key('settings') and json_response['result']['settings'] is not None:
        for item in json_response['result']['settings']:
            if item["id"] == "debug.showloginfo":
                if item["value"] is True:
                    return True
                else:
                    return False