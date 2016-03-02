###########################################################################
#
#          FILE:  plugin.program.tvhighlights
#
#        AUTHOR:  Tobias D. Oestreicher
#
#       LICENSE:  GPLv3 <http://www.gnu.org/licenses/gpl.txt>
#       VERSION:  0.1.2
#       CREATED:  22.01.2016
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
#     CHANGELOG:  (22.01.2016) TDOe - First Publishing
###########################################################################


Beschreibung:
=============

Das Plugin plugin.program.tvhighlights holt von tvdigital.de die TV-Highlights des Tages und stellt diese dann als 
RecentlyAdded Widget beim Menüpunkt TV bereit (nach Skintegration).
Hierbei richtet sich das Plugin anhand der im PVR befindlichen Sender, und zeigt nur TV Highlights für diese an.
Desweiteren besteht eine integration des Dienstes service.kn.switchtimer in der Sendungs-Detailansicht mit 
welchem die Highlights zum umschalten vorgemerkt werden können.

Im Settingsmenü kann eingestellt werden welche Kategorie für die Anzeige und Aktualisierung verwendet werden soll.
Zur Auswahl stehen hier folgende Kategorien:
  * spielfilme
  * serien
  * sport
  * kinder
  * doku und info
  * unterhaltung

Ein Popup-Window kann für die Highlights geöffnet werden, in welchem Detailinformationen zur Sendung angezeigt werden, und mithilfe des Dienstes "service.kn.switchtimer" (Danke BJ1) kann ein Umschalten vorgemerkt werden.

Das Plugin wird bei jedem Kodi Start ausgefüht und aktualisiert die Daten. Je nachdem welches Interval man für Content Refresh eingestellt hat geht es in eine Loop 
und aktualisiert die TV-Highlights anhand der eingestellten Minuten. Ist hier die "0" ausgewählt, beendet sich der Dienst, ohne Daten abzurufen. Die Anzeige Aktualisierung kann hier seperat eingestellt werden.



Modi:
==============

Es gibt zwei Modi in denen das Plugin betrieben werden kann:
- Mastermode
- Splitmode


Mastermode:
--------------
Im Mastermode wird eine Kategorie ausgewählt welche vom Plugin automatisch aktualisiert wird.
Als Kategorie (watchtype) kann folgendes verwendet werden: 
- spielfilm
- serie
- unterhaltung
- sport
- kinder
- doku-und-info



Splitmode:
--------------
Hierbei können mehrere Kategorien ausgewählt werden welche vom Plugin aktualisiert werden sollen. 
Die zur Verfügung stehenden Kategorien sind die selben wie im Mastermode.


Einstellungen:
==============
Das Plugin kann so konfiguriert werden dass nur Sendungen angezeigt werden, welche beim letzten screen refresh nicht schon in der Vergangenheit lagen.
Weiterhin kann das Content Refresh Interval konfiguriert werden. (Bitte denkt an den Hoster, also nicht zu oft aktualisieren. Denke kleiner 120 Minuten ist unnötig)
Auch die Popup Nachricht beim Start von kodi und dem Content-Refresh kann aktiviert/deaktiviert werden.





=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=
=*=                                                              Für Skinner                                                                        =*=
=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=


Skintegration:
==============

Um die TVHighlights des Tages in Confluence zu integrieren sind folgende Schritte erforderlich (als Beispiel
dient hier die Integration unter einer Linux-Distribution). Die zum Kopieren erforderlichen Dateien befinden
sich im Ordner 'integration' des Plugins (plugin.program.tvhighlights):

cd $HOME/.kodi/addons/plugin.program.tvhighlights/integration

1. Kopieren des XML Files in den Confluence Skin Ordner
   (für mastermode:script-tvhighlights.xml; für splitmode:script-tvhighlights-splitmode-simple.xml)

  cp *.xml /usr/share/kodi/addons/skin.confluence/720p/

2. Script als include am Skin "anmelden"
Hierzu die Datei "/usr/share/kodi/addons/skin.confluence/720p/includes.xml" editieren, und unterhalb der Zeile:

  <include file="IncludesHomeRecentlyAdded.xml" />

folgendes einfügen:

  <include file="script-tvhighlights.xml" />

3. Das include in "/usr/share/kodi/addons/skin.confluence/720p/IncludesHomeRecentlyAdded.xml" ergänzen:
folgendes include Tag muss innerhalb der ControlGroup mit der ID 9003 ergänzt werden.
  
  <include>HomeRecentlyAddedTVHighlightsTodayInfo</include>

Beispiel:
---------------8<---------------
  1 <?xml version="1.0" encoding="UTF-8"?>
  2 <includes>
  3         <include name="HomeRecentlyAddedInfo">
  4                 <control type="group" id="9003">
  5                         <onup>20</onup>
  6                         <ondown condition="System.HasAddon(script.globalsearch)">608</ondown>
  7                         <ondown condition="!System.HasAddon(script.globalsearch)">603</ondown>
  8                         <visible>!Window.IsVisible(Favourites)</visible>
  9                         <include>VisibleFadeEffect</include>
 10                         <animation effect="fade" time="225" delay="750">WindowOpen</animation>
 11                         <animation effect="fade" time="150">WindowClose</animation>
 12                         <include>HomeRecentlyAddedTVHighlightsTodayInfo</include>

--------------->8---------------


4. Kategorie Wahl für TV Highlights im Master Mode hinzufügen (optional)

in der Datei "/usr/share/kodi/addons/skin.confluence/720p/IncludesHomeMenuItems.xml"
folgende Stelle suchen:

---------------8<---------------
        <include name="HomeSubMenuTV">
                <control type="image" id="90141">
                        <width>35</width>
                        <height>35</height>
                        <texture border="0,0,0,3" flipx="true">HomeSubEnd.png</texture>
                </control>
--------------->8---------------

direkt im Anschluss den zusätzlichen Button hinzufügen:

---------------8<---------------
<!-- Begin neu eingefuegter Button -->
                <control type="button" id="97149">
                        <include>ButtonHomeSubCommonValues</include>
                        <label>$ADDON[plugin.program.tvhighlights  30126]</label>
                        <onclick>RunScript(plugin.program.tvhighlights,"?methode=show_select_dialog")</onclick>
                </control>
<!-- Ende neu eingefuegter Button -->

--------------->8---------------



Pluginaufrufe:
==============

Durch die Methode "settings" wird je nach gesetztem Benutzersetting entschieden was aktualisiert werden soll in welchem Modus.

    XBMC.RunScript(plugin.program.tvhighlights,"?methode=settings")


Ruft das Plugin im Mastermode auf mit "spielfilm" als watchtype

    XBMC.RunScript(plugin.program.tvhighlights,"?methode=mastermode&watchtype=spielfilm")


Ruft das Plugin im Splitmode auf mit "sport" als aktualisierungsziel.

    XBMC.RunScript(plugin.program.tvhighlights,"?methode=get_single_tvdigital&watchtype=sport")


Ruft das Plugin im Splitmode auf und aktualisiert alle watchtypen

    XBMC.RunScript(plugin.program.tvhighlights,"?methode=getall_tvdigital")


Startet den Kategorie Dialog für den Master Mode

    XBMC.RunScript(plugin.program.tvhighlights,"?methode=show_select_dialog")


Beispiel 'onclick' für TV Highlights Element - Öffnet Popup generiert vom Plugin (script-TVHighlights-DialogWindow.xml):
    <onclick>
        RunScript(plugin.program.tvhighlights,"?methode=infopopup&detailurl=$INFO[Window.Property(TVHighlightsToday.1.Popup)]")
    </onclick>


Beispiel 'onclick' für TV Highlights Element - Öffnet Popup generiert vom Plugin (Python):
    <onclick>
        RunScript(plugin.program.tvhighlights,"?methode=get_tvdigital_movie_details&detailurl=$INFO[Window.Property(TVHighlightsToday.1.Popup)]")
    </onclick>


Beispiel 'onclick' für TV Highlights Element - Setzt Properties für Filmdetails auf das Home Window:
    <onclick>
        RunScript(plugin.program.tvhighlights,"?methode=set_details_to_home&detailurl=$INFO[Window.Property(TVHighlightsToday.1.Popup)]")
    </onclick>


Zusätzliche Methoden welche verwendet werden können:
 
  get_master_elements    (schreibt TVHighlightsToday.Mastermode)
  get_split_elements     (schreibt TVHighlightsToday.Splitmode.*)
  refresh_splitmode      (aktualisiert nur Anzeige, zwecks timeframe,kein unnötiger Abruf von Daten von tvdigital)
  refresh_mastermode     (aktualisiert nur Anzeige, zwecks timeframe,kein unnötiger Abruf von Daten von tvdigital)
  get_mode               (schreibt TVHighlightsToday.Mode)
  getall_tvdigital       (aktualisiert ALLE Kategorien für den Splitmode)
  get_single_tvdigital   (aktualisiert eine Kategorie für den Splitmode (zusätzlich muss watchtype angegeben werden)
  set_splitmode          (schaltet die Mode des Plugins auf splitmode, aktualisiert den Content und setzt alle Properties)
  set_mastermode         (schaltet die Mode des Plugins auf mastermode, aktualisiert den Content und setzt alle Properties)

  in folgender Form: 
      <onclick>
          RunScript(plugin.program.tvhighlights,"?methode=METHODENNAME")
      </onclick>



Prooperties:
============

Mastermode:
-----------
  TVHighlightsToday.<nr>.Title
  TVHighlightsToday.<nr>.Thumb
  TVHighlightsToday.<nr>.Time
  TVHighlightsToday.<nr>.Date
  TVHighlightsToday.<nr>.Channel
  TVHighlightsToday.<nr>.Icon
  TVHighlightsToday.<nr>.Logo
  TVHighlightsToday.<nr>.Genre
  TVHighlightsToday.<nr>.Comment
  TVHighlightsToday.<nr>.Year
  TVHighlightsToday.<nr>.Duration
  TVHighlightsToday.<nr>.Extrainfos
  TVHighlightsToday.<nr>.Popup
  TVHighlightsToday.<nr>.WatchType


Splitmode:
----------
  TV<watchtype>HighlightsToday.<nr>.Title
  TV<watchtype>HighlightsToday.<nr>.Thumb
  TV<watchtype>HighlightsToday.<nr>.Time
  TV<watchtype>HighlightsToday.<nr>.Date
  TV<watchtype>HighlightsToday.<nr>.Channel
  TV<watchtype>HighlightsToday.<nr>.Icon
  TV<watchtype>HighlightsToday.<nr>.Logo
  TV<watchtype>HighlightsToday.<nr>.Genre
  TV<watchtype>HighlightsToday.<nr>.Comment
  TV<watchtype>HighlightsToday.<nr>.Year
  TV<watchtype>HighlightsToday.<nr>.Duration
  TV<watchtype>HighlightsToday.<nr>.Extrainfos
  TV<watchtype>HighlightsToday.<nr>.Popup
  TV<watchtype>HighlightsToday.<nr>.WatchType


Alle Modi:
----------
  TVHighlightsToday.Mode                     (splitmode/mastermode)
  TVHighlightsToday.Splitmode.Spielfilm      (true/false)
  TVHighlightsToday.Splitmode.Sport          (true/false)
  TVHighlightsToday.Splitmode.Unterhaltung   (true/false)
  TVHighlightsToday.Splitmode.Serie          (true/false)
  TVHighlightsToday.Splitmode.Kinder         (true/false)
  TVHighlightsToday.Splitmode.Doku           (true/false)
  TVHighlightsToday.Mastermode               (spielfilm/sport/serie/unterhaltung/doku-und-info/kinder)


Info-Window:
------------
  TVHighlightsToday.Info.Title
  TVHighlightsToday.Info.Picture
  TVHighlightsToday.Info.Subtitle
  TVHighlightsToday.Info.Description
  TVHighlightsToday.Info.Broadcastdetails
  TVHighlightsToday.Info.Genre
  TVHighlightsToday.Info.Channel
  TVHighlightsToday.Info.Logo
  TVHighlightsToday.Info.PVRID
  TVHighlightsToday.Info.StartTime
  TVHighlightsToday.Info.EndTime
  TVHighlightsToday.Info.StartDate
  TVHighlightsToday.Info.RatingType.1
  TVHighlightsToday.Info.Rating.1
  TVHighlightsToday.Info.RatingType.2
  TVHighlightsToday.Info.Rating.2
  TVHighlightsToday.Info.RatingType.3
  TVHighlightsToday.Info.Rating.3
  TVHighlightsToday.Info.RatingType.4
  TVHighlightsToday.Info.Rating.4
  TVHighlightsToday.Info.RatingType.5
  TVHighlightsToday.Info.Rating.5


Debugging:
==========
Für besseres debugging bitte im Plugin in Zeile  von

NODEBUG = True

auf 

NODEBUG = False

ändern. Das kodi.log dann bitte per PN über kodinerds.net zusenden.


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!                                                   ACHTUNG                                                     !!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


Es ist NICHT notwendig Aktualisierungen innerhalb irgendwelcher <onload>`s auszuführen!
Das Plugin verfügt über einen Dienst, welcher sich sowohl um die Content Aktualisierung als auch
um die Aktualisierung der Angezeigten Daten kümmert. Beide Werte sind einstellbar. Hierbei gilt 
dass das das Screen-Refresh Interval kleiner sein muss als das Content-Refresh Interval.
Das Content-Refresh Interval sollte mit Bedacht gewählt werden, siehe hierzu:
http://www.kodinerds.net/index.php/Thread/47201-TEST-RELEASE-TV-Highlights-Grabber-TV-Digital/?postID=271794#post271794


-- That's It , viel Spass damit, TDOe 2015-2016 --
