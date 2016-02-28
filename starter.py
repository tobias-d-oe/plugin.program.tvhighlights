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

import os,sys,time,xbmc,xbmcgui,xbmcaddon

icon = xbmc.translatePath("special://home/addons/plugin.program.tvhighlights/icon.png")
#mdelay = 14400 # 4h
#mdelay = 120 # 2m
mdelay = 0
mdelay2 = 0

addon       = xbmcaddon.Addon()
enableinfo  = addon.getSetting('enableinfo')
translation = addon.getLocalizedString
notifyheader= str(translation(30010))
notifytxt   = str(translation(30106))
screenrefresh = int(addon.getSetting('screenrefresh'))
refreshcontent = int(addon.getSetting('mdelay'))/int(screenrefresh)

xbmc.log("TV Highlights Grabber - TV Digital: Contentrefresh (%s), Screenrefresh (%s)" % (addon.getSetting('mdelay'),addon.getSetting('screenrefresh')))

if int(addon.getSetting('mdelay')) == 0:
    xbmc.log("Do not start TV Highlights Service, content refresh is 0")
    sys.exit()

if int(addon.getSetting('screenrefresh')) >= int(addon.getSetting('mdelay')):
    xbmc.executebuiltin('XBMC.Notification('+notifyheader+', "Contentrefresh has to be higher than Screenrefresh. (Recommended 120/5)" ,10000,'+icon+')')
    xbmc.log("Do not start TV Highlights Service, content refresh (%s) is lower than screen refresh (%s)" % (refreshcontent,screenrefresh))
    sys.exit()



class MyMonitor( xbmc.Monitor ):
    def __init__( self, *args, **kwargs ):
        xbmc.Monitor.__init__( self )

    def onSettingsChanged( self ):
        settings_initialize()





def settings_initialize():
    global mdelay
    global mdelay2
    mdelay = int(addon.getSetting('mdelay'))*int("60")
    xbmc.log("TVHighlights: mdelay from settings=%s" % (mdelay))
    mdelay2 = int(screenrefresh)*int("60")
    xbmc.log("Refresh Interval content: %s" % (mdelay))
    xbmc.log("Refresh Interval screen : %s" % (mdelay2))
    xbmc.log("Refresh screen : %s" % (screenrefresh))
    xbmc.log("Refresh content : %s" % (refreshcontent))
    xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=get_mode")')
    if addon.getSetting('mastermode') == 'true':
        xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=get_master_elements")')
    else:
        xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=get_split_elements")')
    xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=settings")')    





xbmc.log("Start TV Highlights Service")
if enableinfo == 'true':
    xbmc.executebuiltin('XBMC.Notification('+notifyheader+', '+notifytxt+' ,4000,'+icon+')')

settings_initialize()


## Thoughts: refresh = 5m; refresh-content=120 => i-max=120/5;
counter = 0

if __name__ == '__main__':
    monitor = MyMonitor()
    while not monitor.abortRequested():
        # Sleep/wait for abort for $mdelay seconds
        #if monitor.waitForAbort(float(mdelay)):
        if monitor.waitForAbort(float(mdelay2)):
            # Abort was requested while waiting. We should exit
            break
        counter+=1
        if int(counter) == int(refreshcontent):
            xbmc.log("Refreshing TVHighlights! %s" % time.time(), level=xbmc.LOGDEBUG)
            if enableinfo == 'true':
                notifytxt = str(translation(30108))
                xbmc.executebuiltin('XBMC.Notification('+notifyheader+', '+notifytxt+' ,4000,'+icon+')')
            xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=settings")')
            counter = 0
        else:
            if enableinfo == 'true':
                notifytxt = str(translation(30108))
                xbmc.executebuiltin('XBMC.Notification('+notifyheader+', "Refresh Screen" ,4000,'+icon+')')

            if addon.getSetting('showtimeframe') == 'false':
                xbmc.log("TV Highlights doing contentrefresh on home screen")
                if addon.getSetting('mastermode') == 'true':
                    xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=refresh_mastermode")')
                else:
                    xbmc.executebuiltin('XBMC.RunScript(plugin.program.tvhighlights,"?methode=refresh_splitmode")')

