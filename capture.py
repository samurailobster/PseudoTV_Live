#   Copyright (C) 2015 Kevin S. Graer
#
#
# This file is part of PseudoTV Live.
#
# PseudoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV Live.  If not, see <http://www.gnu.org/licenses/>.

import xbmc, xbmcgui, xbmcaddon
import sys, os

from urllib import unquote
from xml.dom.minidom import parse, parseString
from resources.lib.utils import *
from resources.lib.Globals import *
from resources.lib.ChannelList import ChannelList
from resources.lib.FileAccess import FileAccess

class Main:

    def __init__(self):
        self._parse_argv()
    
    
    def log(self, msg, level = xbmc.LOGDEBUG):
        log('capture: ' + msg, level)


    def _parse_argv(self):
        self.handle = None
        self.infos = []
        self.params = {" Label": None,
                       " Path": None,
                       " FileName": None,
                       " DBIDType": None,
                       " AddonName": None,
                       " AddonType": None,
                       " Description": None,
                       " isPlayable": None,
                       " isFolder": None}
        for arg in sys.argv:
            if arg == 'script.pseudotv.live':
                continue
            param = (arg.replace('"', '').replace("'", " ").replace("[ ", " ").replace(" ]", " ").replace("' ", "'").replace(" ' ", "'"))
            try:
                self.params[param.split("=")[0]] = "=".join(param.split("=")[1:]).strip()
            except:
                pass
                
        self.log("params = " + str(self.params))
        self.Label = self.params[" Label"] = self.params.get(" Label", "").strip()
        self.Path = self.params[" Path"] = self.params.get(" Path", "").strip()
        self.FileName = self.params[" FileName"] = self.params.get(" FileName", "").strip()
        self.DBIDType = self.params[" DBIDType"] = self.params.get(" DBIDType", "").strip()
        self.AddonName = self.params[" AddonName"] = self.params.get(" AddonName", "").strip()
        self.AddonType = self.params[" AddonType"] = self.params.get(" AddonType", "").strip()
        
        try:
            self.Description = self.params[" Description"] = self.params.get(" Description", "").strip()
        except:
            self.Description = self.params[" Description"] = self.params.get("Description", "").strip()
        
        self.isPlayable = self.params[" isPlayable"] = self.params.get(" isPlayable", "").strip()
        self.isFolder = self.params[" isFolder"] = self.params.get(" isFolder", "").strip()
        
        if self.AddonName:
            ADDON = xbmcaddon.Addon(id=self.AddonName)
            ADDON_ID = ADDON.getAddonInfo('id')
            self.AddonName = ADDON.getAddonInfo('name')
        self.chnlst = ChannelList()
        self.Label = self.chnlst.cleanLabels(self.Label)
        self.Description  = self.chnlst.cleanLabels(self.Description)
        self.AddonName = self.chnlst.cleanLabels(self.AddonName)
        self.ImportChannel()
        
        
    def ImportChannel(self):
        self.log("ImportChannel")
        show_busy_dialog()
        self.chnlst = ChannelList()
        self.chantype = 9999
        self.setting1 = ''
        self.setting2 = ''
        self.setting3 = ''
        self.setting4 = ''
        self.channame = ''
        self.theitem = []
        self.itemlst = []
        ADDON_SETTINGS.loadSettings()
        
        for i in range(999):
            self.theitem.append(str(i + 1))
        self.updateListing()
        hide_busy_dialog()
        available = False
        try:
            Lastchan = int(getProperty("PTVL.CM.LASTCHAN"))
            self.log("ImportChannel, Lastchan = " + str(Lastchan))
            self.nitemlst = self.itemlst
            self.itemlst = self.nitemlst[Lastchan:] + self.nitemlst[:Lastchan]
        except:
            pass
        while not available:
            select = selectDialog(self.itemlst, 'Select Channel Number')
            if select != -1:
                # self.channel = select + 1
                self.channel = int(self.chnlst.cleanLabels((self.itemlst[select]).split(' - ')[0]))
                if not (self.itemlst[select]).startswith('[COLOR=dimgrey]'):
                    available = True
                    
                    if self.Path[-3:].lower() == 'xsp':
                        self.chantype = 0
                    elif self.Path.lower().startswith('plugin://plugin.video.youtube/channel/'):
                        self.chantype = 10
                        self.YTtype = 1
                    elif self.Path.lower().startswith(('plugin://plugin.video.youtube/playlist/','plugin://plugin.video.spotitube/?limit&mode=listyoutubeplaylist')):
                        self.chantype = 10
                        self.YTtype = 2
                    elif self.Path.lower().startswith(('plugin', 'http', 'rtmp', 'pvr', 'hdhomerun', 'upnp')):
                        if self.isPlayable == 'True':
                            if dlg.yesno("PseudoTV Live", 'Add source as', yeslabel="LiveTV", nolabel="InternetTV"):
                                self.chantype = 8
                            else:
                                self.chantype = 9
                        else:
                            if self.Path.lower().startswith(('pvr')):
                                self.chantype = 8
                            elif self.isFolder == 'True' and self.Path.lower().startswith(('plugin')):
                                self.chantype = 15
                            elif self.isFolder == 'True' and self.Path.lower().startswith(('upnp')):
                                self.chantype = 16
                    elif self.isFolder == 'True':
                        if self.DBIDType == 'tvshow':
                            self.chantype = 6
                        elif self.DBIDType == '':
                            self.chantype = 7                        
                    self.buildChannel()
                else:
                    xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % ("PseudoTV Live", "Channel "+str(self.channel)+" already in use", 1000, THUMB) )
            else:
                available = True
            
            
    def buildChannel(self):
        self.log("buildChannel, chantype = " + str(self.chantype))
        self.chnlst = ChannelList()
        self.addonDirectoryPath = []
        
        if self.chantype == 0:
            self.setting1 = xbmc.translatePath(self.Path)
            self.channame = self.getSmartPlaylistName(self.Path)
        elif self.chantype == 6:
            self.setting1 = self.Label
            self.setting2 = '4'
            self.channame = self.Label
            
        elif self.chantype == 7:
            self.setting1 = xbmc.translatePath(self.Path)
            self.setting3 = str(MEDIA_LIMIT)
            self.setting4 = '0'
            self.channame = self.Label
            
        elif self.chantype == 8: 
            xmltvFle = xmltvFile(listXMLTV())
            if self.Path.startswith('plugin://plugin.video.ustvnow'):
                self.Label = self.Label.split(' - ')[0]
                dname = "USTVnow - "+self.Label
            else:
                dname = self.Label

            self.channame, self.setting1 = self.chnlst.findZap2itID(dname, xmltvFle)
            self.channame = self.Label+" USTV"
            self.setting2 = self.Path
                
        elif self.chantype == 9:
            self.setting1 = '5400'
            self.setting2 = self.Path
            self.setting3 = self.Label
            self.setting4 = self.Description
            self.channame = self.Label +' - '+ self.AddonName
            
        elif self.chantype == 10:
            if self.YTtype == 1:
                self.setting1 = ((self.Path).replace('plugin://plugin.video.youtube/channel/','')).replace('/','')
            elif self.YTtype == 2:
                self.setting1 = ((self.Path).replace('plugin://plugin.video.','').replace('youtube/playlist/','').replace('spotitube/?limit&mode=listyoutubeplaylist&type=browse&url=','')).replace('/','')

            self.setting2 = str(self.YTtype)
            self.setting3 = str(MEDIA_LIMIT)
            self.setting4 = '0'
            self.channame = self.Label
            
        elif self.chantype == 15:
            self.setting1 = self.Path
            self.setting2 = ''
            self.setting3 = str(MEDIA_LIMIT)
            self.setting4 = '0'
            self.channame = self.Label +' - '+ self.AddonName
            
        self.saveSettings()
        if dlg.yesno("PseudoTV Live", 'Channel Successfully Added', 'Open Channel Manager?'):
            xbmc.executebuiltin("RunScript("+ADDON_PATH+"/config.py, %s)" %str(self.channel))
                
        
    def updateListing(self, channel = -1):
        self.log("updateListing")
        start = 0
        end = 999

        if channel > -1:
            start = channel - 1
            end = channel

        for i in range(start, end):
            try:
                theitem = self.theitem[i]
                chantype = 9999
                chansetting1 = ''
                chansetting2 = ''
                chansetting3 = ''
                chansetting4 = ''
                channame = ''
                newlabel = ''

                try:
                    chantype = int(ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_type"))
                    chansetting1 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_1")
                    chansetting2 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_2")
                    chansetting3 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_3")
                    chansetting4 = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_4")
                    channame = ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_rule_1_opt_1")
                except:
                    pass

                if chantype == 0:
                    newlabel = self.getSmartPlaylistName(chansetting1)
                elif chantype == 1 or chantype == 2 or chantype == 5 or chantype == 6:
                    newlabel = chansetting1
                elif chantype == 3:
                    newlabel = chansetting1 + " - TV"
                elif chantype == 4:
                    newlabel = chansetting1 + " - Movies"
                elif chantype == 7:
                    if chansetting1[-1] == '/' or chansetting1[-1] == '\\':
                        newlabel = os.path.split(chansetting1[:-1])[1]
                    else:
                        newlabel = os.path.split(chansetting1)[1]
                elif chantype == 8:
                    newlabel = channame + " - LiveTV"
                elif chantype == 9:
                    newlabel = channame + " - InternetTV"
                elif chantype == 10:
                    newlabel = channame + " - Youtube"            
                elif chantype == 11:
                    newlabel = channame + " - RSS"            
                elif chantype == 12:
                    newlabel = channame + " - Music"
                elif chantype == 13:
                    newlabel = channame + " - Music Videos"
                elif chantype == 14:
                    newlabel = channame + " - Exclusive"
                elif chantype == 15:
                    newlabel = channame + " - Plugin"
                elif chantype == 16:
                    newlabel = channame + " - UPNP"
                if newlabel:
                    newlabel = '[COLOR=dimgrey][B]'+ theitem +'[/B] - '+ newlabel+'[/COLOR]'
                else:
                    newlabel = '[COLOR=blue][B]'+theitem+'[/B][/COLOR]'
                self.itemlst.append(newlabel)
            except:
                pass
        self.log("updateListing return")
             
             
    def getSmartPlaylistName(self, fle):
        self.log("getSmartPlaylistName " + fle)
        fle = xbmc.translatePath(fle)

        try:
            xml = FileAccess.open(fle, "r")
        except:
            self.log('Unable to open smart playlist')
            return ''

        try:
            dom = parse(xml)
        except:
            xml.close()
            self.log("getSmartPlaylistName return unable to parse")
            return ''

        xml.close()

        try:
            plname = dom.getElementsByTagName('name')
            self.log("getSmartPlaylistName return " + plname[0].childNodes[0].nodeValue)
            return plname[0].childNodes[0].nodeValue
        except:
            self.playlist('Unable to find element name')

        self.log("getSmartPlaylistName return")


    def saveSettings(self):
        self.log("saveSettings channel " + str(self.channel))
        chantype = 9999
        chan = str(self.channel)
        setProperty("PTVL.CM.LASTCHAN",chan)

        chantype = "Channel_" + chan + "_type"
        setting1 = "Channel_" + chan + "_1"
        setting2 = "Channel_" + chan + "_2"
        setting3 = "Channel_" + chan + "_3"
        setting4 = "Channel_" + chan + "_4"

        ADDON_SETTINGS.setSetting(chantype, str(self.chantype))
        ADDON_SETTINGS.setSetting(setting1, self.setting1)
        ADDON_SETTINGS.setSetting(setting2, self.setting2)
        ADDON_SETTINGS.setSetting(setting3, self.setting3)
        ADDON_SETTINGS.setSetting(setting4, self.setting4)
        ADDON_SETTINGS.setSetting(setting4, self.setting4)
        ADDON_SETTINGS.setSetting("Channel_" + chan + "_rulecount", "1")
        ADDON_SETTINGS.setSetting("Channel_" + chan + "_rule_1_id", "1")
        ADDON_SETTINGS.setSetting("Channel_" + chan + "_rule_1_opt_1", self.channame)      
        ADDON_SETTINGS.setSetting("Channel_" + chan + "_changed", "True")
        self.log("saveSettings return")
                
if (__name__ == "__main__"):
    Main()
xbmc.log('PseudoTV Live Export Finished')
