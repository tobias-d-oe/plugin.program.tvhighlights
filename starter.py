#!/usr/bin/python
###########################################################################
#
#          FILE:  plugin.program.tvhighlights/starter.py
#
#        AUTHOR:  Tobias D. Oestreicher
#
#       LICENSE:  GPLv3 <http://www.gnu.org/licenses/gpl.txt>
#       VERSION:  0.1.5
#       CREATED:  05.02.2016
#
###########################################################################
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <http://www.gnu.org/licenses/>.
#
###########################################################################
#     CHANGELOG:  (02.09.2015) TDOe - First Publishing
###########################################################################

import os,sys,time,re,xbmc,xbmcgui,xbmcaddon

__addon__ = xbmcaddon.Addon()
__addonID__ = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__path__ = __addon__.getAddonInfo('path')
__LS__ = __addon__.getLocalizedString
__icon__ = xbmc.translatePath(os.path.join(__path__, 'icon.png'))

OSD = xbmcgui.Dialog()

# Helpers #

def notifyOSD(header, message, icon=xbmcgui.NOTIFICATION_INFO, disp=4000, enabled=True):
    if enabled:
        OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon, disp)

def writeLog(message, level=xbmc.LOGNOTICE):
        xbmc.log('[%s %s]: %s' % (__addonID__, __version__,  message.encode('utf-8')), level)

# End Helpers #

_mdelay = int(re.match('\d+', __addon__.getSetting('mdelay')).group())
_screenrefresh = int(re.match('\d+', __addon__.getSetting('screenrefresh')).group())

writeLog('Content refresh: %s mins, screen refresh: %s mins' % (_mdelay, _screenrefresh), level=xbmc.LOGDEBUG)

if _mdelay == 0:
    writeLog('Don\'t start Service, content refresh is 0', level=xbmc.LOGERROR)
    sys.exit()

if _screenrefresh >= _mdelay:
    notifyOSD(__LS__(30010), __LS__(30130), icon=__icon__, disp=10000)
    writeLog('Don\'t start Service, content refresh is lower than screen refresh', level=xbmc.LOGERROR)
    sys.exit()

class MyMonitor(xbmc.Monitor):
    def __init__(self, *args, **kwargs ):
        xbmc.Monitor.__init__(self)
        self.settingsChanged = False

    def onSettingsChanged( self ):
        self.settingsChanged = True

class Starter():

    def __init__(self):
        self.mastermode = None
        self.enableinfo = None
        self.showtimeframe = None
        self.mdelay = 0
        self.screenrefresh = 0

    def getSettings(self):
        self.mastermode = True if __addon__.getSetting('mastermode').upper() == 'TRUE' else False
        self.enableinfo = True if __addon__.getSetting('enableinfo').upper() == 'TRUE' else False
        self.showtimeframe = True if __addon__.getSetting('showtimeframe').upper() == 'TRUE' else False
        self.mdelay = int(re.match('\d+', __addon__.getSetting('mdelay')).group()) * 60
        self.screenrefresh = int(re.match('\d+', __addon__.getSetting('screenrefresh')).group()) * 60
        self.refreshcontent = self.mdelay/self.screenrefresh

        writeLog('Settings (re)loaded')
        writeLog('Mastermode:               %s' % (self.mastermode))
        writeLog('Show notifications:       %s' % (self.enableinfo))
        writeLog('Show timeframe:           %s' % (self.showtimeframe))
        writeLog('Refresh interval content: %s secs' % (self.mdelay))
        writeLog('Refresh interval screen:  %s secs' % (self.screenrefresh))
        writeLog('Refreshing content ratio: %s' % (self.refreshcontent))

        xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=get_mode")')

        if self.mastermode:
            xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=get_master_elements")')
        else:
            xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=get_split_elements")')

        xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=settings")')

    def start(self):
        writeLog('Starting %s V.%s' % (__addonname__, __version__))
        notifyOSD(__LS__(30010), __LS__(30106), __icon__, enabled=self.enableinfo)
        self.getSettings()

        ## Thoughts: refresh = 5m; refresh-content=120 => i-max=120/5;

        counter = 0
        monitor = MyMonitor()
        while not monitor.abortRequested():
            if monitor.settingsChanged:
                self.getSettings()
                monitor.settingsChanged = False
            if monitor.waitForAbort(self.screenrefresh):
                break
            counter += 1
            if counter >= self.refreshcontent:
                writeLog('Refreshing TVHighlights @%s' % time.time(), level=xbmc.LOGDEBUG)
                notifyOSD(__LS__(30010), __LS__(30018), __icon__, enabled=self.enableinfo)
                xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=settings")')
                counter = 0
            else:
                notifyOSD(__LS__(30010), __LS__(30108), __icon__, enabled=self.enableinfo)
                if not self.showtimeframe:
                    if self.mastermode:
                        writeLog('Refresh content on home screen in mastermode')
                        xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=refresh_mastermode")')
                    else:
                        writeLog('Refresh content on home screen in splitmode')
                        xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=refresh_splitmode")')

if __name__ == '__main__':
    starter = Starter()
    starter.start()
    del starter

