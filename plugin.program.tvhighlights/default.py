#!/usr/bin/python
###########################################################################
#
#          FILE:  plugin.program.tvhighlights/default.py
#
#        AUTHOR:  Tobias D. Oestreicher
#
#       LICENSE:  GPLv3 <http://www.gnu.org/licenses/gpl.txt>
#       VERSION:  0.0.5
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

import urllib
import urllib2
import re
import os
import xbmcgui
import xbmcaddon
import xbmcplugin

NODEBUG = True

addon               = xbmcaddon.Addon()
addonID             = addon.getAddonInfo('id')
addonFolder         = downloadScript = xbmc.translatePath('special://home/addons/'+addonID).decode('utf-8')
addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID).decode('utf-8')

addonDir   = addon.getAddonInfo("path")
XBMC_SKIN  = xbmc.getSkinDir()
icon       = os.path.join(addonFolder, "icon.png")#.encode('utf-8')
WINDOW     = xbmcgui.Window( 10000 )


SKYAvail   = False
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

TVDigitalWatchtypes = ['spielfilm', 'sport', 'serie', 'unterhaltung', 'doku-und-info', 'kinder'] 

mastermode = addon.getSetting('mastermode')
showsky    = addon.getSetting('showsky')
mastertype = addon.getSetting('mastertype')


##########################################################################################################################
##
##########################################################################################################################
def getUnicodePage(url):
    req = urllib2.urlopen(url)
    content = ""
    if "content-type" in req.headers and "charset=" in req.headers['content-type']:
        encoding=req.headers['content-type'].split('charset=')[-1]
        content = unicode(req.read(), encoding)
    else:
        content = unicode(req.read(), "utf-8")
    return content


##########################################################################################################################
##
##########################################################################################################################
def debug(content):
    if (NODEBUG):
        return
    print unicode(content).encode("utf-8")


##########################################################################################################################
##
##########################################################################################################################
def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


##########################################################################################################################
## clear Properties (mastermode)
##########################################################################################################################
def clear_tvdigital_mastermode_highlights():
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


##########################################################################################################################
## retrieve tvhighlights (mastermode)
##########################################################################################################################
def get_tvdigital_mastermode_highlights(mastertype):
    url="http://www.tvdigital.de/tv-tipps/heute/"+mastertype+"/"
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
    
##########################################################################################################################
## Clear possible existing property values. watchtype is one of spielfilm,sport,serie,unterhaltung,doku-und-info,kinder    
##########################################################################################################################
def clear_tvdigital_watchtype_highlights(watchtype):
    debug("Clear Props for "+watchtype)
    for i in range(1, 14, 1):
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Title" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Thumb" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Time" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Date" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Channel" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Icon" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Logo" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Genre" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Comment" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Year" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Duration" %(watchtype,i) )
        WINDOW.clearProperty( "TV%sHighlightsToday.%s.Extrainfos" %(watchtype,i) )



##########################################################################################################################
## Retrieve tvhighlights for a choosen watchtype. Set Home properties. 
## Possible watchtype types are spielfilm,sport,serie,unterhaltung,doku-und-info,kinder
##########################################################################################################################
def get_tvdigital_watchtype_highlights(watchtype):
    debug("Start retrive watchtype "+watchtype)
    url="http://www.tvdigital.de/tv-tipps/heute/"+watchtype+"/"
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
   
        watchtype.translate(None, '-')
 
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Title" %(watchtype,thumbNr), title )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Thumb" %(watchtype,thumbNr), thumbUrl )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Time" %(watchtype,thumbNr), time )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Date" %(watchtype,thumbNr), date )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Channel" %(watchtype,thumbNr), channel )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Icon" %(watchtype,thumbNr), thumbUrl )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Logo" %(watchtype,thumbNr), logoUrl )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Genre" %(watchtype,thumbNr), genre )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Comment" %(watchtype,thumbNr), comment )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Extrainfos" %(watchtype,thumbNr), extrainfos )
        debug("===========TIP "+watchtype+" START=============")
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
        debug("===========TIP "+watchtype+" END=============")
        thumbNr = thumbNr + 1
 


##########################################################################################################################
##########################################################################################################################
##
##                                                       M  A  I  N
##
##########################################################################################################################
##########################################################################################################################



#### OLD Should Work ####
##if type(suburl) is str:
##    url="http://www.tvdigital.de/tv-tipps/heute/"+suburl+"/"
##else:
##    url="http://www.tvdigital.de/tv-tipps/heute/spielfilm/"
##
##clearprops()
##get_single_preview(url)
#########################


##########################################################################################################################
## Get starting methode
##########################################################################################################################
debug("TVHighlights sysargv: "+str(sys.argv))
debug("TVHighlights mastermode: "+mastermode)
if len(sys.argv)>1:
    params = parameters_string_to_dict(sys.argv[1])
    methode = urllib.unquote_plus(params.get('methode', ''))
    watchtype = urllib.unquote_plus(params.get('watchtype', ''))
else:
    methode = None
    watchtype = None

#if methode==None or not (watchtype in TVDigitalWatchtypes):
#        clear_tvdigital_watchtype_highlights('spielfilm')
#        get_tvdigital_watchtype_highlights('spielfilm')


if methode=='mastermode':
        debug("Mastermode Retrieve")
        clear_tvdigital_mastermode_highlights()
        get_tvdigital_mastermode_highlights(watchtype)
 
elif methode=='getall_tvdigital':
        debug("Get All Highlights")
        for singlewatchtype in TVDigitalWatchtypes:
            clear_tvdigital_watchtype_highlights(singlewatchtype)
            get_tvdigital_watchtype_highlights(singlewatchtype)

elif methode=='get_single_tvdigital':
        debug("Single Methode Retrieve for "+watchtype)
        if watchtype in TVDigitalWatchtypes:
            clear_tvdigital_watchtype_highlights(watchtype)
            get_tvdigital_watchtype_highlights(watchtype)

elif methode=='settings' or methode==None or not (watchtype in TVDigitalWatchtypes):
        debug("Settings Methode Retrieve")
        if mastermode=='true':
            clear_tvdigital_mastermode_highlights()
            get_tvdigital_mastermode_highlights(mastertype)
        else:
            setting_spielfilm  = addon.getSetting('setting_spielfilm')
            setting_sport  = addon.getSetting('setting_sport')
            setting_unterhaltung  = addon.getSetting('setting_unterhaltung')
            setting_serie  = addon.getSetting('setting_serie')
            setting_kinder  = addon.getSetting('setting_kinder')
            setting_doku  = addon.getSetting('setting_doku')
            debug("setting_spielfilm"+setting_spielfilm)
            debug("setting_sport"+setting_sport)
            debug("setting_unterhaltung"+setting_unterhaltung)
            debug("setting_serie"+setting_serie)
            debug("setting_kinder"+setting_kinder)
            debug("setting_doku"+setting_doku)
            if setting_spielfilm=='true':
                clear_tvdigital_watchtype_highlights('spielfilm')
                get_tvdigital_watchtype_highlights('spielfilm')
            if setting_serie=='true':
                clear_tvdigital_watchtype_highlights('serie')
                get_tvdigital_watchtype_highlights('serie')
            if setting_doku=='true':
                clear_tvdigital_watchtype_highlights('doku-und-info')
                get_tvdigital_watchtype_highlights('doku-und-info')
            if setting_unterhaltung=='true':
                clear_tvdigital_watchtype_highlights('unterhaltung')
                get_tvdigital_watchtype_highlights('unterhaltung')
            if setting_kinder=='true':
                clear_tvdigital_watchtype_highlights('kinder')
                get_tvdigital_watchtype_highlights('kinder')
            if setting_sport=='true':
                clear_tvdigital_watchtype_highlights('sport')
                get_tvdigital_watchtype_highlights('sport')
    
    
