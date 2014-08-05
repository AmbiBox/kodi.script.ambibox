# -*- coding: utf-8 -*-
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file LICENSE.txt.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *

# Modules General
import os
import sys
import mmap
import time
import re
from _winreg import *
import subprocess
from operator import itemgetter
import ctypes
import threading
from xml.etree import cElementTree as ET
from collections import namedtuple
# Modules XBMC
simul = 'XBMC' not in sys.executable
if simul:
    import xbmcsim as xbmc
else:
    import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
# Modules AmbiBox
from resources.lib.ambibox import AmbiBox
from resources.lib.abxtimer import Timer
from resources.lib.xbmcoutput import notification, debug, info
from resources.lib.keyboardxml import KeyboardXml

__language__ = None

if not simul:
    __addon__ = xbmcaddon.Addon()
    __cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode('utf-8')
    __scriptname__ = __addon__.getAddonInfo('name')
    __version__ = str(__addon__.getAddonInfo('version'))
    __settings__ = xbmcaddon.Addon("script.ambibox")
    __language__ = __settings__.getLocalizedString
    __settingsdir__ = xbmc.translatePath(os.path.join(__cwd__, 'resources'))
    __resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib'))
    mediax = None
    screenx = 0
    screeny = 0
    sar = 0.0
    ambibox = None
    scriptsettings = None
    kbs = None
    Arprofile_info = namedtuple('Arprofile_info', 'profile_name, aspectratio, lower_lmt, upper_lmt')
    xbmc_version = 0


def start_debugger(remote=False):
    if remote:
        if xbmcvfs.exists(
                r'C:\\Users\\Ken User\\AppData\\Roaming\\XBMC\\addons\\script.ambibox\\resources\\lib\\'
                r'pycharm-debug.py3k\\'):
            sys.path.append(
                r'C:\\Users\\Ken User\\AppData\\Roaming\\XBMC\\addons\\script.ambibox\\resources\\lib\\'
                r'pycharm-debug.py3k\\')
            import pydevd
            pydevd.settrace('192.168.1.103', port=51234, stdoutToServer=True, stderrToServer=True, suspend=False)
    else:
        if xbmcvfs.exists(r'C:\Program Files (x86)\JetBrains\PyCharm 3.1.3\pycharm-debug-py3k.egg'):
            sys.path.append(r'C:\Program Files (x86)\JetBrains\PyCharm 3.1.3\pycharm-debug-py3k.egg')
            import pydevd

            pydevd.settrace('localhost', port=51234, stdoutToServer=True, stderrToServer=True, suspend=False)


def chk_mediainfo():
    # Check if user has installed mediainfo.dll to resources/lib or has installed full Mediainfo package
    global mediax
    __usingMediaInfo__ = False
    if mediax is None:
        mi_url = xbmc.translatePath(os.path.join(__resource__ + '\\mediainfo.dll'))
        if xbmcvfs.exists(mi_url):
            __usingMediaInfo__ = True
        else:
            try:
                aReg = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
                key = OpenKey(aReg, r'Software\Microsoft\Windows\CurrentVersion\App Paths\MediaInfo.exe')
                path = QueryValue(key, None)
                CloseKey(key)
                CloseKey(aReg)
                if path != '':
                    __usingMediaInfo__ = True
            except WindowsError:
                pass
        if __usingMediaInfo__ is True:
            #from media import *
            try:
                # import media as mediax
                from resources.lib.media import Media as mediax
            except ImportError:
                mediax = None


class Profiles(object):
    def __init__(self):
        self._profile_dict = dict()

    def add(self, name, is_xbmc_direct):
        self._profile_dict[name] = is_xbmc_direct

    def profiles(self):
        return self._profile_dict

    def __len__(self):
        return len(self._profile_dict)

    def is_xbmc_direct(self, name):
        if name in self._profile_dict:
            return self._profile_dict[name]
        else:
            return None


class XbmcAmbibox(AmbiBox):
    LIGHTS_ON = True
    LIGHTS_OFF = False

    def __init__(self, host, port):
        self.ambiboxw_installed = False
        self.is_installed = False
        self.chkAmibiboxInstalled()
        self.is_running = False
        self.chk_ambiboxw_running()
        self.xbmc_started_ambiboxw = False
        self.leds_on = False
        self.current_profile = ''
        self.ambibox_process = None
        self.profiles = []
        super(XbmcAmbibox, self).__init__(host, port)
        if __settings__.getSetting('start_ambibox') == 'true' and self.is_running is False:
            self.start_ambiboxw()
        self.retrieve_profiles()

    def get_profiles(self):
        if len(self.profiles) == 0:
            self.retrieve_profiles()
        return self.profiles

    def retrieve_profiles(self):
        if self.connect() == 0:
            self.profiles = self.getProfiles()
        else:
            self.profiles = []
            aReg = ConnectRegistry(None, HKEY_CURRENT_USER)
            try:
                key = OpenKey(aReg, r'Software\Server IR\Backlight\Profiles')
                profileCount = QueryValueEx(key, 'ProfilesCount')
                if isinstance(profileCount[0], int):
                    count = int(profileCount[0])
                else:
                    count = 0
                for i in xrange(0, count):
                    key = OpenKey(aReg, r'Software\Server IR\Backlight\Profiles')
                    pname = QueryValueEx(key, 'ProfileName_%s' % str(i))
                    self.profiles.append(str(pname[0]))
                CloseKey(aReg)
            except WindowsError or EnvironmentError, e:
                info("Error reading profiles from registry")
                if hasattr(e, 'message'):
                    info(str(e.message))
                return
            except Exception, e:
                info("Other error reading profiles from registry")
                if hasattr(e, 'message'):
                    info(str(e.message))
                return

    def chkAmibiboxInstalled(self):
        # returns number of profiles if installed, 0 if installed with no profiles, -1 not installed
        aReg = ConnectRegistry(None, HKEY_CURRENT_USER)
        try:
            key = OpenKey(aReg, r'Software\Server IR\Backlight\Profiles')
            profileCount = QueryValueEx(key, 'ProfilesCount')
            if int(profileCount[0]) == 0:
                ret = 0
            else:
                ret = int(profileCount[0])
            CloseKey(key)
        except WindowsError or EnvironmentError:
            ret = -1
        CloseKey(aReg)
        if ret > 0:
            self.is_installed = True
        if ret == 0:
            notification(__language__(32006))  # @[No profiles configured in Ambibox]
            info('No profiles found in Ambibox')
        elif ret == -1:
            notification(__language__(32007))  # @[AmbiBox installation not found: exiting script]
            info('Ambibox installation not found: terminating script')
            sys.exit()
        return ret

    def chk_ambiboxw_running(self):
        proclist = []
        cmd = 'WMIC PROCESS get Caption,Commandline,Processid'
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        for line in proc.stdout:
            proclist.append(str(line))
        proc.terminate()
        del proc
        proclist.sort()
        self.is_running = False
        for proc in proclist:
            if proc[0:7] == "AmbiBox":
                self.is_running = True
                break
            elif str(proc[0:1]).lower() == 'b':
                break
        return self.is_running

    def start_ambiboxw(self):
        if self.is_running is False:
            self.chk_ambiboxw_running()
        if self.is_installed and self.is_running is False:
            aReg = ConnectRegistry(None, HKEY_CURRENT_USER)
            try:
                key = OpenKey(aReg, r'Software\Server IR')
                p = QueryValueEx(key, 'InstallPath')
                ambiboxpath = xbmc.translatePath(str(p[0]) + r'\Ambibox.exe')
                CloseKey(key)
                CloseKey(aReg)
            except WindowsError:
                CloseKey(aReg)
                return False
            try:
                popobj = subprocess.Popen([ambiboxpath])
                self.ambibox_process = popobj
                pid = popobj.pid
            except WindowsError as e:
                notification(__language__(32008))  # @[Ambibox could not be started]
                info('Could not start AmbiBox executable')
                if hasattr(e, 'message'):
                    info(e.message)
                sys.exit()
            else:
                if pid is not None:
                    self.is_running = True
                    self.lightSwitch(self.LIGHTS_OFF)
                    return True
                else:
                    notification(__language__(32008))  # @[Ambibox could not be started]
                    info('Could not start AmbiBox executable')
                    sys.exit()

    def __del__(self):
        if self.ambibox_process is not None:
            self.close()

    def set_profile(self, profile, enable=True, force=False):
        """
        If connected to AmbiBox, change the profile to profile.
        If force = true, turn on lights regardless of state
        @type enable: string (either 'true' or 'false')
        @type profile: string
        @type force: bool
        @rtype: None
        """
        self.current_profile = profile
        if self.connect() == 0:
            self.lock()
            if profile != 'None':
                notification(__language__(32033) % profile)  # @[Set profile %s]
                self.setProfile(profile)
            else:
                notification(__language__(32032))  # @[Ambibox turned off]
            self.unlock()
        if force or profile != 'None':
            self.lightSwitch(self.LIGHTS_ON)
        else:
            self.lightSwitch(self.LIGHTS_OFF)

    def lightSwitch(self, lightChangeState):
        global scriptsettings
        """
        lightchangestate is class constant either LIGHTS_ON or LIGHTS_OFF
        @param lightChangeState: LIGHTS_ON or LIGHTS_OFF
        @type  lightChangeState: bool
        @rtype: None
        """
        if self.connect() == 0:
            self.lock()
            try:
                if (lightChangeState is self.LIGHTS_ON) and scriptsettings.check_manual_switch() == 'on':
                    self.turnOn()
                elif lightChangeState is self.LIGHTS_OFF:
                    self.turnOff()
            except Exception:
                pass
            self.unlock()

    def switch_to_default_profile(self):
        global scriptsettings
        if scriptsettings.settings['default_enable'] is True:
            self.set_profile(scriptsettings.settings['default_profile'])
        else:
            self.lightSwitch(self.LIGHTS_OFF)

    def close(self):
        try:
            if self.ambibox_process is not None:
                self.ambibox_process.terminate()
                self.ambibox_process = None
        except Exception as e:
            info('Error deleting ambibox process')
            if hasattr(e, 'message'):
                info(str(e.message))


class ScriptSettings(object):
    def __init__(self):
        self.settings = dict()
        self.aspect_ratio_codes = ['43', '32', '169', '185', '22', '24']
        self.ar_dict = {'43': 1.333, '32': 1.5, '69': 1.778, '85': 1.85, '22': 2.2, '24': 2.4}
        self.stereo_modes = ['2D', '3DS', '3DT']
        self.aspect_ratio_settings = []
        self.profiles = Profiles()
        self.refresh_settings()

    def refresh_settings(self):
        global __settings__
        __settings__ = xbmcaddon.Addon('script.ambibox')
        self.settings = dict()
        settingliststr = ['host', 'port', 'notification', 'default_profile', 'audio_profile',
                          'video_profile', 'key_on_str', 'key_off_str']
        settinglistint = ['video_choice', 'directXBMC_quality']
        settinglistbool = ['notification', 'start_ambibox', 'default_enable', 'audio_enable', 'disable_on_screensaver',
                           'show_menu', 'use_threading', 'instrumented', '3D_enable', 'key_use', 'key_on_shift',
                           'key_on_ctrl', 'key_on_alt', 'key_off_shift', 'key_off_ctrl', 'key_off_alt']
        settinglistfloat = ['throttle']

        for s in settingliststr:
            self.settings[s] = str(__settings__.getSetting(s)).decode('utf-8')
        for s in settinglistint:
            try:
                self.settings[s] = int(__settings__.getSetting(s))
            except ValueError:
                info('Error reading integer settings')
        for s in settinglistbool:
            if __settings__.getSetting(s) == 'true':
                self.settings[s] = True
            else:
                self.settings[s] = False
        for s in settinglistfloat:
            self.settings[s] = int(__settings__.getSetting(s))
        self.chkProfileSettings()
        self.updateprofilesettings()
        self.get_ar_profiles()
        self.get_profile_types_from_reg()
        info('Settings refreshed')

    def check_manual_switch(self):
        global __settings__
        __settings__ = xbmcaddon.Addon('script.ambibox')
        return __settings__.getSetting('manual_switch')

    def get_ar_profiles(self):
        global ambibox
        global Arprofile_info
        arprofiles = {}
        ambiboxprofiles = ambibox.get_profiles()
        for stereomode in self.stereo_modes:
            tempprofiles = []
            for ar_code in self.aspect_ratio_codes:
                settingid = '%s_%s' % (stereomode, ar_code)
                profl = __settings__.getSetting(settingid)
                if profl != 'None':
                    spfl = settingid[len(settingid) - 2:]
                    ar = self.ar_dict[spfl]
                    ar_profileinfo = Arprofile_info(profile_name=profl, aspectratio=ar, lower_lmt=ar, upper_lmt=ar)
                    if profl in ambiboxprofiles:
                        tempprofiles.append(ar_profileinfo)
                    elif not ambiboxprofiles:
                        #Should never get to this statement
                        info("Profile existance not checked due to unavailability of Amibibox API")
                        tempprofiles.append(ar_profileinfo)
            tempprofiles.sort(key=itemgetter(1))
            arprofiles[stereomode] = tempprofiles
        for stereomode in self.stereo_modes:
            tempprofiles = arprofiles[stereomode]
            i1 = len(tempprofiles)
            new_profiles = []
            for i, pfl in enumerate(tempprofiles):
                if i == 0:
                    ll = 0.1
                else:
                    ll = float((pfl.aspectratio + tempprofiles[i - 1].aspectratio) / 2)
                if i == i1 - 1:
                    ul = 99
                else:
                    ul = float((pfl.aspectratio + tempprofiles[i + 1].aspectratio) / 2)
                new_profile_info = Arprofile_info(profile_name=pfl.profile_name, aspectratio=pfl.aspectratio,
                                                  lower_lmt=ll, upper_lmt=ul)
                new_profiles.append(new_profile_info)
            arprofiles[stereomode] = new_profiles
        self.aspect_ratio_settings = arprofiles

    def get_profile_types_from_reg(self):
        reg_pfl_names = []
        aReg = ConnectRegistry(None, HKEY_CURRENT_USER)
        try:
            key = OpenKey(aReg, r'Software\Server IR\Backlight\Profiles')
            profileCount = QueryValueEx(key, 'ProfilesCount')
            if isinstance(profileCount[0], int):
                count = int(profileCount[0])
            else:
                count = 0
            for i in xrange(0, count):
                key = OpenKey(aReg, r'Software\Server IR\Backlight\Profiles')
                pname = QueryValueEx(key, 'ProfileName_%s' % str(i))
                reg_pfl_names.append(str(pname[0]))
                try:
                    key = OpenKey(aReg, r'Software\Server IR\Backlight\Profiles\%s' % str(pname[0]))
                except Exception, e:
                    info('Error opening registry key for profile: %s' % str(pname[0]))
                    continue
                backlight_plugin_name = QueryValueEx(key, 'BacklightPluginName')
                grabber = QueryValueEx(key, 'Grabber')
                debug('Profile - Pname: %s  Plugin: %s  Grabber: %s' % (pname[0], backlight_plugin_name[0], grabber[0]))
                if grabber[0] == 8:
                    self.profiles.add(pname[0], True)
                else:
                    self.profiles.add(pname[0], False)
            CloseKey(aReg)
        except WindowsError or EnvironmentError, e:
            info("Error reading profile types from registry")
            if hasattr(e, 'message'):
                info(str(e.message))
            return
        except Exception, e:
            info("Other error reading profile types from registry")
            if hasattr(e, 'message'):
                info(str(e.message))
            return

    def chkProfileSettings(self):
        global scriptsettings
        if ambibox.connect() == 0:
            pfls = ambibox.get_profiles()
            sets2chk = ['default_profile', 'audio_profile', 'video_profile']
            vidfmts = ['2D', '3DS', '3DT']
            ars = ['43', '32', '169', '185', '22', '24']
            for vidfmt in vidfmts:
                for ar in ars:
                    setn = vidfmt + '_' + ar
                    sets2chk.append(setn)
            dirty = False
            for setn in sets2chk:
                pname = __settings__.getSetting(setn)
                if pname != 'None':
                    if not (pname in pfls):
                        dirty = True
                        __settings__.setSetting(setn, 'None')
                        info('Missing profile %s set to None' % setn)
            if dirty is True:
                self.refresh_settings()

    def updateprofilesettings(self):
        # updates choices (values="..") in settings.xml with profiles present in Ambibox program
        pstrl = []
        if ambibox.connect() == 0:
            pfls = ambibox.get_profiles()
            numpfls = len(pfls)
            info('%s profile(s) retrieved from program' % numpfls)
            defpfl = 'None'
            pstrl.append('None')
            pstrl.append('|')
            for pfl in pfls:
                pstrl.append(str(pfl))
                pstrl.append('|')
                if str(pfl).lower() == 'default':
                    defpfl = str(pfl)
            del pstrl[-1]
            pstr = "".join(pstrl)
            doc = ET.parse(__settingsdir__ + "\\settings.xml")
            repl = ".//setting[@type='labelenum']"
            fixg = doc.iterfind(repl)
            for fixe in fixg:
                fixe.set('values', pstr)
                fixe.set('default', defpfl)
            doc.write(__settingsdir__ + "\\settings.xml")
            xbmc.executebuiltin('UpdateLocalAddons')

    def set_setting(self, name, value):
        global __settings__
        __settings__ = xbmcaddon.Addon('script.ambibox')
        __settings__.setSetting(name, value)
        self.settings[name] = value


class CapturePlayer(xbmc.Player):
    def __init__(self, *args):
        self.re3D = re.compile("[-. _]3d[-. _]", re.IGNORECASE)
        self.reTAB = re.compile("[-. _]h?tab[-. _]", re.IGNORECASE)
        self.reSBS = re.compile("[-. _]h?sbs[-. _]", re.IGNORECASE)
        self.onPBSfired = False
        self.xd = None
        self.playing_file = ''
        super(CapturePlayer, self).__init__(*args)

    def showmenu(self):
        menu = ambibox.get_profiles()
        menu.append(__language__(32021))  # @[Backlight off] 
        menu.append(__language__(32022))  # @[Backlight on] 
        off = len(menu) - 2
        on = len(menu) - 1
        mquit = False
        xbmc.sleep(100)
        selected = xbmcgui.Dialog().select(__language__(32020), menu)  # @[Select profile] 
        while not mquit:
            if selected != -1:
                if (off == int(selected)):
                    ambibox.lightSwitch(ambibox.LIGHTS_OFF)
                elif (on == int(selected)):
                    ambibox.lightSwitch(ambibox.LIGHTS_ON)
                else:
                    ambibox.set_profile(menu[selected])
            mquit = True

    def onPlayBackPaused(self):
        pass

    def onPlayBackResumed(self):
        if self.getPlayingFile() != self.playing_file:
            self.onPlayBackEnded()
            self.onPlayBackStarted()

    def get_aspect_ratio(self):
        try:
            self.playing_file = self.getPlayingFile()
        except:
            info('Error retrieving video file from xbmc.player')
            return
        infos = [0, 0, 1, 0, 0]
        self.mi_called = False
        # Get aspect ratio
        # First try MediaInfo, then infoLabels, then Capture. Default to screen dimensions.

        #MediaInfo Method
        if mediax is not None:
            if self.playing_file[0:3] != 'pvr':  # Cannot use for LiveTV stream
                if xbmcvfs.exists(self.playing_file):
                    try:
                        infos = mediax().getInfos(self.playing_file)
                        self.mi_called = True
                    except:
                        infos = [0, 0, 1, 0, 0]
                    else:
                        if infos[3] != 0:
                            info('Aspect ratio determined by mediainfo.dll = % s' % infos[3])
                        else:
                            info('mediainfo.dll returned AR = 0')
                else:
                    infos = [0, 0, 1, 0, 0]
            else:
                xbmc.sleep(1000)

        #Info Label Method
        if infos[3] == 0:
            while xbmc.getInfoLabel("VideoPlayer.VideoAspect") is None:
                xbmc.sleep(500)
            vp_ar = xbmc.getInfoLabel("VideoPlayer.VideoAspect")
            try:
                infos[3] = float(vp_ar)
            except TypeError:
                infos[3] = float(0)
            else:
                info('Aspect ratio determined by InfoLabel = %s' % vp_ar)

        # Capture Method
        if infos[3] == 0:
            rc = xbmc.RenderCapture()
            infos[3] = rc.getAspectRatio()
            if not (0.95 < infos[3] < 1.05) and infos[3] != 0:
                info('Aspect ratio determined by XBMC.Capture = %s' % infos[3])
            else:
                # Fallback Method
                infos[3] = float(screenx) / float(screeny)
                info('Aspect ratio not able to be determined - using screen AR = %s' % infos[3])
        return infos

    def get_stereo_format(self):
        if scriptsettings.settings['3D_enable'] is True:
            # Get Stereoscopic Information
            # Use infoLabels
            #sm2 = getStereoscopicMode()
            stereomode = xbmc.getInfoLabel("VideoPlayer.StereoscopicMode")
            vidfmt = ''
            if stereomode == 'top_bottom':
                vidfmt = '3DT'
            elif stereomode == 'left_right':
                vidfmt = '3DS'
            else:
                m = self.re3D.search(self.playing_file)
                if m:
                    n = self.reTAB.search(self.playing_file)
                    if n:
                        vidfmt = "3DT"
                    else:
                        n = self.reSBS.search(self.playing_file)
                        if n:
                            vidfmt = "3DS"
                        else:
                            info("Error in 3D filename - using default settings")
                            ambibox.set_profile(scriptsettings["video_profile"])
                else:
                    vidfmt = "2D"
        else:
            vidfmt = "2D"
        return vidfmt

    def get_dimensions_for_XBMCD(self, infos):
        # If using XBMCDirect, get video dimensions, some guesswork needed for Infolabel method
        # May need to use guessed ratio other than 1.778 as 4K video becomes more prevalent
        if ((infos[0] == 0) or (infos[1] == 0)) and (mediax is not None) and not self.mi_called:
            xxx = self.getPlayingFile()
            if xxx[0:3] != 'pvr':  # Cannot use for LiveTV stream
                if xbmcvfs.exists(xxx):
                    try:
                        infos = mediax().getInfos(xxx)
                    except:
                        infos = [0, 0, 1, 0]

        # InfoLabel Method
        if (infos[0] == 0) or (infos[1] == 0):
            vp_res = xbmc.getInfoLabel("VideoPlayer.VideoResolution")
            if str(vp_res).lower() == '4k':
                vp_res_int = 2160
            else:
                try:
                    vp_res_int = int(vp_res)
                except ValueError or TypeError:
                    vp_res_int = 0
            if vp_res_int != 0 and infos[3] != 0:
                if infos[3] > 1.7778:
                    infos[0] = int(vp_res_int * 1.7778)
                    infos[1] = int(infos[0] / infos[3])
                else:
                    infos[0] = int(infos[3] * vp_res_int)
                    infos[1] = vp_res_int
        # Fallback
        if (infos[0] == 0) or (infos[1] == 0):
            infos[0] = screenx
            infos[1] = screeny

        # Set quality
        quality = scriptsettings.settings['directXBMC_quality']
        minq = 32
        maxq = infos[1]
        if quality == 0:
            infos[1] = minq
            infos[0] = int(infos[1] * infos[3])
        elif quality == 1:
            infos[1] = int(minq + ((maxq - minq) / 3))
            infos[0] = int(infos[1] * infos[3])
        elif quality == 2:
            infos[1] = int(minq + (2 * (maxq - minq) / 3))
            infos[0] = int(infos[1] * infos[3])
        else:
            if infos[3] > sar:
                if infos[1] == 0:
                    infos[1] = screeny
                infos[0] = int(infos[1] * infos[3])
            else:
                if infos[0] == 0:
                    infos[0] = screenx
                infos[1] = int(infos[0] / infos[3])
        return infos, quality

    def onPlayBackStarted(self):
        self.onPBSfired = True
        if ambibox.connect() != 0:
            return
        counter = 0
        while (not (self.isPlayingAudio() or self.isPlayingVideo())) and counter < 20:
            xbmc.sleep(500)
            counter += 1
        if self.isPlayingAudio():
            ambibox.set_profile(scriptsettings.settings["audio_enable"],
                                enable=scriptsettings.settings["audio_profile"])
        if self.isPlayingVideo():

            infos = self.get_aspect_ratio()
            vidfmt = self.get_stereo_format()

            # Switch profile

            videomode = scriptsettings.settings["video_choice"]
            if videomode == 0:  # Use Default Video Profile
                info('Using default video profile')
                ambibox.set_profile(scriptsettings.settings["video_profile"])
            elif videomode == 1:  # Autoswitch
                DAR = infos[3]
                if DAR != 0:
                    self.setprofilebydar(DAR, vidfmt)
                    info('Autoswitched on AR')
                else:
                    info("Error retrieving DAR from video file")
            elif videomode == 2:  # Show menu
                self.showmenu()
                info('Using menu for profile pick')
            elif videomode == 3:  # Turn off
                info('User set lights off for video')
                ambibox.lightSwitch(ambibox.LIGHTS_OFF)

            # XBMC Direct

            profile_is_XBMCDirect = scriptsettings.profiles.is_xbmc_direct(ambibox.current_profile)
            if profile_is_XBMCDirect is True:

                infos, quality = self.get_dimensions_for_XBMCD(infos)
              # Get other settings associated with XBMC Direct

                use_threading = scriptsettings.settings['use_threading']
                throttle = scriptsettings.settings['throttle']
                instrumented = scriptsettings.settings['instrumented']

                info('XBMCDirect throttle =  %s, qual = %s, captureX = %s, captureY = %s, thread = %s, instr = %s'
                     % (throttle, quality, infos[0], infos[1], use_threading, instrumented))

                #Start XBMC Direct
                self.run_XBMCD(infos, use_threading, instrumented, throttle)

            elif profile_is_XBMCDirect is False:
                info('XBMCDirect not started because profile not using XBMCDirect')
            elif profile_is_XBMCDirect is None:
                info('XBMCDirect not started due to an error detecting whether or not profile uses XBMCDirect')

    def onPlayBackEnded(self):
        if scriptsettings.profiles.is_xbmc_direct(ambibox.current_profile) is True:
            self.kill_XBMCDirect()
        if ambibox.connect() == 0:
            ambibox.switch_to_default_profile()
        self.onPBSfired = False

    def kill_XBMCDirect(self):
        try:
            if self.xd is not None:
                self.xd.stop()
            if self.xd is not None:
                if self.xd.is_alive() and isinstance(self.xd, XBMCDt):
                    self.xd.join(0.5)
            if self.xd is not None:
                self.xd = None
        except Exception as e:
            info('Error terminating XBMCDirect')
            if hasattr(e, 'message'):
                info(str(e.message))

    def onPlayBackStopped(self):
        self.onPlayBackEnded()

    def close(self):
        if ambibox.connect() == 0:
            ambibox.lock()
            ambibox.turnOff()
            ambibox.unlock()
            ambibox.disconnect()

    def run_XBMCD(self, infos, use_threading, instrumented, throttle=100.0):
        if use_threading:
            if self.xd is not None:
                self.kill_XBMCDirect()
            info('XBMCDirect using threading')
            try:
                p = XBMCDt(infos, instrumented=instrumented, throttle=throttle)
                p.start()
            except Exception as e:
                info('Error starting XBMC Direct threaded')
                info(str(e.message))
            else:
                self.xd = p
        else:
            info('XBMCDirect not using threading')
            self.xd = XBMCDnormal(infos, instrumented=instrumented, throttle=throttle)
            self.xd.run()

    def setprofilebydar(self, aspect_ratio, vidfmt):
        global scriptsettings, ambibox
        pfls = ambibox.get_profiles()
        arp = scriptsettings.aspect_ratio_settings[vidfmt]
        pfl = [x.profile_name for x in arp if x.lower_lmt < aspect_ratio <= x.upper_lmt]
        ret = pfl[0]
        if ret != "":
            if ret in pfls:
                ambibox.set_profile(ret)
            else:
                info("Profile in settings.xml not found by Ambibox - using default")
                ambibox.switch_to_default_profile()
        else:
            info("No profiles have been set up for this video type - using default")
            ambibox.switch_to_default_profile()


class XbmcMonitor(xbmc.Monitor):
    def __init__(self):
        super(XbmcMonitor, self).__init__()

    def onScreensaverDeactivated(self):
        global scriptsettings
        if scriptsettings.settings["disable_on_screensaver"] is True and ambibox.connect() == 0:
            ambibox.lightSwitch(ambibox.LIGHTS_ON)
            info('Screensaver stopped: LEDs on')

    def onScreensaverActivated(self):
        global scriptsettings
        if scriptsettings.settings["disable_on_screensaver"] is True and ambibox.connect() == 0:
            notification(__language__(32032), True)  # silent notification  # @[Ambibox turned off] 
            ambibox.lightSwitch(ambibox.LIGHTS_OFF)
            info('Screensaver started: LEDs off')

    def onSettingsChanged(self):
        global scriptsettings, ambibox, __settings__
        __settings__ = xbmcaddon.Addon('script.ambibox')
        scriptsettings.refresh_settings()
        if scriptsettings.settings['start_ambibox'] is True and ambibox.is_running is False:
            ambibox.start_ambiboxw()
        chk_mediainfo()
        if scriptsettings.settings['key_use']:
            kbs.process_keyboard_settings()


class XBMCDt(threading.Thread):
    # __metaclass__ = Singleton

    def __init__(self, infos, instrumented=False, throttle=100.0):
        self.worker = None
        self.infos = infos
        self.instrumented = instrumented
        self.throttle = throttle
        super(XBMCDt, self).__init__(name='XBMCDt')

    def run(self):
        info('XBMCD_threaded run event')
        self.worker = XBMCD(self.infos, XBMCD.TYPE_THREADED, self.instrumented, self.throttle)
        self.worker.run()

    def stop(self):
        self.worker.stop()
        del self.worker
        del self


class XBMCDnormal(object):
    def __init__(self, infos, instrumented=False, throttle=100.0):
        self.worker = None
        self.infos = infos
        self.instrumented = instrumented
        self.throttle = throttle

    def run(self):
        self.worker = XBMCD(self.infos, XBMCD.TYPE_STANDARD, self.instrumented, self.throttle)
        self.worker.run()

    def stop(self):
        self.worker.stop()
        del self.worker
        del self

    def is_alive(self):
        return self.worker is not None


class XBMCD(object):
    TYPE_STANDARD = 1
    TYPE_THREADED = 2

    def __init__(self, infos, runtype=TYPE_STANDARD, instrumented=False, throttle=100.0):
        self.infos = infos
        self.inDataMap = None
        self.runtype = runtype
        self.throttle = throttle
        self.instrumented = instrumented
        if runtype == self.TYPE_STANDARD:
            self.player = xbmc.Player()
        self.killswitch = False
        self.playing_file = ''
        self.capture = xbmc.RenderCapture()
        tw = self.capture.getHeight()
        th = self.capture.getWidth()
        tar = self.capture.getAspectRatio()
        self.width = self.infos[0]
        self.height = self.infos[1]
        self.ratio = self.infos[2]
        self.length = self.width * self.height * 4
        self.sfps = self.infos[4]
        if self.sfps == 0:
            self.sfps = float(xbmc.getInfoLabel('System.FPS'))
        info('Initial video framerate reported as %s' % str(self.sfps))
        self.tpf = int(1000.0 / self.sfps)
        self.sleeptime = int(0.1 * self.tpf)
        self.frame_count = 0
        self.frame_freq_to_chk_file_changed = int(self.sfps * 5.0)
        try:
            self.inDataMap = mmap.mmap(0, self.length + 11, 'AmbiBox_XBMC_SharedMemory', mmap.ACCESS_WRITE)
            if simul:
                self.inDataMap[0] = chr(248)
        except Exception, e:
            info('Error creating connection to Ambibox Windows')
            if hasattr(e, 'message'):
                info(str(e.message))
            return
        else:
            if self.inDataMap is None:
                info('Error creating connection to Ambibox Windows, no further information available')
                return

    def exit_event(self):
        if self.runtype == self.TYPE_STANDARD:
            if self.frame_count > self.frame_freq_to_chk_file_changed:
                current_file = self.player.getPlayingFile()
                if self.playing_file != current_file:
                    info('XBMCD restarting due to file change')
                    self.run()
                self.frame_count = 0
            self.frame_count += 1
            return not (self.player.isPlaying())
        elif self.runtype == self.TYPE_THREADED:
            return self.killswitch

    def stop(self):
        if self.runtype == self.TYPE_THREADED:
            self.killswitch = True

    def run(self):
        if self.instrumented:
            self.run_i()
        else:
            self.run_ni()

    def run_ni(self):
        missed_capture_count = -1  # always misses the first frame
        first_pass = True
        self.frame_count = 0
        self.capture.capture(self.width, self.height, xbmc.CAPTURE_FLAG_CONTINUOUS)
        if self.runtype == self.TYPE_STANDARD:
            self.playing_file = self.player.getPlayingFile()
        while self.exit_event() is False:
            self.capture.waitForCaptureStateChangeEvent(self.tpf)
            cgcs = self.capture.getCaptureState()
            if cgcs == xbmc.CAPTURE_STATE_DONE:
                self.copy_image_to_mmap(first_pass)
                first_pass = False
                xbmc.sleep(self.sleeptime)
                if simul:
                    self.inDataMap[0] = chr(248)
            elif cgcs == xbmc.CAPTURE_STATE_WORKING:
                missed_capture_count += 1
                continue
            elif cgcs == xbmc.CAPTURE_STATE_FAILED:
                info('XBMCDirect Capture stopped')
                if self.player.isPlaying():
                    if (self.runtype == XBMCD.TYPE_THREADED and self.killswitch is False) or self.runtype == XBMCD.TYPE_STANDARD:
                        notification(__language__(32035))  # @[XBMCDirect Fail]
                break
        del self.capture
        info('XBMCDirect capture terminated')
        if missed_capture_count != 0:
            info('XBMCDirect reports missing %s captures due to RenderCapture timeouts' % missed_capture_count)
        self.inDataMap.close()
        self.inDataMap = None

    def run_i(self):
        missed_frames = []
        missed_capture_count = -1
        first_pass = True
        self.frame_count = 0
        counter = 0
        sumtime = 0
        ctime = 0
        tfactor = self.throttle / 100.0
        evalframenum = -1
        self.capture.capture(self.width, self.height, xbmc.CAPTURE_FLAG_CONTINUOUS)
        if self.runtype == self.TYPE_STANDARD:
            self.playing_file = self.player.getPlayingFile()
        while self.exit_event() is False:
            with Timer() as t:
                self.capture.waitForCaptureStateChangeEvent(self.tpf)
                cgcs = self.capture.getCaptureState()
                if cgcs == xbmc.CAPTURE_STATE_DONE:
                    with Timer() as t2:
                        self.copy_image_to_mmap(first_pass)
                        first_pass = False
                        counter += 1
                    ctime += t2.microsecs
                    xbmc.sleep(self.sleeptime)
                elif cgcs == xbmc.CAPTURE_STATE_WORKING:
                    missed_capture_count += 1
                    if counter != 0:
                        missed_frames.append(counter)
                    continue
                elif cgcs == xbmc.CAPTURE_STATE_FAILED:
                    info('XBMCDirect Capture stopped after %s frames' % counter)
                    xbmc.sleep(250)
                    if (self.runtype == XBMCD.TYPE_THREADED and self.killswitch is False) or self.runtype == XBMCD.TYPE_STANDARD:
                        notification(__language__(32035))  # @[XBMCDirect Fail]
                    break
            sumtime += t.msecs
            if counter == 50:
                self.sfps = float(xbmc.getInfoLabel('System.FPS'))  # wait for 50 frames before updating fps
                self.tpf = int(1000.0 / self.sfps)
                evalframenum = int(self.sfps * 10.0)  # evaluate how much to sleep over first 10s of video
            if counter == evalframenum:
                dfps = self.sfps * tfactor  # calculates a desired fps based on throttle val
                self.sleeptime = int(0.95 * ((1000.0 / dfps) - (ctime / (1000.0 * counter))))  # 95% of calc sleep
                info('Over first %s frames, avg process time for render = %s microsecs'
                     % (counter, int(float(ctime) / float(counter))))
                if self.sleeptime < 10:
                    info('Capture framerate limited by limited system speed')
                    self.sleeptime = 10
                sumtime = 0
                ctime = 0
        # Exiting
        info('XBMCDirect terminating capture')
        del self.capture
        if evalframenum != -1:
            if counter > evalframenum and sumtime != 0 and counter != 0:
                counter += -evalframenum
                ptime = int(float(ctime) / float(counter))
                fps = float(counter) * 1000 / float(sumtime)
                pcnt_sleep = float(self.sleeptime) * fps * 0.1
                info('XBMCdirect captured %s frames with mean of %s fps at %s %% throttle'
                     % (counter, fps, self.throttle))
                info('XBMC System rendering speed: %s fps' % self.sfps)
                info('XBMCdirect mean processing time per frame %s microsecs' % ptime)
                info('XBMCdirect slept for %s msec per frame or slept %s %% of the time for each video frame'
                     % (self.sleeptime, pcnt_sleep))
                if missed_capture_count > 0:
                    info('XBMCDirect reports missing %s captures due to RenderCapture timeouts' % missed_capture_count)
                    info('The following frame number(s) were missed: %s' % str(missed_frames))
        self.inDataMap.close()
        self.inDataMap = None

    def copy_image_to_mmap(self, first_pass):
        image = self.capture.getImage()
        self.inDataMap.seek(0)
        seeked = self.inDataMap.read_byte()
        if ord(seeked) == 248:
            if first_pass:
                info('XBMCDirect Capture successful')
                notification(__language__(32034))
                # width
                self.inDataMap[1] = chr(self.width & 0xff)
                self.inDataMap[2] = chr((self.width >> 8) & 0xff)
                # height
                self.inDataMap[3] = (chr(self.height & 0xff))
                self.inDataMap[4] = (chr((self.height >> 8) & 0xff))
                # aspect ratio
                self.inDataMap[5] = (chr(int(self.ratio * 100)))
                # image format
                fmt = self.capture.getImageFormat()
                if fmt == 'RGBA':
                    self.inDataMap[6] = (chr(0))
                elif fmt == 'BGRA':
                    self.inDataMap[6] = (chr(1))
                else:
                    self.inDataMap[6] = (chr(2))
                # datasize
                self.inDataMap[7] = (chr(self.length & 0xff))
                self.inDataMap[8] = (chr((self.length >> 8) & 0xff))
                self.inDataMap[9] = (chr((self.length >> 16) & 0xff))
                self.inDataMap[10] = (chr((self.length >> 24) & 0xff))
            #self.inDataMap[11:(11 + self.length)] = str(image)
            self.ctype_copy_to_mmap(self.inDataMap, image)
            # write first byte to indicate we finished writing the data
            self.inDataMap[0] = (chr(240))

    def copy_to_mmap(self, inDataMap, image):
        inDataMap[11:(11 + self.length)] = str(image)

    def ctype_copy_to_mmap(self, inDataMap, image):
        T = (ctypes.c_uint8 * (self.length + 11))
        U = (ctypes.c_uint8 * self.length)
        dest = T.from_buffer(inDataMap)
        src = U.from_buffer(image)
        ctypes.memmove(ctypes.addressof(dest)+11, ctypes.addressof(src), self.length)


def simulate():
    global __language__

    def language(x):
        return 'blank'

    __language__ = language
    infos = [1920, 1080, 1, 2.4, 23.97]
    xd = XBMCDt(infos, True)
    xd.start()
    time.sleep(10)
    xd.stop()
    print 'Done'


def startup():
    global ambibox, screenx, screeny, sar, scriptsettings, kbs, xbmc_version
    user32 = ctypes.windll.user32
    screenx = user32.GetSystemMetrics(0)
    screeny = user32.GetSystemMetrics(1)
    del user32
    if screeny != 0:
        sar = float(screenx) / float(screeny)
    else:
        sar = 16.0 / 9.0
    try:
        xbmc_version = float(str(xbmc.getInfoLabel("System.BuildVersion"))[0:4])
    except ValueError:
        xbmc_version = 13.1
    chk_mediainfo()
    ambibox = XbmcAmbibox(__settings__.getSetting("host"), int(__settings__.getSetting("port")))
    if __settings__.getSetting('start_ambibox') == 'true':
        ambibox.start_ambiboxw()
    scriptsettings = ScriptSettings()
    if scriptsettings.settings['key_use']:
        kbs = KeyboardXml()
        kbs.process_keyboard_settings()


def main():
    global ambibox, scriptsettings
    info('Service Started - ver %s' % __version__)
    startup()
    player = None
    monitor = XbmcMonitor()
    chk = 13.0 <= xbmc_version < 13.11
    count = 0
    while not xbmc.abortRequested:
        if player is None:
            if ambibox.connect() == 0:
                notification(__language__(32030))  # @[Connected to AmbiBox]
                ambibox.switch_to_default_profile()
                player = CapturePlayer()
            xbmc.sleep(1000)
        else:
            # This is to get around a bug where onPlayBackStarted is not fired for external players present
            # in releases up to Gotham 13.1
            if count > 8:
                if chk is True:
                    if player.isPlayingVideo() and not player.onPBSfired:
                        info('Firing missed onPlayBackStarted event')
                        player.onPlayBackStarted()
                count = 0
            count += 1
            xbmc.sleep(250)
    if player is not None:
        player.kill_XBMCDirect()
        player.close()
        del player
        if ambibox is not None:
            ambibox.close()
            del ambibox
    del monitor
    del scriptsettings


if __name__ == '__main__':
    #start_debugger()
    if not simul:
        main()
        info('Ambibox exiting')
    else:
        simulate()