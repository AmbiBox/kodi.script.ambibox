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


from xml.etree import cElementTree as ET
from collections import Counter
import re
import time
import xml.dom.minidom as xdm

import xbmcaddon
import xbmcvfs
from xbmcoutput import info


class KeyboardXml(object):

    def parsexml(self, fn):
        if xbmcvfs.exists(fn):
            with open(fn, 'rt') as f:
                try:
                    tree = ET.parse(f)
                except ET.ParseError, e:
                    info('Error in keyboard.xml file, skipping keymap processing')
                    info(str(e.message))
                    tree = None
                return tree
        else:
            return None

    def findkeybyname(self, element, keyname, modlist):
        """
        @type element: xml.etree.ElementTree.Element
        @type keyname: str
        @type modlist: list
        @return:
        @rtype: xml.etree.ElementTree.Element
        """
        keys = element.findall('./%s' % keyname)
        retkey = None
        for key in keys:
            if key.get('mod') is None and len(modlist) == 0:
                retkey = key
                break
            elif len(modlist) == 0 and key.get('mod') is not None:
                retkey = None
                break
            elif len(modlist) != 0 and key.get('mod') is None:
                retkey = None
                break
            else:
                modstr = key.attrib['mod']
                mods = modstr.split(',')
                if Counter(mods) == Counter(modlist):  # compares hashes of strings so that order doesn't matter
                    retkey = key
                    break
        return retkey

    def savexml(self, tree, fn):
        tstr = ET.tostring(tree.getroot(), encoding='utf-8', method='xml')
        xml = xdm.parseString(tstr)
        uglyXml = xml.toprettyxml(indent='  ')
        text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
        prettyXml = text_re.sub('>\g<1></', uglyXml)
        p2 = re.sub(r'\n(\s+\n)+', '\n', prettyXml)
        p3 = re.sub(r'<\?.+?\?>', r'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'.encode('string_escape'),
                    p2)
        p4 = p3.encode('utf-8')
        if xbmcvfs.exists(fn):
            with open(fn, 'r') as fo:
                oldxml = fo.read()
            if Counter(oldxml) != Counter(p4):  # Only make backup and rewrite if new xml is different
                bakfn = fn + '-' + time.strftime('%Y%m%d-%H%M', time.localtime()) + '.bak.xml'
                if xbmcvfs.exists(bakfn):
                    xbmcvfs.delete(bakfn)
                xbmcvfs.rename(fn, bakfn)
                with open(fn, 'w') as fo:
                    fo.write(p4)
        else:
            with open(fn, 'w') as fo:
                fo.write(p4)

    def findkeyswithcmd(self, elementx, commandtext):
        """
        @type elementx: xml.etree.ElementTree.Element
        @type commandtext: str
        @return:
        @rtype: xml.etree.ElementTree.Element
        """

        keys = [element for element in elementx.iter() if element.text == commandtext]
        if len(keys) != 0:
            return keys[0]
        else:
            return None

    def translate_key_settingsxml(self, key_type):
        __settings = xbmcaddon.Addon('script.ambibox')
        checks = ['ctrl', 'shift', 'alt']
        mod = []
        for check in checks:
            if __settings.getSetting(key_type + '_' + check) == 'true':
                mod.append(check)
        key = (__settings.getSetting(key_type + '_str')[0:2]).lower()
        if key[0:1] != 'f':
            key2 = key[0:1]
        else:
            if key[1].isdigit():
                key2 = key
            else:
                key2 = 'f'
        ret = [key2, mod]
        return ret

    def create_element(self, element, tag, lst, idx=0):
        if idx == 0:
            if len(lst) == 0:
                return ET.SubElement(element, tag)
            else:
                return ET.SubElement(element, tag, attrib={'mod': ','.join(lst)})
        else:
            myelem = ET.Element(tag)
            if len(lst) != 0:
                myelem.attrib = {'mod': ','.join(lst)}
            return element.insert(idx, myelem)

    def process_keyboard_settings(self):
        try:
            fn = r"C:\Users\Ken User\AppData\Roaming\XBMC\userdata\keymaps\keyboard.xml"
            keylst = [self.translate_key_settingsxml('key_off'), self.translate_key_settingsxml('key_on')]
            cmdlst = [r'XBMC.RunScript(special://home\addons\script.ambibox\switch.py, off)',
                      r'XBMC.RunScript(special://home\addons\script.ambibox\switch.py, on)']
            if xbmcvfs.exists(fn):
                tree = self.parsexml(fn)
                if tree is None:
                    return
                root = tree.getroot()
                myroot = root.find('./global/keyboard')
                if myroot is not None:
                    for key, cmd in zip(keylst, cmdlst):
                        mkey = self.findkeybyname(myroot, key[0], key[1])
                        mcmd = self.findkeyswithcmd(myroot, cmd)
                        if mcmd is None and mkey is None:  # No key or command set
                            # Add new key
                            newkey = self.create_element(myroot, key[0], key[1])
                            newkey.text = cmd
                        elif mkey == mcmd:  # Key already correctly set
                            continue
                        elif (mkey is not None and mcmd is not None) and (mkey != mcmd):  # Key in use and other key set
                            # Remove other key set for command and change key in use to use command
                            myroot.remove(mcmd)
                            idx = myroot.getchildren().index(mkey)
                            comment_element = ET.Comment(ET.tostring(mkey))
                            myroot.insert(idx, comment_element)
                            mkey.text = cmd
                        elif mkey is not None and mcmd is None:  # Key in use, no other key set for command
                            # Change key to command
                            idx = myroot.getchildren().index(mkey)
                            comment_element = ET.Comment(ET.tostring(mkey))
                            myroot.insert(idx, comment_element)
                            mkey.text = cmd
                        elif mcmd is not None and mkey is None:  # Command set for other key, desired key not in use
                            # Remove mcmd, add new key
                            myroot.remove(mcmd)
                            newkey = self.create_element(myroot, key[0], key[1])
                            newkey.text = cmd
                        else:
                            pass
                else:
                    myroot = root.find('./global')
                    if myroot is not None:  # create keyboard and add two keys
                        newkb = ET.SubElement(myroot, 'keyboard')
                        newkb.tail = '\n'
                    else:
                        newgl = ET.SubElement(root, 'global')
                        newkb = ET.SubElement(newgl, 'keyboard')
                    for key, cmd in zip(keylst, cmdlst):
                        newkey = self.create_element(newkb, key[0], key[1])
                        newkey.text = cmd
                self.savexml(tree, fn)
            else:  # create file and write xml
                root = ET.Element('keymap')
                newgl = ET.SubElement(root, 'global')
                newkb = ET.SubElement(newgl, 'keyboard')
                for key, cmd in zip(keylst, cmdlst):
                    newkey = self.create_element(newkb, key[0], key[1])
                    newkey.text = cmd
                mytree = ET.ElementTree(root)
                self.savexml(mytree, fn)
        except Exception, e:
            info('Error in keyboard xml processing')
            if hasattr(e, 'message'):
                info(str(e.message))
        else:
            info('keyboard.xml processed succesfully')