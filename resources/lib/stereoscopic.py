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

from json import load as jloads
import xbmc


def getStereoscopicMode():
    query = '{"jsonrpc": "2.0", "method": "GUI.GetProperties", "params": {"properties": ["stereoscopicmode"]}, "id": 1}'
    result = xbmc.executeJSONRPC(query)
    jsonr = jloads(result)
    print jsonr
    ret = 'unknown'
    if jsonr.has_key('result'):
        if jsonr['result'].has_key('stereoscopicmode'):
            if jsonr['result']['stereoscopicmode'].has_key('mode'):
                ret = jsonr['result']['stereoscopicmode']['mode'].encode('utf-8')
    #"off", "split_vertical", "split_horizontal", "row_interleaved", "hardware_based", "anaglyph_cyan_red",
    #"anaglyph_green_magenta", "monoscopic"
    return ret