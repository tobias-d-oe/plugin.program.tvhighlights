#!/usr/bin/python
###########################################################################
#
#          FILE:  plugin.program.tvhighlights/default.py
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

import urllib
import urllib2
import re
import os
import xbmcgui
import xbmcaddon
import time
import datetime
import json

import starter

NODEBUG = True

__addon__ = xbmcaddon.Addon()
__addonID__ = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__path__ = __addon__.getAddonInfo('path')
__LS__ = __addon__.getLocalizedString
__icon__ = xbmc.translatePath(os.path.join(__path__, 'icon.png'))

WINDOW     = xbmcgui.Window( 10000 )

ChannelTranslateFile = xbmc.translatePath(os.path.join('special://home/addons', __addonID__, 'ChannelTranslate.json'))
with open(ChannelTranslateFile, 'r') as transfile:
    ChannelTranslate=transfile.read().rstrip('\n')

TVDigitalWatchtypes = ['spielfilm', 'sport', 'serie', 'unterhaltung', 'doku-und-info', 'kinder'] 

mastermode    = __addon__.getSetting('mastermode')
mastertype    = __addon__.getSetting('mastertype')
showtimeframe = __addon__.getSetting('showtimeframe')

##########################################################################################################################
##
##########################################################################################################################
def getUnicodePage(url, container, split=True):
    req = urllib2.urlopen(url)
    encoding = 'utf-8'
    if "content-type" in req.headers and "charset=" in req.headers['content-type']:
        encoding=req.headers['content-type'].split('charset=')[-1]
    content = unicode(req.read(), encoding).replace("\\", "")
    if split: return content.split(container)
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
## convert date-time string to timestamp with workaround python bug (http://bugs.python.org/issue7980) # Thanks to BJ1
##########################################################################################################################
def date2timeStamp(date, format):
    debug("Date date2timeStamp : %s" % (date))
    debug("Format date2timeStamp : %s" % (format))
    try:
        dtime = datetime.datetime.strptime(date, format)
    except TypeError:
        try:
            dtime = datetime.datetime.fromtimestamp(time.mktime(time.strptime(date, format)))
        except ValueError:
            return False
    except Exception:
        return False
    return int(time.mktime(dtime.timetuple()))



##########################################################################################################################
## get pvr channel-id
##########################################################################################################################
def channelName2channelId(channelname):
    query = {
            "jsonrpc": "2.0",
            "method": "PVR.GetChannels",
            "params": {"channelgroupid": "alltv"},
            "id": 1
            }
    res = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))

    # translate via json if necessary
    trans = json.loads(str(ChannelTranslate))
    for tr in trans:
        if channelname == tr['name']:
            debug("Translating %s to %s" % (channelname,tr['pvrname']))
            channelname = tr['pvrname']
    
    if 'result' in res and 'channels' in res['result']:
        res = res['result'].get('channels')
        for channels in res:

            # priorize HD Channel
            if channelname+" HD".lower() in channels['label'].lower(): 
                debug("TVHighlights found  HD priorized channel %s" % (channels['label']))
                return channels['channelid']
            if channelname.lower() in channels['label'].lower(): 
                debug("TVHighlights found  channel %s" % (channels['label']))
                return channels['channelid']
    return 0

##########################################################################################################################
## get pvr channelname by id
##########################################################################################################################
def pvrchannelid2channelname(channelid):
    query = {
            "jsonrpc": "2.0",
            "method": "PVR.GetChannels",
            "params": {"channelgroupid": "alltv"},
            "id": 1
            }
    res = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))
    if 'result' in res and 'channels' in res['result']:
        res = res['result'].get('channels')
        for channels in res:
            if channels['channelid'] == channelid:
                debug("TVHighlights found id for channel %s" % (channels['label']))
                return channels['label']
    return 0

##########################################################################################################################
## get pvr channel logo url
##########################################################################################################################
def pvrchannelid2logo(channelid):
    query = {
            "jsonrpc": "2.0",
            "method": "PVR.GetChannelDetails",
            "params": {"channelid": channelid, "properties": ["thumbnail"]},
            "id": 1
            }
    res = json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))
    if 'result' in res and 'channeldetails' in res['result'] and 'thumbnail' in res['result']['channeldetails']:
        return res['result']['channeldetails']['thumbnail']
    else:
        return 0

properties = ['Title', 'Thumb', 'Time', 'Date', 'Channel', 'PVRID', 'Icon', 'Logo', 'Genre', 'Comment', 'Year', 'Duration', 'Extrainfos', 'WatchType']

def clearProperties(start, watchtype):
    for i in range(start, 14, 1):
        for property in properties:
            WINDOW.clearProperty( "TV%sHighlightsToday.%s.%s" %(watchtype, i, property))

##########################################################################################################################
## refresh content timebased in splitmode -  watchtype is one of spielfilm,sport,serie,unterhaltung,doku-und-info,kinder
##########################################################################################################################
def refresh_tvdigital_splitmode_highlights(watchtype):
    highlights = '['
    json_data = json.loads( '{}' )
    # read Properties from Home Screen
    for i in range(1, 14, 1):
        blub = WINDOW.getProperty("TV%sHighlightsToday.%s.Title" %(watchtype,i)).decode("utf8").rstrip()
        debug("TV Highlights Refresh Home Screen %s" % (i))
        debug("TV Highlights Refresh Home Screen %s" % (blub))
        entry     = "{ \"id\": \"%s\", \"title\": \"%s\", \"thumb\": \"%s\", \"time\": \"%s\", \"date\": \"%s\", \"channel\": \"%s\", \"pvrid\": \"%s\", \"icon\": \"%s\", \"logo\": \"%s\", \"genre\": \"%s\", \"comment\": \"%s\", \"year\": \"%s\", \"duration\": \"%s\", \"extrainfos\": \"%s\", \"watchtype\": \"%s\" }" % (i, WINDOW.getProperty("TV%sHighlightsToday.%s.Title" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.Thumb" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.Time" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.Date" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.Channel" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.PVRID" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.Icon" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.Logo" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.Genre" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.Comment" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.Year" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.Duration" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.Extrainfos" %(watchtype,i)).decode("utf8").rstrip(), WINDOW.getProperty("TV%sHighlightsToday.%s.WatchType" %(watchtype,i)).decode("utf8").rstrip()) 

        debug("TV Highlights Refresh Home Screen %s" % (entry))
        json_object = json.loads(entry)
        if len(highlights) > 2:
            highlights = "%s, %s" % (highlights,entry)
        else:
            highlights = "%s %s" % (highlights,entry)

    highlights = "%s ]" % (highlights)
    debug("TV Highlights: highlights= %s" % (highlights))
    json_object = json.loads(highlights)
    i = 1
    for jd in json_object:
        debug("Processing title: %s in watchtype %s" % (jd["title"],watchtype))

        if len(jd["time"]) < 4:
            debug('TV Highlights: Empty Time...')
            continue
        else:
            debug("Highlightstime: %s" % (jd["time"]))
        now = datetime.datetime.now()
        htsstr = '%s %s %s %s:00' % (now.year, now.month, now.day, jd["time"])
        hts = date2timeStamp(htsstr, "%Y %m %d %H:%M:%S")

        curts = time.time()
        if int(hts) < int(curts):
            debug('Remove outdated entry')
            continue
        else:
            debug("Highlighttime is in future: %s - %s" % (hts, curts))
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Title" %(watchtype,i), jd["title"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Thumb" %(watchtype,i), jd["thumb"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Time" %(watchtype,i), jd["time"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Date" %(watchtype,i), jd["date"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Channel" %(watchtype,i), jd["channel"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.PVRID" %(watchtype,i), jd["pvrid"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Icon" %(watchtype,i), jd["icon"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Logo" %(watchtype,i), jd["logo"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Genre" %(watchtype,i), jd["genre"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Comment" %(watchtype,i), jd["comment"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Year" %(watchtype,i), jd["year"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Duration" %(watchtype,i), jd["duration"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Extrainfos" %(watchtype,i), jd["extrainfos"] )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.WatchType" %(watchtype,i), jd["watchtype"] )
        i+=1

    clearProperties(i, watchtype)

##########################################################################################################################
## refresh content timebased in mastermode
##########################################################################################################################
def refresh_tvdigital_mastermode_highlights():
    highlights = '['
    json_data = json.loads( '{}' )
    # read Properties from Home Screen
    for i in range(1, 14, 1):
        blub = WINDOW.getProperty("TVHighlightsToday.%s.Title" %(i)).decode("utf8").rstrip()
        debug("TV Highlights Refresh Home Screen %s" % (i))
        debug("TV Highlights Refresh Home Screen %s" % (blub))
        entry     = "{ \"id\": \"%s\", \"title\": \"%s\", \"thumb\": \"%s\", \"time\": \"%s\", \"date\": \"%s\", \"channel\": \"%s\", \"pvrid\": \"%s\", \"icon\": \"%s\", \"logo\": \"%s\", \"genre\": \"%s\", \"comment\": \"%s\", \"year\": \"%s\", \"duration\": \"%s\", \"extrainfos\": \"%s\", \"watchtype\": \"%s\" }" % (i, WINDOW.getProperty("TVHighlightsToday.%s.Title" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.Thumb" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.Time" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.Date" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.Channel" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.PVRID" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.Icon" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.Logo" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.Genre" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.Comment" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.Year" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.Duration" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.Extrainfos" %(i)).decode("utf8").rstrip(), WINDOW.getProperty("TVHighlightsToday.%s.WatchType" %(i)).decode("utf8").rstrip()) 

        debug("TV Highlights Refresh Home Screen %s" % (entry))
        json_object = json.loads(entry) 
        # xbmc.log("TV Highlights Entry=%s" % (json_object))
        if len(highlights) > 2:
            highlights = "%s, %s" % (highlights,entry)
        else:
            highlights = "%s %s" % (highlights,entry)

    highlights = "%s ]" % (highlights)
    debug("TV Highlights: highlights= %s" % (highlights))
    json_object = json.loads(highlights)
    i = 1
    for jd in json_object:
        debug("Processing title: %s" % (jd["title"]))

        if len(jd["time"]) < 4:
            debug('TV Highlights: Empty Time...')
            continue
        else:
            debug("Highlightstime: %s" % (jd["time"]))
        now = datetime.datetime.now()
        htsstr = '%s %s %s %s:00' % (now.year, now.month, now.day, jd["time"])
        hts = date2timeStamp(htsstr, "%Y %m %d %H:%M:%S")

        curts = time.time()
        if int(hts) < int(curts):
            debug('Remove outdated entry')
            continue
        else:
            debug("Highlighttime is in future: %s - %s" % (hts, curts))
        WINDOW.setProperty( "TVHighlightsToday.%s.Title" %(i), jd["title"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.Thumb" %(i), jd["thumb"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.Time" %(i), jd["time"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.Date" %(i), jd["date"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.Channel" %(i), jd["channel"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.PVRID" %(i), jd["pvrid"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.Icon" %(i), jd["icon"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.Logo" %(i), jd["logo"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.Genre" %(i), jd["genre"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.Comment" %(i), jd["comment"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.Year" %(i), jd["year"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.Duration" %(i), jd["duration"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.Extrainfos" %(i), jd["extrainfos"] )
        WINDOW.setProperty( "TVHighlightsToday.%s.WatchType" %(i), jd["watchtype"] )
        i+=1

    clearProperties(i, '')

##########################################################################################################################
## clear Properties (mastermode)
##########################################################################################################################
def clear_tvdigital_mastermode_highlights():
    clearProperties(1, '')
##########################################################################################################################
## retrieve tvhighlights (mastermode)
##########################################################################################################################
def get_tvdigital_mastermode_highlights(mastertype):
    url="http://www.tvdigital.de/tv-tipps/heute/"+mastertype+"/"
    spl = getUnicodePage(url, 'class="highlight-container"')
    debug("TestTest %s" % (len(spl)))
    max = 10
    thumbNr = 1
    for i in range(1, len(spl), 1):
        if thumbNr > max:
            break
        entry = spl[i]
        channel = re.compile('/programm/" title="(.+?) Programm"', re.DOTALL).findall(entry)[0]
        thumbs = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumbUrl=thumbs[0]
        logoUrl=thumbs[1]
        if len(re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry))>0:
            title = re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry)[0]
        else:
            title = re.compile('<h2 class="highlight-title">(.+?)</h2>', re.DOTALL).findall(entry)[0]
        detailurl = re.compile('<a class="highlight-title(.+?)<h2>', re.DOTALL).findall(entry)[0]
        detailurl = re.compile('href="(.+?)"', re.DOTALL).findall(detailurl)[0]
        date = re.compile('highlight-date">(.+?) | </div>', re.DOTALL).findall(entry)[0]
        highlighttime = re.compile('highlight-time">(.+?)</div>', re.DOTALL).findall(entry)[0]
        descs = re.compile('<strong>(.+?)</strong>', re.DOTALL).findall(entry)
        extrainfos = descs[0]
        if len(descs) == 2:
            comment = descs[1]
        else:
            comment = ""
        genre = re.compile('(.+?) | ', re.DOTALL).findall(extrainfos)
    
        extrainfos2 = extrainfos.split('|')
        genre = extrainfos2[0]
   
        debug("===========TESTTIP START=============")
        debug("Title "+title)
        debug("Thumb "+thumbUrl)
        debug("Time "+highlighttime)
        debug("Date "+date)
        debug("Channel "+channel)
        debug("Icon "+thumbUrl)
        debug("Genre "+genre)
        debug("Comment "+comment)
        debug("Extrainfos "+extrainfos)
        debug("Detailurl "+detailurl)
        debug("WatchType "+mastertype)
        debug("===========TESTTIP END=============")

        if showtimeframe == "false":
            debug("TVHighlights: Show only upcoming events")
            refreshtimestamp = int(time.time())
            now = datetime.datetime.now()
            highlightstimestampstr = '%s-%s-%s %s:00' % (now.year, now.month, now.day, highlighttime)
            highlightstimestampstr = highlightstimestampstr.replace('-', ' ')
            highlightstimestamp = date2timeStamp(highlightstimestampstr, "%Y %m %d %H:%M:%S")
            if (highlightstimestamp <= refreshtimestamp):
                debug("TVHighlights: Throw away entry, its in the past")
                continue
        channelexist = channelName2channelId(channel)
        debug("TVHighlights: Channel-Exists %s" % (channelexist))
        if (channelexist == 0):
            debug("TVHighlights: Channel %s not in PVR" % (channel))
            continue
        else:
            channelpvrid = channelexist
            debug("TVHighlights: Found Channel %s in PVR %s" % (channel,channelpvrid))
            logoUrl = str(pvrchannelid2logo(channelpvrid))
            channel = pvrchannelid2channelname(channelpvrid)
    
        debug("TVHighlights: %s" % (channelName2channelId(channel)))

        debug("===========TIP START=============")
        debug("Title "+title)
        debug("Thumb "+thumbUrl)
        debug("Time "+highlighttime)
        debug("Date "+date)
        debug("Channel "+channel)
        debug("PVR-Channel %s" % (channelpvrid))
        debug("Icon "+thumbUrl)
        debug("Logo "+logoUrl)
        debug("Genre "+genre)
        debug("Comment "+comment)
        debug("Extrainfos "+extrainfos)
        debug("Detailurl "+detailurl)
        debug("WatchType "+mastertype)
        debug("===========TIP END=============")

        WINDOW.setProperty( "TVHighlightsToday.%s.Title" %(thumbNr), title )
        WINDOW.setProperty( "TVHighlightsToday.%s.PVRID" %(thumbNr), str(channelpvrid) )
        WINDOW.setProperty( "TVHighlightsToday.%s.Thumb" %(thumbNr), thumbUrl )
        WINDOW.setProperty( "TVHighlightsToday.%s.Time" %(thumbNr), highlighttime )
        WINDOW.setProperty( "TVHighlightsToday.%s.Date" %(thumbNr), date )
        WINDOW.setProperty( "TVHighlightsToday.%s.Channel" %(thumbNr), channel )
        WINDOW.setProperty( "TVHighlightsToday.%s.Icon" %(thumbNr), thumbUrl )
        WINDOW.setProperty( "TVHighlightsToday.%s.Logo" %(thumbNr), logoUrl )
        WINDOW.setProperty( "TVHighlightsToday.%s.Genre" %(thumbNr), genre )
        WINDOW.setProperty( "TVHighlightsToday.%s.Comment" %(thumbNr), comment )
        WINDOW.setProperty( "TVHighlightsToday.%s.Extrainfos" %(thumbNr), extrainfos )
        WINDOW.setProperty( "TVHighlightsToday.%s.Popup" %(thumbNr), detailurl)
        WINDOW.setProperty( "TVHighlightsToday.%s.WatchType" %(thumbNr), mastertype)

        thumbNr = thumbNr + 1
    
##########################################################################################################################
## Clear possible existing property values. watchtype is one of spielfilm,sport,serie,unterhaltung,doku-und-info,kinder    
##########################################################################################################################
def clear_tvdigital_watchtype_highlights(watchtype):
    debug("Clear Props for "+watchtype)
    clearProperties(1, watchtype)

##########################################################################################################################
## Retrieve tvhighlights for a choosen watchtype. Set Home properties. 
## Possible watchtype types are spielfilm,sport,serie,unterhaltung,doku-und-info,kinder
##########################################################################################################################
def get_tvdigital_watchtype_highlights(watchtype):
    debug("Start retrive watchtype "+watchtype)
    url="http://www.tvdigital.de/tv-tipps/heute/"+watchtype+"/"
    spl = getUnicodePage(url, 'class="highlight-container"')
    max = 10
    thumbNr = 1
    for i in range(1, len(spl), 1):
        if thumbNr > max:
            break
        entry = spl[i]
        channel = re.compile('/programm/" title="(.+?) Programm"', re.DOTALL).findall(entry)[0]
        thumbs = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumbUrl=thumbs[0]
        logoUrl=thumbs[1]
        if len(re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry))>0:
            title = re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry)[0]
        else:
            title = re.compile('<h2 class="highlight-title">(.+?)</h2>', re.DOTALL).findall(entry)[0]
        detailurl = re.compile('<a class="highlight-title(.+?)<h2>', re.DOTALL).findall(entry)[0]
        detailurl = re.compile('href="(.+?)"', re.DOTALL).findall(detailurl)[0]
        date = re.compile('highlight-date">(.+?) | </div>', re.DOTALL).findall(entry)[0]
        highlighttime = re.compile('highlight-time">(.+?)</div>', re.DOTALL).findall(entry)[0]
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

        if showtimeframe == "false":
            debug("TVHighlights: Show only upcoming events")
            refreshtimestamp = int(time.time())
            now = datetime.datetime.now()
            highlightstimestampstr = '%s-%s-%s %s:00' % (now.year, now.month, now.day, highlighttime)
            highlightstimestampstr = highlightstimestampstr.replace('-', ' ')
            highlightstimestamp = date2timeStamp(highlightstimestampstr, "%Y %m %d %H:%M:%S")
            if (highlightstimestamp <= refreshtimestamp):
                debug("TVHighlights: Throw away entry, its in the past")
                continue
        channelexist = channelName2channelId(channel)
        debug("TVHighlights: Channel-Exists %s" % (channelexist))
        if (channelexist == 0):
            debug("TVHighlights: Channel %s not in PVR" % (channel))
            continue
        else:
            channelpvrid = channelexist
            debug("TVHighlights: Found Channel %s in PVR %s" % (channel,channelpvrid))
            logoUrl = str(pvrchannelid2logo(channelpvrid))
            channel = pvrchannelid2channelname(channelpvrid)

        debug("TVHighlights: %s" % (channelName2channelId(channel)))
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Title" %(watchtype,thumbNr), title )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Thumb" %(watchtype,thumbNr), thumbUrl )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Time" %(watchtype,thumbNr), highlighttime )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Date" %(watchtype,thumbNr), date )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Channel" %(watchtype,thumbNr), channel )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.PVRID" %(watchtype,thumbNr), str(channelpvrid) )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Icon" %(watchtype,thumbNr), thumbUrl )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Logo" %(watchtype,thumbNr), logoUrl )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Genre" %(watchtype,thumbNr), genre )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Comment" %(watchtype,thumbNr), comment )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Extrainfos" %(watchtype,thumbNr), extrainfos )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Popup" %(watchtype,thumbNr),detailurl)
        WINDOW.setProperty( "TV%sHighlightsToday.%s.WatchType" %(watchtype,thumbNr),watchtype)
        debug("===========TIP "+watchtype+" START=============")
        debug("Title "+title)
        debug("Thumb "+thumbUrl)
        debug("Time "+highlighttime)
        debug("Date "+date)
        debug("Channel "+channel)
        debug("PVRID %s" % (channelpvrid))
        debug("Icon "+thumbUrl)
        debug("Logo "+logoUrl)
        debug("Genre "+genre)
        debug("Comment "+comment)
        debug("Extrainfos "+extrainfos)
        debug("Detailurl "+detailurl)
        debug("Watchtype "+watchtype)
        debug("===========TIP "+watchtype+" END=============")
        thumbNr = thumbNr + 1
 



##########################################################################################################################
## Get movie details
##########################################################################################################################
def get_movie_details(url):
    # url.rstrip()
    debug("In Function get_movie_details with parameter: "+url)
    #### Start capture ####
    content = getUnicodePage(url, 'id="broadcast-content-box"', split=False)
    spl = content.split('id="broadcast-content-box"')
    debug("TestTest: %s - %s" % (str(type(spl)),len(spl)))
    if len(spl) == 1:
        notifyheader= str(__LS__(30010))
        notifytxt   = str(__LS__(30129))
        xbmc.executebuiltin('XBMC.Notification('+notifyheader+', '+notifytxt+' ,10000,'+__icon__+')')
        sys.exit()

    ### movie picture
    picture = re.compile('<img id="galpic" itemprop="image" src="(.+?)"', re.DOTALL).findall(content)[0]
    debug("Picture %s" % (picture))
    ### movie title
    titel = re.compile('<li id="broadcast-title" itemprop="name">(.+?)</li>', re.DOTALL).findall(content)[0]
    debug("Title %s" % (titel))
    ### movie subtitle
    subtitel = re.compile('<li id="broadcast-subtitle"><h2>(.+?)</h2>', re.DOTALL).findall(content)
    if len(subtitel) == 0:
        subtitel = ""
    else:
        subtitel = subtitel[0]
    debug(len(subtitel))
    ### movie broadcast details
    playson = re.compile('<li id="broadcast-title" itemprop="name">(.+?)<li id="broadcast-genre', re.DOTALL).findall(content)  # class="broadcast-info-icons
    playson = re.compile('<li>(.+?)</li>', re.DOTALL).findall(playson[0])
    if len(playson) == 0:
        playson = "-"
    else:
        playson = playson[0]
        playson = re.sub('<[^<]+?>','', str(playson))
    #playson = playson.lstrip('|')

    debug("Playson %s" % (playson))
    ### channel
    channel = str(playson.split('|',1)[0])
    channel = channel.strip()
    debug("Channel-Pre %s" % (channel))
    #playson = channel
    channelexist = channelName2channelId(channel)
    channelpvrid = channelexist
    channel = pvrchannelid2channelname(channelpvrid)
    debug("Channel-Post %s" % (channel))
 
    ### channel logo   
    logoUrl = str(pvrchannelid2logo(channelpvrid))
  
    ### start- end- time
    starttime = str(playson.split('|',len(str(playson)))[2]).split('-',1)[0].strip() 
    debug("Starttime %s" % (starttime))
    endtime = str(playson.split('|',len(str(playson)))[2]).split('-',1)[1] 
    debug("Endtime %s" % (endtime))
    df = xbmc.getRegion('dateshort') 
    tf = xbmc.getRegion('time').split(':')
    DATEFORMAT = df + ' ' + tf[0][0:2] + ':' + tf[1]
    now = datetime.datetime.now()
    startdate = '%s %s %s %s' % (now.year, now.month, now.day, str(starttime).strip())
    startdate = time.strptime(startdate,"%Y %m %d %H:%M")
    startdate = time.strftime(DATEFORMAT,startdate)

    debug("TVHighlights: Timer %s" % (startdate))


    playson = "%s :   %s - %s" % (channel,starttime,endtime)


    ############# rating values start
    ratingValue = re.compile('<span itemprop="ratingValue">(.+?)</span>', re.DOTALL).findall(content)
    if len(ratingValue) == 0:
        ratingValue = "-"
    else:
        ratingValue = ratingValue[0]
    reviewCount = re.compile('<span itemprop="reviewCount">(.+?)</span>', re.DOTALL).findall(content)
    if len(reviewCount) == 0:
        reviewCount = "-"
    else:
        reviewCount = reviewCount[0]
    bestRating = re.compile('<span itemprop="bestRating">(.+?)</span>', re.DOTALL).findall(content)
    if len(bestRating) == 0:
        bestRating = "-"
    else:
        bestRating = bestRating[0]
    ############# rating values end

    ### movie description start
    description = re.compile('<span itemprop="description">(.+?)</span>', re.DOTALL).findall(content)
    if len(description) == 0:
        description = "-"
    else:
        description = description[0]
    ### movie description end


##    ### actors
    actors = re.compile('class="person-list-actor">(.+?)class="person-list-crew', re.DOTALL).findall(content)
    debug(len(actors))
    if len(actors) > 0:
        actors = actors[0].split('<tr class=')
        actors.pop(0)
        actorsdata = []
        for i in actors:
            rolle = re.compile('<td>(.+?)</td>', re.DOTALL).findall(i)[0]
            if len(rolle) > 50:
                rolle = ""
            actor = re.compile('<span itemprop="name">(.+?)</span>', re.DOTALL).findall(i)[0]
            actordict={'rolle':rolle, 'actor':actor}
            actorsdata.append(actordict)
    else:
        actorsdata = ""

    crewdata = ""

    ### genre
    genre = re.compile('<ul class="genre"(.+?)class="desc-block">', re.DOTALL).findall(content)
    if len(genre) == 0:
        genre = ['nA']
    else:
        genre2 = re.compile('<span itemprop="genre">(.+?)</span>', re.DOTALL).findall(genre[0])
        debug(genre2)
        if len(genre2) == 0:
            genre2 = re.compile('<span >(.+?)</span>', re.DOTALL).findall(genre[0])
    genre = genre2

##    ### rating details
    rating = re.compile('<ul class="rating-box"(.+?)</ul>', re.DOTALL).findall(content)
    ratingdata = []
    if len(rating) > 0:
        rating = rating[0].split('<li>')
        rating.pop(0)
        for i in rating:
           ratingtype = i.split('<span')[0]
           ratingclass = re.compile('class="rating-(.+?)">', re.DOTALL).findall(i)
           ratingdict = {'ratingtype':ratingtype, 'rating': ratingclass}
           ratingdata.append(ratingdict)
    else:
        ratingdata = [ {'ratingtype':'Spannung', 'rating':'-'}, {'ratingtype':'Action', 'rating':'-'}, {'ratingtype':'Humor', 'rating':'-'}, {'ratingtype':'Romantik', 'rating':'-'}, {'ratingtype':'Sex', 'rating':'-'} ]
##
    ### broadcastinfo
    broadcastinfo = re.compile('class="broadcast-info-icons tvd-tooltip">(.+?)</ul>', re.DOTALL).findall(content)
    if len(broadcastinfo) > 0:
        broadcastinfo = re.compile('class="(.+?)"', re.DOTALL).findall(broadcastinfo[0])
    else:
        broadcastinfo = ""

    resultdict = {'titel':titel,'subtitel':subtitel,'picture':picture,'ratingValue':ratingValue,
                  'reviewCount':reviewCount,'bestRating':bestRating,'description':description,
                  'ratingdata':ratingdata,'genre':genre,'broadcastdetails':playson,'actorsdata':actorsdata,'date':startdate,
                  'crewdata':crewdata,'broadcastinfo':broadcastinfo,'channel':channel,'pvrid':channelpvrid,'starttime':starttime,'endtime':endtime,'logourl':logoUrl}
    return resultdict



##########################################################################################################################
## Show movie details window
##########################################################################################################################
def show_detail_window(detailurl):
    debug('Open detail window')
    DETAILS = get_movie_details(detailurl)

    PopupWindow = xbmcgui.WindowDialog()

    ### Set Background Window to skin default
    BGImage = xbmc.translatePath("special://skin/backgrounds/").decode('utf-8')
    BGImage = BGImage+"SKINDEFAULT.jpg"
    BGImage = xbmcgui.ControlImage(0,0,1280,720,BGImage)
    PopupWindow.addControl(BGImage)

    ### Set Background Panel
    ContentPanelIMG = xbmc.translatePath("special://skin/").decode('utf-8')
    ContentPanelIMG = ContentPanelIMG+"media/ContentPanel.png"
    BGPanel = xbmcgui.ControlImage(240,20,800,680,ContentPanelIMG)
    PopupWindow.addControl(BGPanel)

    ### Set Title Cover Image
    TitleCover = xbmcgui.ControlImage(650,170,320,240,DETAILS['picture'].decode('utf-8'))
    PopupWindow.addControl(TitleCover)

    ### Movie Title
    TitleLabel = xbmcgui.ControlFadeLabel(300, 80, 680, 15, font='font14',textColor='FF2E9AFE',_alignment=6)
    PopupWindow.addControl(TitleLabel)
    TitleLabel.addLabel(DETAILS['titel'])

    ### Movie SubTitle
    SubTitelLabel = xbmcgui.ControlLabel(300, 115, 680, 11, DETAILS['subtitel'],font='font11',alignment=6)
    PopupWindow.addControl(SubTitelLabel)
    #SubTitelLabel.setLabel(DETAILS['titel'])
    #xbmcgui.ControlLabel(300, 140, 300, 11, DETAILS['subtitel'],font='font11',textColor='FFFF3300'))

    ### Description Text
    PopupWindow.addControl(xbmcgui.ControlLabel(300, 440,300,10, 'Beschreibung:', font='font14',textColor='FF2E9AFE'))
    DescText = xbmcgui.ControlTextBox(300, 480, 670, 140) 
    PopupWindow.addControl(DescText)
    DescText.setText(DETAILS['description'])
    DescText.autoScroll(3000, 2500, 10000)
    ###

    ### Begin Broadcast Infos
    PopupWindow.addControl(xbmcgui.ControlLabel(300, 160,300,10, 'Rating:', font='font14',textColor='FF2E9AFE'))
    BCastInfo = xbmcgui.ControlFadeLabel(650, 420,320,10,_alignment=6)
    PopupWindow.addControl(BCastInfo)
    BCastInfo.addLabel(DETAILS['broadcastdetails'])
    ### End Broadcast Infos

    ### Begin Genre
    PopupWindow.addControl(xbmcgui.ControlLabel(300, 360,300,10, 'Genre:', font='font14',textColor='FF2E9AFE'))
    debug(DETAILS['genre'])
    genreSTR = ""
    for g in DETAILS['genre']:
        if len(genreSTR) > 0:
            genreSTR = genreSTR+", "+g
        else:
            genreSTR = g
    GenreLabel = xbmcgui.ControlFadeLabel(300, 400,310,10)
    PopupWindow.addControl(GenreLabel) 
    GenreLabel.addLabel(genreSTR)
    ### End Genre

    ### Begin Rating-Kategorie
    ratingy=200
    for r in DETAILS['ratingdata']:
        debug(r)
        PopupWindow.addControl(xbmcgui.ControlLabel(300, int(ratingy),300,10,r['ratingtype']))
        PopupWindow.addControl(xbmcgui.ControlLabel(500, int(ratingy),300,10,r['rating'][0]))
        ratingy = int(ratingy) + 30
    ### End Rating-Kategorie
    
    PopupWindow.doModal()




##########################################################################################################################
## Clear possible existing property values from detail info     
##########################################################################################################################
def clear_details_of_home():
    debug("Clear Details from Home")
    WINDOW.clearProperty( "TVHighlightsToday.Info.Title" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Picture" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Subtitle" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Description" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Broadcastdetails" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Genre" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.PVRID" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Channel" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Date" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.StartTime" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.EndTime" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Logo" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.RatingType.1" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Rating.1" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.RatingType.2" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Rating.2" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.RatingType.3" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Rating.3" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.RatingType.4" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Rating.4" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.RatingType.5" )
    WINDOW.clearProperty( "TVHighlightsToday.Info.Rating.5" )

##########################################################################################################################
## Set details to Home (INFO Labels)
##########################################################################################################################
def set_details_to_home(detailurl):
    debug('Set details to home screen')
    clear_details_of_home()
    #DETAILWIN = xbmcgui.WindowXMLDialog('script-TVHighlights-DialogWindow.xml', addonDir, 'Default', '720p')
    #DETAILWIN = xbmcgui.Window( 3099 )
    DETAILS   = get_movie_details(detailurl)
    debug(DETAILS)
    debug(xbmcgui.getCurrentWindowId())
    WINDOW.setProperty( "TVHighlightsToday.Info.Title", DETAILS['titel'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Picture", DETAILS['picture'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Subtitle", DETAILS['subtitel'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Description", DETAILS['description'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Broadcastdetails", DETAILS['broadcastdetails'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.PVRID", str(DETAILS['pvrid']) )
    WINDOW.setProperty( "TVHighlightsToday.Info.Channel", str(DETAILS['channel'].encode('utf-8')) )
    WINDOW.setProperty( "TVHighlightsToday.Info.StartTime", DETAILS['starttime'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.EndTime", DETAILS['endtime'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Date", DETAILS['date'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Logo", DETAILS['logourl'] )

    ### Begin Genre
    genreSTR = ""
    for g in DETAILS['genre']:
        if len(genreSTR) > 0:
            genreSTR = genreSTR+", "+g
        else:
            genreSTR = g
    WINDOW.setProperty( "TVHighlightsToday.Info.Genre", genreSTR )
    ### End Genre

    ### Begin Rating-Kategorie
    ratingy=200
    i=1
    for r in DETAILS['ratingdata']:
        WINDOW.setProperty( "TVHighlightsToday.Info.RatingType.%s" %(i), r['ratingtype'] )
        WINDOW.setProperty( "TVHighlightsToday.Info.Rating.%s" %(i), r['rating'][0] )
        ratingy = int(ratingy) + 30
        i += 1
    ### End Rating-Kategorie
    #DETAILWIN.doModal() 

##########################################################################################################################
## Set details to Window (INFO Labels)
##########################################################################################################################
def set_details_to_window(detailurl):
    debug('Set details to info screen')
    clear_details_of_home()
    DETAILWIN = xbmcgui.WindowXMLDialog('script-TVHighlights-DialogWindow.xml', __path__, 'Default', '720p')
    DETAILS   = get_movie_details(detailurl)
    debug(DETAILS)
    debug(xbmcgui.getCurrentWindowId())
    WINDOW.setProperty( "TVHighlightsToday.Info.Title", DETAILS['titel'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Picture", DETAILS['picture'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Subtitle", DETAILS['subtitel'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Description", DETAILS['description'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Broadcastdetails", DETAILS['broadcastdetails'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.PVRID", str(DETAILS['pvrid']) )
    WINDOW.setProperty( "TVHighlightsToday.Info.Channel", str(DETAILS['channel'].encode('utf-8')) )
    WINDOW.setProperty( "TVHighlightsToday.Info.StartTime", DETAILS['starttime'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.EndTime", DETAILS['endtime'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Date", DETAILS['date'] )
    WINDOW.setProperty( "TVHighlightsToday.Info.Logo", DETAILS['logourl'] )

    ### Begin Genre
    genreSTR = ""
    for g in DETAILS['genre']:
        if len(genreSTR) > 0:
            genreSTR = genreSTR+", "+g
        else:
            genreSTR = g
    WINDOW.setProperty( "TVHighlightsToday.Info.Genre", genreSTR )
    ### End Genre

    ### Begin Rating-Kategorie
    ratingy=200
    i=1
    for r in DETAILS['ratingdata']:
        WINDOW.setProperty( "TVHighlightsToday.Info.RatingType.%s" %(i), r['ratingtype'] )
        WINDOW.setProperty( "TVHighlightsToday.Info.Rating.%s" %(i), r['rating'][0] )
        ratingy = int(ratingy) + 30
        i += 1
    ### End Rating-Kategorie
    DETAILWIN.doModal() 



##########################################################################################################################
##########################################################################################################################
##
##                                                       M  A  I  N
##
##########################################################################################################################
##########################################################################################################################




##########################################################################################################################
## Get starting methode
##########################################################################################################################
debug("TVHighlights sysargv: "+str(sys.argv))
debug("TVHighlights mastermode: "+mastermode)
if len(sys.argv)>1:
    params = parameters_string_to_dict(sys.argv[1])
    methode = urllib.unquote_plus(params.get('methode', ''))
    watchtype = urllib.unquote_plus(params.get('watchtype', ''))
    detailurl = urllib.unquote_plus(params.get('detailurl', ''))
else:
    methode = None
    watchtype = None
    detailurl= "-"

debug("Methode in Script:")
debug(methode)

if methode=='mastermode':
        debug("Methode: Mastermode Retrieve")
        clear_tvdigital_mastermode_highlights()
        get_tvdigital_mastermode_highlights(watchtype)
 
elif methode=='getall_tvdigital':
        debug("Methode: Get All Highlights")
        for singlewatchtype in TVDigitalWatchtypes:
            clear_tvdigital_watchtype_highlights(singlewatchtype)
            get_tvdigital_watchtype_highlights(singlewatchtype)

elif methode=='get_single_tvdigital':
        debug("Methode: Single Methode Retrieve for "+watchtype)
        if watchtype in TVDigitalWatchtypes:
            clear_tvdigital_watchtype_highlights(watchtype)
            get_tvdigital_watchtype_highlights(watchtype)

elif methode=='infopopup':
        debug('Methode: set Detail INFOs to Window')
        set_details_to_window(detailurl)

elif methode=='get_tvdigital_movie_details':
        debug('Methode: should get moviedetails')
        show_detail_window(detailurl)

elif methode=='set_details_to_home':
        debug('Methode: get_details_to_home')
        set_details_to_home(detailurl)

elif methode=='get_mode':
    debug('Methode: getStatus') #FIXIT
    if mastermode == 'true':
        modeinfo = "mastermode"
    else:
        modeinfo = "splitmode"
        WINDOW.setProperty( "TVHighlightsToday.Mode", modeinfo )

elif methode=='refresh_mastermode':
        debug('Methode: refresh_mastermode')
        refresh_tvdigital_mastermode_highlights()

elif methode=='refresh_splitmode':
        debug('Methode: refresh_splitmode '+watchtype)
        setting_spielfilm     = __addon__.getSetting('setting_spielfilm')
        setting_sport         = __addon__.getSetting('setting_sport')
        setting_unterhaltung  = __addon__.getSetting('setting_unterhaltung')
        setting_serie         = __addon__.getSetting('setting_serie')
        setting_kinder        = __addon__.getSetting('setting_kinder')
        setting_doku          = __addon__.getSetting('setting_doku')
        if setting_spielfilm == 'true':
            refresh_tvdigital_splitmode_highlights('spielfilm')
        if setting_sport =='true':
            refresh_tvdigital_splitmode_highlights('sport')
        if setting_unterhaltung == 'true':
            refresh_tvdigital_splitmode_highlights('unterhaltung')
        if setting_serie == 'true':
            refresh_tvdigital_splitmode_highlights('serie')
        if setting_kinder == 'true':
            refresh_tvdigital_splitmode_highlights('kinder')
        if setting_doku == 'true':
            refresh_tvdigital_splitmode_highlights('doku')

elif methode=='get_split_elements':
        debug('Methode: get Split Elements')
        setting_spielfilm     = __addon__.getSetting('setting_spielfilm')
        setting_sport         = __addon__.getSetting('setting_sport')
        setting_unterhaltung  = __addon__.getSetting('setting_unterhaltung')
        setting_serie         = __addon__.getSetting('setting_serie')
        setting_kinder        = __addon__.getSetting('setting_kinder')
        setting_doku          = __addon__.getSetting('setting_doku')
        WINDOW.setProperty( "TVHighlightsToday.Splitmode.Spielfilm", str(setting_spielfilm) )
        WINDOW.setProperty( "TVHighlightsToday.Splitmode.Sport", str(setting_sport) )
        WINDOW.setProperty( "TVHighlightsToday.Splitmode.Unterhaltung", str(setting_unterhaltung) )
        WINDOW.setProperty( "TVHighlightsToday.Splitmode.Serie", str(setting_serie) )
        WINDOW.setProperty( "TVHighlightsToday.Splitmode.Kinder", str(setting_kinder) )
        WINDOW.setProperty( "TVHighlightsToday.Splitmode.Doku", str(setting_doku) )

elif methode=='get_master_elements':
        debug('Methode: get Master Elements')
        WINDOW.setProperty( "TVHighlightsToday.Mastermode", str(mastertype) )

elif methode=='show_select_dialog':
    debug('Methode: show select dialog')
    dialog = xbmcgui.Dialog()
    ret = dialog.select(str(__LS__(30011)), [str(__LS__(30120)), str(__LS__(30121)), str(__LS__(30122)), str(__LS__(30123)), str(__LS__(30124)), str(__LS__(30125))])
    debug(ret)
    clear_tvdigital_mastermode_highlights()
    if ret==0:
        get_tvdigital_mastermode_highlights('spielfilm')
    elif ret==1:
        get_tvdigital_mastermode_highlights('serie')
    elif ret==2:
        get_tvdigital_mastermode_highlights('sport')
    elif ret==3:
        get_tvdigital_mastermode_highlights('unterhaltung')
    elif ret==4:
        get_tvdigital_mastermode_highlights('doku-und-info')
    elif ret==5:
        get_tvdigital_mastermode_highlights('kinder')
    # else:
    #    get_tvdigital_mastermode_highlights('spielfilm')

elif methode=='set_mastermode':
    __addon__.setSetting('mastermode', 'true')
    WINDOW.setProperty( "TVHighlightsToday.Mode", "mastermode" )
    WINDOW.setProperty( "TVHighlightsToday.Mastermode", str(mastertype) )

elif methode=='set_splitmode':
    __addon__.setSetting('mastermode', 'false')
    WINDOW.setProperty( "TVHighlightsToday.Mode", "splitmode" )
    setting_spielfilm     = __addon__.getSetting('setting_spielfilm')
    setting_sport         = __addon__.getSetting('setting_sport')
    setting_unterhaltung  = __addon__.getSetting('setting_unterhaltung')
    setting_serie         = __addon__.getSetting('setting_serie')
    setting_kinder        = __addon__.getSetting('setting_kinder')
    setting_doku          = __addon__.getSetting('setting_doku')
    WINDOW.setProperty( "TVHighlightsToday.Splitmode.Spielfilm", str(setting_spielfilm) )
    WINDOW.setProperty( "TVHighlightsToday.Splitmode.Sport", str(setting_sport) )
    WINDOW.setProperty( "TVHighlightsToday.Splitmode.Unterhaltung", str(setting_unterhaltung) )
    WINDOW.setProperty( "TVHighlightsToday.Splitmode.Serie", str(setting_serie) )
    WINDOW.setProperty( "TVHighlightsToday.Splitmode.Kinder", str(setting_kinder) )
    WINDOW.setProperty( "TVHighlightsToday.Splitmode.Doku", str(setting_doku) )


elif methode=='settings' or methode==None or not (watchtype in TVDigitalWatchtypes):
        debug("Settings Methode Retrieve")
        if methode==None:
            notifyheader= str(__LS__(30010))
            notifytxt   = str(__LS__(30108))
            xbmc.executebuiltin('XBMC.Notification('+notifyheader+', '+notifytxt+' ,4000,'+__icon__+')')
        if mastermode=='true':
            clear_tvdigital_mastermode_highlights()
            get_tvdigital_mastermode_highlights(mastertype)
        else:
            setting_spielfilm     = __addon__.getSetting('setting_spielfilm')
            setting_sport         = __addon__.getSetting('setting_sport')
            setting_unterhaltung  = __addon__.getSetting('setting_unterhaltung')
            setting_serie         = __addon__.getSetting('setting_serie')
            setting_kinder        = __addon__.getSetting('setting_kinder')
            setting_doku          = __addon__.getSetting('setting_doku')

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
    
