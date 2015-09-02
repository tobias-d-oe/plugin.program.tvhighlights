#!/usr/bin/python
###########################################################################
#
#          FILE:  plugin.program.tvhighlights/starter.py
#
#        AUTHOR:  Tobias D. Oestreicher
#
#       LICENSE:  GPLv3 <http://www.gnu.org/licenses/gpl.txt>
#       VERSION:  0.0.2
#       CREATED:  02.09.2015
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
mdelay = 14400 # 4h

xbmc.executebuiltin('XBMC.Notification(TV Highlights, Dienst gestartet ,4000,'+icon+')')

while True:
    xbmc.executebuiltin('XBMC.RunAddon(plugin.program.tvhighlights)')
    time.sleep(mdelay)

