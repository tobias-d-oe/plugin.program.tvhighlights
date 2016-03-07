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

WINDOW = xbmcgui.Window(10000)

OSD = xbmcgui.Dialog()

# Helpers

def notifyOSD(header, message, icon=xbmcgui.NOTIFICATION_INFO, disp=4000, enabled=True):
    if enabled:
        OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon, disp)

def writeLog(message, level=xbmc.LOGNOTICE):
        xbmc.log('[%s %s]: %s' % (__addonID__, __version__,  message.encode('utf-8')), level)

# End Helpers

ChannelTranslateFile = xbmc.translatePath(os.path.join('special://home/addons', __addonID__, 'ChannelTranslate.json'))
with open(ChannelTranslateFile, 'r') as transfile:
    ChannelTranslate=transfile.read().rstrip('\n')

TVDWatchtypes = ['spielfilm', 'serie', 'sport', 'unterhaltung', 'doku-und-info', 'kinder']
properties = ['Title', 'Thumb', 'Time', 'Date', 'Channel', 'PVRID', 'Icon', 'Logo', 'Genre', 'Comment', 'Year', 'Duration', 'Extrainfos', 'WatchType']
infoprops = ['Title', 'Picture', 'Subtitle', 'Description', 'Broadcastdetails', 'Channel', 'StartTime', 'EndTime', 'Keywords', 'RatingType', 'Rating']

mastermode = True if __addon__.getSetting('mastermode').upper() == 'TRUE' else False
showtimeframe = True if __addon__.getSetting('showtimeframe').upper() == 'TRUE' else False
mastertype = __addon__.getSetting('mastertype')

def getsplitmodes():
    splitmodes = []
    for watchtype in TVDWatchtypes:
        if __addon__.getSetting(watchtype).upper() == 'TRUE': splitmodes.append(watchtype)
    return splitmodes

# get remote URL, replace '\' and optional split into css containers

def getUnicodePage(url, container=None):
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
    writeLog("Date date2timeStamp : %s" % (date), level=xbmc.LOGDEBUG)
    writeLog("Format date2timeStamp : %s" % (format), level=xbmc.LOGDEBUG)
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

            # priorize HD Channel
            if channelname+" HD".lower() in channels['label'].lower(): 
                writeLog("TVHighlights found HD priorized channel %s" % (channels['label']), level=xbmc.LOGDEBUG)
                return channels['channelid']
            if channelname.lower() in channels['label'].lower(): 
                writeLog("TVHighlights found  channel %s" % (channels['label']), level=xbmc.LOGDEBUG)
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

# clear all properties in Home Window

def clearProperties(watchtype=''):
    writeLog('clear all TVHighlights properties', level=xbmc.LOGDEBUG)
    for i in range(1, 14, 1):
        for property in properties:
            WINDOW.clearProperty( "TV%sHighlightsToday.%s.%s" %(watchtype, i, property))

# clear all info properties (info window) in Home Window

def clearInfoProps():
    writeLog('clear all info properties (used in info popup)', level=xbmc.LOGDEBUG)
    for property in infoprops:
        WINDOW.clearProperty('TVHighlightsToday.Info.%s' % (property))
    for i in range(1, 5, 1):
        WINDOW.clearProperty('TVHighlightsToday.RatingType.%s' % (i))
        WINDOW.clearProperty('TVHighlightsToday.Rating.%s' % (i))

# read all properties, build dictionary blob

def readProperties(watchtype=''):
    highlights = []

    for i in range(1, 14, 1):
        entry = {
                "id": i,
                "title": WINDOW.getProperty("TV%sHighlightsToday.%s.Title" % (watchtype, i)).decode("utf8"),
                "thumb": WINDOW.getProperty("TV%sHighlightsToday.%s.Thumb" % (watchtype, i)).decode("utf8"),
                "time": WINDOW.getProperty("TV%sHighlightsToday.%s.Time" % (watchtype, i)).decode("utf8"),
                "date": WINDOW.getProperty("TV%sHighlightsToday.%s.Date" % (watchtype, i)).decode("utf8"),
                "channel": WINDOW.getProperty("TV%sHighlightsToday.%s.Channel" % (watchtype, i)).decode("utf8"),
                "pvrid": WINDOW.getProperty("TV%sHighlightsToday.%s.PVRID" % (watchtype, i)).decode("utf8"),
                "icon": WINDOW.getProperty("TV%sHighlightsToday.%s.Icon" % (watchtype, i)).decode("utf8"),
                "logo": WINDOW.getProperty("TV%sHighlightsToday.%s.Logo" % (watchtype, i)).decode("utf8"),
                "genre": WINDOW.getProperty("TV%sHighlightsToday.%s.Genre" % (watchtype, i)).decode("utf8"),
                "comment": WINDOW.getProperty("TV%sHighlightsToday.%s.Comment" % (watchtype, i)).decode("utf8"),
                "year": WINDOW.getProperty("TV%sHighlightsToday.%s.Year" % (watchtype, i)).decode("utf8"),
                "duration": WINDOW.getProperty("TV%sHighlightsToday.%s.Duration" % (watchtype, i)).decode("utf8"),
                "extrainfos": WINDOW.getProperty("TV%sHighlightsToday.%s.Extrainfos" % (watchtype, i)).decode("utf8"),
                "watchtype": WINDOW.getProperty("TV%sHighlightsToday.%s.WatchType" % (watchtype, i)).decode("utf8")
                }
        writeLog("TV Highlights: blob %s: %s" % (i, entry), level=xbmc.LOGDEBUG)
        highlights.append(entry)

    return highlights

# refresh content timebased in splitmode -  watchtype is one of spielfilm, sport, serie, unterhaltung, doku, kinder

def refresh_tvdigital_splitmode_highlights(watchtype=''):

    highlights = readProperties(watchtype)
    clearProperties(watchtype)

    i = 1
    for highlight in highlights:
        writeLog("Processing title: %s in watchtype %s" % (highlight["title"], watchtype), level=xbmc.LOGDEBUG)

        if len(highlight["time"]) < 4:
            writeLog('TV Highlights: Empty Time...', level=xbmc.LOGDEBUG)
            continue
        else:
            writeLog("Highlightstime: %s" % (highlight["time"]), level=xbmc.LOGDEBUG)
        now = datetime.datetime.now()
        htsstr = '%s %s %s %s:00' % (now.year, now.month, now.day, highlight["time"])
        hts = date2timeStamp(htsstr, "%Y %m %d %H:%M:%S")

        curts = time.time()
        if int(hts) < int(curts):
            writeLog('Remove outdated entry', level=xbmc.LOGDEBUG)
            continue
        else:
            writeLog("Highlighttime is in future: %s - %s" % (hts, curts), level=xbmc.LOGDEBUG)

        WINDOW.setProperty("TV%sHighlightsToday.%s.Title" % (watchtype, i), highlight["title"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.Thumb" % (watchtype, i), highlight["thumb"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.Time" % (watchtype, i), highlight["time"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.Date" % (watchtype, i), highlight["date"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.Channel" % (watchtype, i), highlight["channel"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.PVRID" % (watchtype, i), highlight["pvrid"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.Icon" % (watchtype, i), highlight["icon"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.Logo" % (watchtype, i), highlight["logo"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.Genre" % (watchtype, i), highlight["genre"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.Comment" % (watchtype, i), highlight["comment"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.Year" % (watchtype, i), highlight["year"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.Duration" % (watchtype, i), highlight["duration"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.Extrainfos" % (watchtype, i), highlight["extrainfos"])
        WINDOW.setProperty("TV%sHighlightsToday.%s.WatchType" % (watchtype, i), highlight["watchtype"])
        i += 1

# refresh content timebased in mastermode

def refresh_tvdigital_mastermode_highlights():
    refresh_tvdigital_splitmode_highlights(mastermode)

# retrieve tvhighlights (mastermode)

 # Retrieve tvhighlights for a choosen watchtype. Set Home properties.
# Possible watchtypes are spielfilm, sport, serie, unterhaltung, doku-und-info, kinder

def get_tvd_highlights(watchtype):
    url = 'http://www.tvdigital.de/tv-tipps/heute/%s/' % (watchtype)
    writeLog('Start retrieving watchtype %s from %s' % (watchtype, url), level=xbmc.LOGDEBUG)

    spl = getUnicodePage(url, container='class="highlight-container"')
    data = TVDScraper()
    max = 10

    for i in range(1, len(spl), 1):
        if i > max:
            break

        data.scrapeHighlights(spl[i])

        if not showtimeframe:
            writeLog("TVHighlights: Show only upcoming events", level=xbmc.LOGDEBUG)
            now = datetime.datetime.now()
            data.datetime = '%s.%s.%s %s' % (now.day, now.month, now.year, data.starttime)
            timestamp = date2timeStamp(data.datetime, '%d.%m.%Y %H:%M')
            if timestamp < int(time.time()):
                writeLog('TVHighlights: discard entry, start time is in the past', level=xbmc.LOGDEBUG)
                continue

        pvrchannel = channelName2channelId(data.channel)
        if not  pvrchannel:
            writeLog("TVHighlights: Channel %s is not in PVR, discard entry" % (data.channel), level=xbmc.LOGDEBUG)
            continue

        data.logoURL = pvrchannelid2logo(pvrchannel)
        data.channel = pvrchannelid2channelname(pvrchannel)

        writeLog('Data for item   #%s' %(i), level=xbmc.LOGDEBUG)
        writeLog('Success:        %s' % (data.success), level=xbmc.LOGDEBUG)
        writeLog('Title:          %s' % (data.title), level=xbmc.LOGDEBUG)
        writeLog('Picture:        %s' % (data.picture), level=xbmc.LOGDEBUG)
        writeLog('Time:           %s' % (data.starttime), level=xbmc.LOGDEBUG)
        writeLog('Date:           %s' % (data.date), level=xbmc.LOGDEBUG)
        writeLog('Comment:        %s' % (data.subtitle), level=xbmc.LOGDEBUG)
        writeLog('Channel:        %s' % (data.channel), level=xbmc.LOGDEBUG)
        writeLog('PVRID:          %s' % (pvrchannel), level=xbmc.LOGDEBUG)
        writeLog('Icon:           %s' % (data.picture), level=xbmc.LOGDEBUG)
        writeLog('Logo:           %s' % (data.logoURL), level=xbmc.LOGDEBUG)
        writeLog('Genre:          %s' % (data.genre), level=xbmc.LOGDEBUG)
        writeLog('Extrainfos:     %s' % (data.extrainfos), level=xbmc.LOGDEBUG)
        writeLog('Popup:          %s' % (data.detailURL), level=xbmc.LOGDEBUG)
        writeLog('Watchtype:      %s' % (watchtype), level=xbmc.LOGDEBUG)

        watchtype = ''
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Title" %(watchtype,i), data.title )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Thumb" %(watchtype,i), data.picture )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Time" %(watchtype,i), data.starttime )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Date" %(watchtype,i), data.date )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Channel" %(watchtype,i), data.channel )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.PVRID" %(watchtype,i), str(pvrchannel) )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Icon" %(watchtype,i), data.picture )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Logo" %(watchtype,i), data.logoURL )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Genre" %(watchtype,i), data.genre )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Comment" %(watchtype,i), data.subtitle )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Extrainfos" %(watchtype,i), data.extrainfos )
        WINDOW.setProperty( "TV%sHighlightsToday.%s.Popup" %(watchtype,i), data.detailURL)
        WINDOW.setProperty( "TV%sHighlightsToday.%s.WatchType" %(watchtype,i),watchtype)

# Set details to Window (INFO Labels)

def showInfoWindow(detailurl):
    writeLog('Set details to info screen', level=xbmc.LOGDEBUG)
    Popup = xbmcgui.WindowXMLDialog('script-TVHighlights-DialogWindow.xml', __path__, 'Default', '720p')

    data = TVDScraper()
    data.scrapeDetailPage(getUnicodePage(detailurl), 'id="broadcast-content-box"')

    writeLog('Success:        %s' % (data.success), level=xbmc.LOGDEBUG)
    writeLog('Title:          %s' % (data.title), level=xbmc.LOGDEBUG)
    writeLog('Subtitle:       %s' % (data.subtitle), level=xbmc.LOGDEBUG)
    writeLog('Picture:        %s' % (data.picture), level=xbmc.LOGDEBUG)
    writeLog('Channel:        %s' % (data.channel), level=xbmc.LOGDEBUG)
    writeLog('Start Time:     %s' % (data.starttime), level=xbmc.LOGDEBUG)
    writeLog('End Time:       %s' % (data.endtime), level=xbmc.LOGDEBUG)
    writeLog('Rating Value:   %s' % (data.ratingValue), level=xbmc.LOGDEBUG)
    writeLog('Reviews:        %s' % (data.reviewCount), level=xbmc.LOGDEBUG)
    writeLog('Best Rating:    %s' % (data.bestRating), level=xbmc.LOGDEBUG)
    writeLog('Description:    %s' % (data.description), level=xbmc.LOGDEBUG)
    writeLog('Keywords:       %s' % (data.keywords), level=xbmc.LOGDEBUG)
    writeLog('Rating Data:    %s' % (data.ratingdata), level=xbmc.LOGDEBUG)
    writeLog('Broadcast Info: %s' % (data.broadcastinfo), level=xbmc.LOGDEBUG)

    clearInfoProps()

    if data.success:

        now = datetime.datetime.now()
        data.datetime = '%s.%s.%s %s' % (now.day, now.month, now.year, data.starttime)
        data.date = time.strftime(getDateFormat(), time.strptime(data.datetime, '%d.%m.%Y %H:%M'))

        WINDOW.setProperty( "TVHighlightsToday.Info.Title", data.title)
        WINDOW.setProperty( "TVHighlightsToday.Info.Picture", data.picture)
        WINDOW.setProperty( "TVHighlightsToday.Info.Subtitle", data.subtitle)
        WINDOW.setProperty( "TVHighlightsToday.Info.Description", data.description)
        WINDOW.setProperty( "TVHighlightsToday.Info.Broadcastdetails", data.broadcastinfo)
        WINDOW.setProperty( "TVHighlightsToday.Info.Channel", data.channel)
        WINDOW.setProperty( "TVHighlightsToday.Info.Date", data.date)
        WINDOW.setProperty( "TVHighlightsToday.Info.StartTime", data.starttime)
        WINDOW.setProperty( "TVHighlightsToday.Info.EndTime", data.endtime)
        WINDOW.setProperty( "TVHighlightsToday.Info.Keywords", ', '.join(data.keywords))

        # Ratings
        i = 1
        for r in data.ratingdata:
            WINDOW.setProperty( "TVHighlightsToday.Info.RatingType.%s" %(i), r['ratingtype'] )
            WINDOW.setProperty( "TVHighlightsToday.Info.Rating.%s" %(i), r['rating'][0] )
            i += 1

        Popup.doModal()


# Parameter Wrapper, strongly required to ensure backward compatibility

def get_tvdigital_mastermode_highlights(watchtype):
    get_tvd_highlights(watchtype)

def get_tvdigital_watchtype_highlights(singewatchtype):
    get_tvd_highlights(singewatchtype)




# M A I N
#________

# Get starting methode

writeLog("TVHighlights sysargv: "+str(sys.argv), level=xbmc.LOGDEBUG)
writeLog("TVHighlights mastermode: %s" % (mastermode), level=xbmc.LOGDEBUG)
if len(sys.argv)>1:
    params = parameters_string_to_dict(sys.argv[1])
    methode = urllib.unquote_plus(params.get('methode', ''))
    watchtype = urllib.unquote_plus(params.get('watchtype', ''))
    detailurl = urllib.unquote_plus(params.get('detailurl', ''))
else:
    methode = None
    watchtype = None
    detailurl= "-"

writeLog("Methode in Script: %s" % (methode), level=xbmc.LOGDEBUG)

if methode=='mastermode':
        writeLog("Methode: Mastermode Retrieve", level=xbmc.LOGDEBUG)
        clearProperties()
        get_tvdigital_mastermode_highlights(watchtype)
 
elif methode=='getall_tvdigital':
        writeLog("Methode: Get All Highlights", level=xbmc.LOGDEBUG)
        for singlewatchtype in TVDWatchtypes:
            clearProperties(singlewatchtype)
            get_tvdigital_watchtype_highlights(singlewatchtype)

elif methode=='get_single_tvdigital':
        writeLog("Methode: Single Methode Retrieve for "+watchtype, level=xbmc.LOGDEBUG)
        if watchtype in TVDWatchtypes:
            clearProperties(watchtype)
            get_tvd_highlights(watchtype)

elif methode=='infopopup':
        writeLog('Methode: set Detail INFOs to Window', level=xbmc.LOGDEBUG)
        showInfoWindow(detailurl)

elif methode=='get_tvdigital_movie_details':
        writeLog('Methode: should get moviedetails', level=xbmc.LOGDEBUG)
        # show_detail_window(detailurl)

#elif methode=='set_details_to_home':
#        writeLog('Methode: set_details_to_home', level=xbmc.LOGDEBUG)
#        set_details_to_home(detailurl)

elif methode=='get_mode':
    writeLog('Methode: getStatus', level=xbmc.LOGDEBUG) #FIXIT
    if mastermode:
        modeinfo = "mastermode"
    else:
        modeinfo = "splitmode"
        WINDOW.setProperty( "TVHighlightsToday.Mode", modeinfo )

elif methode=='refresh_mastermode':
        writeLog('Methode: refresh_mastermode', level=xbmc.LOGDEBUG)
        refresh_tvdigital_mastermode_highlights()

elif methode=='refresh_splitmode':
        writeLog('Methode: refresh_splitmode '+watchtype, level=xbmc.LOGDEBUG)
        for mode in getsplitmodes():
            refresh_tvdigital_splitmode_highlights(mode)

elif methode=='get_split_elements':
        writeLog('Methode: get Split Elements', level=xbmc.LOGDEBUG)
        setting_spielfilm     = __addon__.getSetting('spielfilm')
        setting_sport         = __addon__.getSetting('sport')
        setting_unterhaltung  = __addon__.getSetting('unterhaltung')
        setting_serie         = __addon__.getSetting('serie')
        setting_kinder        = __addon__.getSetting('kinder')
        setting_doku          = __addon__.getSetting('doku')
        WINDOW.setProperty("TVHighlightsToday.Splitmode.Spielfilm", str(setting_spielfilm))
        WINDOW.setProperty("TVHighlightsToday.Splitmode.Sport", str(setting_sport))
        WINDOW.setProperty("TVHighlightsToday.Splitmode.Unterhaltung", str(setting_unterhaltung))
        WINDOW.setProperty("TVHighlightsToday.Splitmode.Serie", str(setting_serie))
        WINDOW.setProperty("TVHighlightsToday.Splitmode.Kinder", str(setting_kinder))
        WINDOW.setProperty("TVHighlightsToday.Splitmode.Doku", str(setting_doku))

elif methode=='get_master_elements':
        writeLog('Methode: get Master Elements', level=xbmc.LOGDEBUG)
        WINDOW.setProperty("TVHighlightsToday.Mastermode", str(mastertype))

elif methode=='show_select_dialog':
    writeLog('Methode: show select dialog', level=xbmc.LOGDEBUG)
    dialog = xbmcgui.Dialog()
    ret = dialog.select(__LS__(30011), [__LS__(30120), __LS__(30121), __LS__(30122), __LS__(30123), __LS__(30124), __LS__(30125)])
    writeLog(str(ret), level=xbmc.LOGDEBUG)
    clearProperties()
    if ret >= 0:
        get_tvdigital_mastermode_highlights(TVDWatchtypes[ret])

elif methode=='set_mastermode':
    __addon__.setSetting('mastermode', 'true')
    WINDOW.setProperty("TVHighlightsToday.Mode", "mastermode")
    WINDOW.setProperty("TVHighlightsToday.Mastermode", str(mastertype))

elif methode=='set_splitmode':
    __addon__.setSetting('mastermode', 'false')
    WINDOW.setProperty( "TVHighlightsToday.Mode", "splitmode" )
    setting_spielfilm     = __addon__.getSetting('spielfilm')
    setting_sport         = __addon__.getSetting('sport')
    setting_unterhaltung  = __addon__.getSetting('unterhaltung')
    setting_serie         = __addon__.getSetting('serie')
    setting_kinder        = __addon__.getSetting('kinder')
    setting_doku          = __addon__.getSetting('doku')
    WINDOW.setProperty("TVHighlightsToday.Splitmode.Spielfilm", str(setting_spielfilm))
    WINDOW.setProperty("TVHighlightsToday.Splitmode.Sport", str(setting_sport))
    WINDOW.setProperty("TVHighlightsToday.Splitmode.Unterhaltung", str(setting_unterhaltung))
    WINDOW.setProperty("TVHighlightsToday.Splitmode.Serie", str(setting_serie))
    WINDOW.setProperty("TVHighlightsToday.Splitmode.Kinder", str(setting_kinder))
    WINDOW.setProperty("TVHighlightsToday.Splitmode.Doku", str(setting_doku))


elif methode=='settings' or methode is None or not (watchtype in TVDWatchtypes):
        writeLog("Settings Methode Retrieve", level=xbmc.LOGDEBUG)
        if methode is None:
            notifyheader= str(__LS__(30010))
            notifytxt   = str(__LS__(30108))
            xbmc.executebuiltin('XBMC.Notification('+notifyheader+', '+notifytxt+' ,4000,'+__icon__+')')
        if mastermode:
            clearProperties()
            get_tvdigital_mastermode_highlights(mastertype)
        else:
            for mode in getsplitmodes():
                get_tvdigital_watchtype_highlights(mode)
