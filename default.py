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

import urllib
import urllib2
import os
import re
import sys
import xbmc
import xbmcgui
import xbmcaddon
import time
import datetime
import json

from resources.lib.tvhighlights import TVDScraper

__addon__ = xbmcaddon.Addon()
__addonID__ = __addon__.getAddonInfo('id')
__addonname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__path__ = __addon__.getAddonInfo('path')
__LS__ = __addon__.getLocalizedString
__icon__ = xbmc.translatePath(os.path.join(__path__, 'icon.png'))

__showOutdated__ = True if __addon__.getSetting('showOutdated').upper() == 'TRUE' else False
__maxHLCat__ = int(re.match('\d+', __addon__.getSetting('max_hl_cat')).group())
__prefer_hd__ = True if __addon__.getSetting('prefer_hd').upper() == 'TRUE' else False

WINDOW = xbmcgui.Window(10000)
OSD = xbmcgui.Dialog()
TVDURL = 'http://www.tvdigital.de/tv-tipps/heute/'

# Helpers

def notifyOSD(header, message, icon=xbmcgui.NOTIFICATION_INFO, disp=4000, enabled=True):
    if enabled:
        OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon, disp)

def writeLog(message, level=xbmc.LOGNOTICE):
        try:
            xbmc.log('[%s %s]: %s' % (__addonID__, __version__,  message.encode('utf-8')), level)
        except Exception:
            xbmc.log('[%s %s]: %s' % (__addonID__, __version__,  'Fatal: Message could not displayed'), xbmc.LOGERROR)

# End Helpers

ChannelTranslateFile = xbmc.translatePath(os.path.join('special://home/addons', __addonID__, 'ChannelTranslate.json'))
with open(ChannelTranslateFile, 'r') as transfile:
    ChannelTranslate=transfile.read().rstrip('\n')

TVDWatchtypes = ['spielfilm', 'serie', 'sport', 'unterhaltung', 'doku-und-info', 'kinder']
TVDTranslations = {'spielfilm': __LS__(30120), 'serie': __LS__(30121), 'sport': __LS__(30122), 'unterhaltung': __LS__(30123), 'doku-und-info': __LS__(30124), 'kinder':__LS__(30125)}
properties = ['ID', 'Title', 'Thumb', 'Time', 'Channel', 'PVRID', 'Logo', 'Genre', 'Comment', 'Duration', 'Extrainfos', 'WatchType']
infoprops = ['Title', 'Picture', 'Subtitle', 'Description', 'Broadcastdetails', 'Channel', 'Date', 'StartTime', 'EndTime', 'Keywords', 'RatingType', 'Rating']

# create category list from selection in settings

def categories():
    cats = []
    for category in TVDWatchtypes:
        if __addon__.getSetting(category).upper() == 'TRUE': cats.append(category)
    return cats

# get remote URL, replace '\' and optional split into css containers

def getUnicodePage(url, container=None):
    try:
        req = urllib2.urlopen(url.encode('utf-8'))
    except UnicodeDecodeError:
        req = urllib2.urlopen(url)

    encoding = 'utf-8'
    if "content-type" in req.headers and "charset=" in req.headers['content-type']:
        encoding=req.headers['content-type'].split('charset=')[-1]
    content = unicode(req.read(), encoding).replace("\\", "")
    if container is None: return content
    return content.split(container)

# get parameter hash, convert into parameter/value pairs, return dictionary

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

# get used dateformat of kodi

def getDateFormat():
    df = xbmc.getRegion('dateshort')
    tf = xbmc.getRegion('time').split(':')

    try:
        # time format is 12h with am/pm
        return df + ' ' + tf[0][0:2] + ':' + tf[1] + ' ' + tf[2].split()[1]
    except IndexError:
        # time format is 24h with or w/o leading zero
        return df + ' ' + tf[0][0:2] + ':' + tf[1]

# convert datetime string to timestamp with workaround python bug (http://bugs.python.org/issue7980) - Thanks to BJ1

def date2timeStamp(date, format):
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

# get pvr channelname, translate from TVHighlights to pvr channelname if necessary

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
            writeLog("Translating %s to %s" % (channelname,tr['pvrname']), level=xbmc.LOGDEBUG)
            channelname = tr['pvrname']
    
    if 'result' in res and 'channels' in res['result']:
        res = res['result'].get('channels')
        for channels in res:

            # prefer HD Channel if available
            if __prefer_hd__ and  (channelname + " HD").lower() in channels['label'].lower():
                writeLog("TVHighlights found HD priorized channel %s" % (channels['label']), level=xbmc.LOGDEBUG)
                return channels['channelid']

            if channelname.lower() in channels['label'].lower():
                writeLog("TVHighlights found channel %s" % (channels['label']), level=xbmc.LOGDEBUG)
                return channels['channelid']
    return False

# get pvr channelname by id

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
                writeLog("TVHighlights found id for channel %s" % (channels['label']), level=xbmc.LOGDEBUG)
                return channels['label']
    return False

# get pvr channel logo url

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
        return False

# clear all info properties (info window) in Home Window

def clearInfoProperties():
    writeLog('clear all info properties (used in info popup)', level=xbmc.LOGDEBUG)
    for property in infoprops:
        WINDOW.clearProperty('TVHighlightsToday.Info.%s' % (property))
    for i in range(1, 5, 1):
        WINDOW.clearProperty('TVHighlightsToday.RatingType.%s' % (i))
        WINDOW.clearProperty('TVHighlightsToday.Rating.%s' % (i))

# clear content of widgets in Home Window

def clearWidgets(start_from=1):
    writeLog('Clear widgets from #%s and up' % (start_from), level=xbmc.LOGDEBUG)
    for i in range(start_from, 16, 1):
        for property in properties:
            WINDOW.clearProperty('TVHighlightsToday.%s.%s' % (i, property))

def refreshWidget(category, offset=0):

    if not __showOutdated__:
        writeLog("TVHighlights: Show only upcoming events", level=xbmc.LOGDEBUG)

    blobs = WINDOW.getProperty('TVD.%s.blobs' % category)
    if blobs == '': return 0

    widget = 1
    for i in range(1, int(blobs) + 1, 1):
        if widget > __maxHLCat__ or offset + widget > 15:
            writeLog('Max. Limit of widgets reached, abort processing', level=xbmc.LOGDEBUG)
            break

        writeLog('Processing blob TVD.%s.%s for widget #%s' % (category, i, offset + widget), level=xbmc.LOGDEBUG)

        blob = eval(WINDOW.getProperty('TVD.%s.%s' % (category, i)))

        if not __showOutdated__:
            _now = datetime.datetime.now()
            _dt = '%s.%s.%s %s' % (_now.day, _now.month, _now.year, blob['time'])
            timestamp = date2timeStamp(_dt, '%d.%m.%Y %H:%M')
            if timestamp < int(time.time()):
                writeLog('TVHighlights: discard blob TVD.%s.%s, start time @%s is in the past' % (category, i, _dt), level=xbmc.LOGDEBUG)
                continue

        WINDOW.setProperty('TVHighlightsToday.%s.ID' % (offset + widget), blob['id'])
        WINDOW.setProperty('TVHighlightsToday.%s.Title' % (offset + widget), blob['title'])
        WINDOW.setProperty('TVHighlightsToday.%s.Thumb' % (offset + widget), blob['thumb'])
        WINDOW.setProperty('TVHighlightsToday.%s.Time' % (offset + widget), blob['time'])
        WINDOW.setProperty('TVHighlightsToday.%s.Channel' % (offset + widget), blob['pvrid'])
        WINDOW.setProperty('TVHighlightsToday.%s.PVRID' % (offset + widget), blob['pvrid'])
        WINDOW.setProperty('TVHighlightsToday.%s.Logo' % (offset + widget), blob['logo'])
        WINDOW.setProperty('TVHighlightsToday.%s.Genre' % (offset + widget), blob['genre'])
        WINDOW.setProperty('TVHighlightsToday.%s.Comment' % (offset + widget), blob['comment'])
        WINDOW.setProperty('TVHighlightsToday.%s.Extrainfos' % (offset + widget), blob['extrainfos'])
        WINDOW.setProperty('TVHighlightsToday.%s.Popup' % (offset + widget), blob['popup'])
        WINDOW.setProperty('TVHighlightsToday.%s.WatchType' % (offset + widget), TVDTranslations[blob['category']])
        widget += 1

    return widget - 1

def refreshHighlights():

    offset = 0
    for category in categories():
        offset += refreshWidget(category, offset)
    clearWidgets(offset + 1)

def searchBlob(item, value):

    for category in categories():
        blobs = WINDOW.getProperty('TVD.%s.blobs' % category)
        if blobs == '':
            continue

        for idx in range(1, int(blobs) + 1, 1):
            blob = eval(WINDOW.getProperty('TVD.%s.%s' % (category, idx)))
            if blob[item] == value:
                return blob
    return False

def scrapeTVDPage(category):
    url = '%s%s/' % (TVDURL, category)
    writeLog('Start scraping category %s from %s' % (category, url), level=xbmc.LOGDEBUG)

    content = getUnicodePage(url, container='class="highlight-container"')
    i = 1
    content.pop(0)

    blobs = WINDOW.getProperty('TVD.%s.blobs' % (category))
    if blobs != '':

        for idx in range(1, int(blobs) + 1, 1):
            WINDOW.clearProperty('TVD.%s.%s' % (category, idx))

    for container in content:

        data = TVDScraper()
        data.scrapeHighlights(container)
        pvrchannelID = channelName2channelId(data.channel)
        if not  pvrchannelID:
            writeLog("TVHighlights: Channel %s is not in PVR, discard entry" % (data.channel), level=xbmc.LOGDEBUG)
            continue

        logoURL = pvrchannelid2logo(pvrchannelID)
        channel = pvrchannelid2channelname(pvrchannelID)

        writeLog('', level=xbmc.LOGDEBUG)
        writeLog('ID:             TVD.%s.%s' %(category, i), level=xbmc.LOGDEBUG)
        writeLog('Title:          %s' % (data.title), level=xbmc.LOGDEBUG)
        writeLog('Thumb:          %s' % (data.thumb), level=xbmc.LOGDEBUG)
        writeLog('Start time:     %s' % (data.starttime), level=xbmc.LOGDEBUG)
        writeLog('Channel (TVD):  %s' % (data.channel), level=xbmc.LOGDEBUG)
        writeLog('Channel (PVR):  %s' % (channel), level=xbmc.LOGDEBUG)
        writeLog('Channel logo:   %s' % (logoURL), level=xbmc.LOGDEBUG)
        writeLog('Genre:          %s' % (data.genre), level=xbmc.LOGDEBUG)
        writeLog('Comment:        %s' % (data.subtitle), level=xbmc.LOGDEBUG)
        writeLog('Extrainfos:     %s' % (data.extrainfos), level=xbmc.LOGDEBUG)
        writeLog('Popup:          %s' % (data.detailURL), level=xbmc.LOGDEBUG)
        writeLog('Watchtype:      %s' % (category), level=xbmc.LOGDEBUG)
        writeLog('', level=xbmc.LOGDEBUG)

        blob = {
                'id': unicode('TVD.%s.%s' % (i, category)),
                'title': unicode(data.title),
                'thumb': unicode(data.thumb),
                'time': unicode(data.starttime),
                'channel': unicode(data.channel),
                'pvrid': unicode(channel),
                'logo': unicode(logoURL),
                'genre': unicode(data.genre),
                'comment': unicode(unicode(data.subtitle)),
                'extrainfos': unicode(data.extrainfos),
                'popup': unicode(data.detailURL),
                'category': unicode(category),
               }

        WINDOW.setProperty('TVD.%s.%s' % (category, i), str(blob))
        i += 1

    WINDOW.setProperty('TVD.%s.blobs' % (category), str(i - 1))

# Set details to Window (INFO Labels)

def showInfoWindow(detailurl):
    writeLog('Set details to info screen', level=xbmc.LOGDEBUG)
    Popup = xbmcgui.WindowXMLDialog('script-TVHighlights-DialogWindow.xml', __path__, 'Default', '720p')

    data = TVDScraper()
    data.scrapeDetailPage(getUnicodePage(detailurl), 'id="broadcast-content-box"')

    blob = searchBlob('popup', detailurl)

    broadcastinfo = '%s: %s - %s' % (blob['pvrid'], blob['time'], data.endtime)

    writeLog('Title:             %s' % (blob['title']), level=xbmc.LOGDEBUG)
    writeLog('Thumb:             %s' % (blob['thumb']), level=xbmc.LOGDEBUG)
    writeLog('Channel (TVD):     %s' % (blob['channel']), level=xbmc.LOGDEBUG)
    writeLog('Preferred Channel: %s' % (blob['pvrid']), level=xbmc.LOGDEBUG)
    writeLog('Start Time:        %s' % (blob['time']), level=xbmc.LOGDEBUG)
    writeLog('End Time:          %s' % (data.endtime), level=xbmc.LOGDEBUG)
    writeLog('Rating Value:      %s' % (data.ratingValue), level=xbmc.LOGDEBUG)
    writeLog('Best Rating:       %s' % (data.bestRating), level=xbmc.LOGDEBUG)
    writeLog('Description:       %s' % (data.description), level=xbmc.LOGDEBUG)
    writeLog('Keywords:          %s' % (data.keywords), level=xbmc.LOGDEBUG)
    writeLog('Rating Data:       %s' % (data.ratingdata), level=xbmc.LOGDEBUG)
    writeLog('Broadcast Flags:   %s' % (data.broadcastflags), level=xbmc.LOGDEBUG)

    clearInfoProperties()

    now = datetime.datetime.now()
    _datetime = '%s.%s.%s %s' % (now.day, now.month, now.year, blob['time'])
    _date = time.strftime(getDateFormat(), time.strptime(_datetime, '%d.%m.%Y %H:%M'))

    WINDOW.setProperty( "TVHighlightsToday.Info.Title", blob['title'])
    WINDOW.setProperty( "TVHighlightsToday.Info.Picture", blob['thumb'])
    WINDOW.setProperty( "TVHighlightsToday.Info.Subtitle", blob['comment'])
    WINDOW.setProperty( "TVHighlightsToday.Info.Description", data.description)
    WINDOW.setProperty( "TVHighlightsToday.Info.Broadcastdetails", broadcastinfo)
    WINDOW.setProperty( "TVHighlightsToday.Info.Channel", blob['pvrid'])
    WINDOW.setProperty( "TVHighlightsToday.Info.Logo", blob['logo'])
    WINDOW.setProperty( "TVHighlightsToday.Info.Date", _date)
    WINDOW.setProperty( "TVHighlightsToday.Info.StartTime", blob['time'])
    WINDOW.setProperty( "TVHighlightsToday.Info.EndTime", data.endtime)
    WINDOW.setProperty( "TVHighlightsToday.Info.Keywords", data.keywords)

    # Ratings
    i = 1
    for r in data.ratingdata:
        WINDOW.setProperty( "TVHighlightsToday.Info.RatingType.%s" %(i), r['ratingtype'] )
        WINDOW.setProperty( "TVHighlightsToday.Info.Rating.%s" %(i), r['rating'][0] )
        i += 1

    Popup.doModal()

# M A I N
#________

# Get starting methode

methode = None
detailurl = None

if len(sys.argv)>1:
    params = parameters_string_to_dict(sys.argv[1])
    methode = urllib.unquote_plus(params.get('methode', ''))
    detailurl = urllib.unquote_plus(params.get('detailurl', ''))

writeLog("Methode from external script: %s" % (methode), level=xbmc.LOGDEBUG)
writeLog("Detailurl from external script: %s" % (detailurl), level=xbmc.LOGDEBUG)

if methode == 'scrape_highlights':
    for category in categories():
        scrapeTVDPage(category)
    refreshHighlights()

elif methode == 'refresh_screen':
    refreshHighlights()

elif methode == 'infopopup':
    showInfoWindow(detailurl)

elif methode=='show_select_dialog':
    writeLog('Methode: show select dialog', level=xbmc.LOGDEBUG)
    dialog = xbmcgui.Dialog()
    cats = [__LS__(30120), __LS__(30121), __LS__(30122), __LS__(30123), __LS__(30124), __LS__(30125)]
    ret = dialog.select(__LS__(30011), cats)

    if ret >= 0:
        writeLog('%s selected' % (cats[ret]), level=xbmc.LOGDEBUG)
        scrapeTVDPage(TVDWatchtypes[ret])
        empty_widgets = refreshWidget(TVDWatchtypes[ret])
        clearWidgets(empty_widgets + 1)
    else:
        refreshHighlights()
