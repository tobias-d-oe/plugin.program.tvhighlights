#!/usr/bin/python
###########################################################################
#
#          FILE:  plugin.program.tvhighlights/default.py
#
#        AUTHOR:  Tobias D. Oestreicher
#
#       LICENSE:  GPLv3 <http://www.gnu.org/licenses/gpl.txt>
#       VERSION:  0.0.4
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

import urllib2
import re
import os
import xbmcgui
import xbmcaddon
import xbmcplugin

addon = xbmcaddon.Addon()
addonID = addon.getAddonInfo('id')
addonFolder = downloadScript = xbmc.translatePath('special://home/addons/'+addonID).decode('utf-8')
addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID).decode('utf-8')

addonDir = addon.getAddonInfo("path")
XBMC_SKIN  = xbmc.getSkinDir()

NODEBUG = True

SKYAvail = False
SKYChannel = [ 'Sky Action', 'Sky Cinema', 'Sky Cinema +1', 'Sky Cinema +24', 'Sky Hits',
               'Sky Atlantic HD', 'Sky Comedy', 'Sky Nostalgie', 'Sky Emotion', 'Sky Krimi',
               'Sky 3D', 'MGM', 'Disney Cinemagic', 'Sky Bundesliga', 'Sky Sport HD 1',
               'Sky Sport HD 2', 'Sky Sport Austria', 'Sky Sport News HD', 'SPORT1+', 'Sport1 US',
               'sportdigital', 'Motorvision TV', 'Discovery Channel', 'National Geographic Channel',
               'Nat Geo Wild', 'Planet', 'History HD', 'A und E', 'Spiegel Geschichte',
               'Spiegel TV Wissen', '13TH STREET', 'Syfy', 'FOX', 'Universal Channel', 'TNT Serie',
               'TNT Film', 'Kinowelt TV', 'kabel eins classics', 'Silverline', 'AXN', 'RTL Crime',
               'Sat.1 Emotions', 'Romance TV', 'Passion', 'ProSieben Fun', 'TNT Glitz', 'RTL Living',
               'E! Entertainment', 'Heimatkanal', 'GoldStar TV', 'Beate-Uhse.TV', 'Junior',
               'Disney Junior', 'Disney XD', 'Cartoon Network', 'Boomerang', 'Animax', 'Classica',
               'MTV Live HD', 'MTV HD'
             ]





showsky=addon.getSetting('showsky')
suburl=addon.getSetting('suburl')
if type(suburl) is str:
    url="http://www.tvdigital.de/tv-tipps/heute/"+suburl+"/"
else:
    url="http://www.tvdigital.de/tv-tipps/heute/spielfilm/"


def getUnicodePage(url):
    req = urllib2.urlopen(url)
    content = ""
    if "content-type" in req.headers and "charset=" in req.headers['content-type']:
        encoding=req.headers['content-type'].split('charset=')[-1]
        content = unicode(req.read(), encoding)
    else:
        content = unicode(req.read(), "utf-8")
    return content


def debug(content):
    if (NODEBUG):
        return
    print unicode(content).encode("utf-8")


def clearprops():
    for i in range(1, 14, 1):
        WINDOW.clearProperty( "TVHighlightsToday.%s.Title" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Thumb" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Time" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Date" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Channel" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Icon" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Logo" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Genre" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Comment" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Year" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Duration" %(i) )
        WINDOW.clearProperty( "TVHighlightsToday.%s.Extrainfos" %(i) )


icon = os.path.join(addonFolder, "icon.png")#.encode('utf-8')

WINDOW = xbmcgui.Window( 10000 )



clearprops()

content = getUnicodePage(url)
content = content.replace("\\","")
spl = content.split('class="highlight-container"')
max = 10
thumbNr = 1
for i in range(1, len(spl), 1):
    if thumbNr > max:
        break

    entry = spl[i]

    channel = re.compile('/programm/" title="(.+?) Programm"', re.DOTALL).findall(entry)[0]
    if showsky != "true":
        debug("Sky not selected, throw away paytv channel")
        if channel in SKYChannel:
            debug("Throw away channel %s. Its PayTV" %(channel))
            continue
    else:
        debug("Sky is selected. No filtering")

    thumbs = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
    thumbUrl=thumbs[0]
    logoUrl=thumbs[1]
    if len(re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry))>0:
        title = re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry)[0]
    else:
        title = re.compile('<h2 class="highlight-title">(.+?)</h2>', re.DOTALL).findall(entry)[0]
    date = re.compile('highlight-date">(.+?) | </div>', re.DOTALL).findall(entry)[0]
    time = re.compile('highlight-time">(.+?)</div>', re.DOTALL).findall(entry)[0]
    descs = re.compile('<strong>(.+?)</strong>', re.DOTALL).findall(entry)
    extrainfos = descs[0]
    if len(descs) == 2:
        comment = descs[1]
    else:
        comment = ""
    genre = re.compile('(.+?) | ', re.DOTALL).findall(extrainfos)

    extrainfos2 = extrainfos.split('|')
    genre = extrainfos2[0]

    WINDOW.setProperty( "TVHighlightsToday.%s.Title" %(thumbNr), title )
    WINDOW.setProperty( "TVHighlightsToday.%s.Thumb" %(thumbNr), thumbUrl )
    WINDOW.setProperty( "TVHighlightsToday.%s.Time" %(thumbNr), time )
    WINDOW.setProperty( "TVHighlightsToday.%s.Date" %(thumbNr), date )
    WINDOW.setProperty( "TVHighlightsToday.%s.Channel" %(thumbNr), channel )
    WINDOW.setProperty( "TVHighlightsToday.%s.Icon" %(thumbNr), thumbUrl )
    WINDOW.setProperty( "TVHighlightsToday.%s.Logo" %(thumbNr), logoUrl )
    WINDOW.setProperty( "TVHighlightsToday.%s.Genre" %(thumbNr), genre )
    WINDOW.setProperty( "TVHighlightsToday.%s.Comment" %(thumbNr), comment )
    WINDOW.setProperty( "TVHighlightsToday.%s.Extrainfos" %(thumbNr), extrainfos )
    debug("===========TIP START=============")
    debug("Title "+title)
    debug("Thumb "+thumbUrl)
    debug("Time "+time)
    debug("Date "+date)
    debug("Channel "+channel)
    debug("Icon "+thumbUrl)
    debug("Logo "+logoUrl)
    debug("Genre "+genre)
    debug("Comment "+comment)
    debug("Extrainfos "+extrainfos)
    debug("===========TIP END=============")
    thumbNr = thumbNr + 1


