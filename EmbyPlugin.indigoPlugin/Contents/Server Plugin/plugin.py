#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

"""
Emby Start Plugin
Authors: See (repo)

Works in combination with FrontViewAPI+ Emby Plugin to display info for
single Emby client.
Prefer this method to keep checking regularly
"""


import datetime
import simplejson
import time as t
import requests
import urllib2
import os
import shutil
from ghpu import GitHubPluginUpdater

try:
    import indigo
except:
    pass

# Establish default plugin prefs; create them if they don't already exist.
kDefaultPluginPrefs = {
    u'configMenuPollInterval': "300",  # Frequency of refreshes.
    u'configMenuServerTimeout': "15",  # Server timeout limit.
    u'refreshFreq': 300,  # Device-specific update frequency
    u'showDebugInfo': False,  # Verbose debug logging?
    u'showDebugLevel': "1",  # Low, Medium or High debug output.
    u'updaterEmail': "",  # Email to notify of plugin updates.
    u'updaterEmailsEnabled': False  # Notification of plugin updates wanted.
}


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        self.debugLog(u"Initializing Emby plugin.")

        self.debug = self.pluginPrefs.get('showDebugInfo', False)
        self.debugLevel = self.pluginPrefs.get('showDebugLevel', "1")
        self.deviceNeedsUpdated = ''
        # self.prefPollInterval = int(self.pluginPrefs.get('configMenuPollInterval', "300"))
        self.prefServerTimeout = int(self.pluginPrefs.get('configMenuServerTimeout', "15"))
        self.updater = GitHubPluginUpdater(self)
        self.updaterEmailsEnabled = self.pluginPrefs.get('updaterEmailsEnabled', False)

        # Convert old debugLevel scale to new scale if needed.
        # =============================================================
        if not isinstance(self.pluginPrefs['showDebugLevel'], int):
            if self.pluginPrefs['showDebugLevel'] == "High":
                self.pluginPrefs['showDebugLevel'] = 3
            elif self.pluginPrefs['showDebugLevel'] == "Medium":
                self.pluginPrefs['showDebugLevel'] = 2
            else:
                self.pluginPrefs['showDebugLevel'] = 1

    def __del__(self):
        if self.debugLevel >= 2:
            self.debugLog(u"__del__ method called.")
        indigo.PluginBase.__del__(self)

    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if self.debugLevel >= 2:
            self.debugLog(u"closedPrefsConfigUi() method called.")

        if userCancelled:
            self.debugLog(u"User prefs dialog cancelled.")

        if not userCancelled:
            self.debug = valuesDict.get('showDebugInfo', False)
            self.debugLevel = self.pluginPrefs.get('showDebugLevel', "1")
            self.debugLog(u"User prefs saved.")

            if self.debug:
                indigo.server.log(u"Debugging on (Level: {0})".format(self.debugLevel))
            else:
                indigo.server.log(u"Debugging off.")

            if int(self.pluginPrefs['showDebugLevel']) >= 3:
                self.debugLog(u"valuesDict: {0} ".format(valuesDict))

        return True

    # Start 'em up.
    def deviceStartComm(self, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"deviceStartComm() method called.")
        indigo.server.log(u"Starting Emby device: " + dev.name)
        dev.stateListOrDisplayStateIdChanged()
        dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Enabled")

    # Shut 'em down.
    def deviceStopComm(self, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"deviceStopComm() method called.")
        indigo.server.log(u"Stopping Emby device: " + dev.name)
        dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Disabled")
    def forceUpdate(self):
        self.updater.update(currentVersion='0.0.0')   
    def checkForUpdates(self):
        self.updater.checkForUpdate()
    def updatePlugin(self):
        self.updater.update()            
    def forceUpdate(self):
        self.updater.update(currentVersion='0.0.0')

    def runConcurrentThread(self):
        if self.debugLevel >= 2:
            self.debugLog(u"indigoPluginUpdater() method called.")
        self.updater.checkForUpdate()
        self.sleep(5)
        if os.path.exists ('/Library/Application Support/Perceptive Automation/images/EmbyPlugin') == 0:
            os.makedirs('/Library/Application Support/Perceptive Automation/images/EmbyPlugin')
        try:
            while True:

                # self.debugLog(u" ")
                # self.debugLog(u" ")
                # self.debugLog(u" ")
                if self.debugLevel >= 2:
                    self.debugLog(u" ")

                for dev in indigo.devices.itervalues(filter="self"):
                    if self.debugLevel >= 2:
                        self.debugLog(u"{0}:".format(dev.name))
                    # self.debugLog(len(dev.states))
                    self.refreshDataForDev(dev)
                else:
                    self.fixErrorState(dev)
                self.sleep(1)

        except self.StopThread:
            self.debugLog(u'Restarting/or error. Stopping Emby thread.')
            pass

    def shutdown(self):
        if self.debugLevel >= 2:
            self.debugLog(u"shutdown() method called.")

    def startup(self):
        if self.debugLevel >= 2:
            self.debugLog(u"Starting EmbyPlugin. startup() method called.")
        if os.path.exists ('/Library/Application Support/Perceptive Automation/images/EmbyPlugin') == 0:
            os.makedirs('/Library/Application Support/Perceptive Automation/images/EmbyPlugin')
        
        # See if there is a plugin update and whether the user wants to be notified.
        try:
            self.updater.checkForUpdate()
        except Exception as error:
            self.errorLog(u"Update checker error: {0}".format(error))

    def validatePrefsConfigUi(self, valuesDict):
        if self.debugLevel >= 2:
            self.debugLog(u"validatePrefsConfigUi() method called.")

        error_msg_dict = indigo.Dict()
        update_email = valuesDict['updaterEmail']
        update_wanted = valuesDict['updaterEmailsEnabled']

        # Test plugin update notification settings.
        try:
            if update_wanted and not update_email:
                error_msg_dict['updaterEmail'] = u"If you want to be notified of updates, you must supply an email address."
                return False, valuesDict, error_msg_dict

            elif update_wanted and "@" not in update_email:
                error_msg_dict['updaterEmail'] = u"Valid email addresses have at least one @ symbol in them (foo@bar.com)."

                return False, valuesDict, error_msg_dict

        except Exception as error:
            self.errorLog(u"Plugin configuration error: {0}".format(error))

        return True, valuesDict

    def checkVersionNow(self):
        """
        The checkVersionNow() method is called if user selects "Check For
        Plugin Updates..." Indigo menu item.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"checkVersionNow() method called.")
        try:
            self.updater.checkVersionPoll()
        except Exception as error:
            self.errorLog(u"Update checker error: {0}".format(error))

    def fixErrorState(self, dev):
        self.deviceNeedsUpdated = False
        dev.stateListOrDisplayStateIdChanged()
        update_time = t.strftime("%m/%d/%Y at %H:%M")
        dev.updateStateOnServer('deviceLastUpdated', value=update_time)
        dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Online")


    def getTheData(self, dev):
        """
        The getTheData() method is used to retrieve target data files.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"getTheData() method called.")

        dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Download")
        try:
            # Initiate curl call to data source.
            url = 'http://'+dev.pluginProps['sourceXML']+'/FrontView'
            r = requests.get(url)
            result = r.json()
            if self.debugLevel >= 2:
                self.debugLog(u"Result:"+unicode(result))
            return result

        except Exception as error:

            self.errorLog(u"{0} - Error getting source data: {1}. Skipping until next scheduled poll.".format(dev.name, unicode(error)))
            
            if self.debugLevel >= 2:
                self.debugLog(u"Device is offline. No data to return. Returning dummy dict.")
            dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="No comm")
            result = ""
            return result
    
    def remoteCall(self,pluginAction,dev,PlayAction):
        try:
            url = 'http://'+dev.pluginProps['sourceXML']+'/FrontView/Play/'+PlayAction
            r = requests.post(url)
        except Exception as error:
            self.errorLog(u"Error RemoteCall:"+unicode(error))
            return
        
    
    def RemotePlay(self, pluginAction,dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: "+unicode(pluginAction))
        self.remoteCall(pluginAction,dev,"Unpause")
        return
    def RemotePause(self, pluginAction,dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: "+unicode(pluginAction))
        self.remoteCall(pluginAction,dev,"Pause")
        return   
    def RemoteFastForward(self, pluginAction,dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: "+unicode(pluginAction))
        self.remoteCall(pluginAction,dev,"FastForward")
        return   
    def RemoteRewind(self, pluginAction,dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: "+unicode(pluginAction))
        self.remoteCall(pluginAction,dev,"Rewind")
        return 
    def RemoteStop(self, pluginAction,dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: "+unicode(pluginAction))
        self.remoteCall(pluginAction,dev,"Stop")
        return  
    def RemoteNextTrack(self, pluginAction,dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: "+unicode(pluginAction))
        self.remoteCall(pluginAction,dev,"NextTrack")
        return 
    def RemotePreviousTrack(self, pluginAction,dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: "+unicode(pluginAction))
        self.remoteCall(pluginAction,dev,"PreviousTrack")
        return         
    def processArt(self, dev):
        
        if self.finalDict['IsPlaying']:
            Thumbvalue="http://"+dev.pluginProps['sourceXML']+"/Items/"+self.finalDict['BackdropItemId']+"/Images/Primary"
            Fanartvalue= "http://"+dev.pluginProps['sourceXML']+"/Items/"+self.finalDict['BackdropItemId']+"/Images/Backdrop"
        else:
            Thumbvalue=""
            Fanartvalue=""
        if self.debugLevel >= 2:
            self.debugLog("Thumb Value:"+str(Thumbvalue))
            self.debugLog("Thumb Current State:"+str(dev.states['playbackThumb']))
        
        #Check if Thumbvalue changed and make new file
    
        if str(Thumbvalue) != str(dev.states['playbackThumb']):
            
            if self.finalDict['IsPlaying']:
                reqObj = urllib2.Request(Thumbvalue)
                fileObj = urllib2.urlopen(reqObj)
                localFile = open("/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Thumbnail_art.png", "wb")
                localFile.write(fileObj.read())
                localFile.close()
                if self.debugLevel >= 2:
                    self.debugLog(u"New Thumbail file created")
            else:
                
                if self.debugLevel >= 2:
                    self.debugLog(u"Nothing is playing - Replacing Thumb Artwork Files")
                shutil.copy2("blank_art.jpg","/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Thumbnail_art.png")
        
        if Fanartvalue != dev.states['playbackFanart']:
            if self.finalDict['IsPlaying']:  
                reqObj = urllib2.Request(Fanartvalue)
                fileObj = urllib2.urlopen(reqObj)
                localFile = open("/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Fanart_art.png", "wb")
                localFile.write(fileObj.read())
                localFile.close()
                if self.debugLevel >= 2:
                    self.debugLog(u"New Fanart file created")
            else:
             # if nothing playing delete the fanart files (else will continue to show wrong images)
            # but this option - gives no URL error
            # need to copy or create a blank png file - use shcopy - done.
                if self.debugLevel >= 2:
                    self.debugLog(u"Nothing is playing - Replacing Fanart Files")
                shutil.copy2("blank_art.jpg","/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Fanart_art.png")
                #hutil.copy2("blank_art.jpg","/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Thumbnail_art.png")
                #os.remove("/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Thumbnail_art.png")
                #os.remove("/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Fanart_art.png")

        return
        

    def parseStateValues(self, dev):
        """
        The parseStateValues() method walks through the dict and assigns the
        corresponding value to each device state.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"parseStateValues() method called.")
            self.debugLog(u"Writing device states:")
        
        self.processArt(dev)
        
        if self.finalDict['IsPlaying']:
            dev.updateStateOnServer(u"playbackTitle", value=self.finalDict['Title'])
            dev.updateStateOnServer(u"playbackMediatype", value=self.finalDict['MediaType'])
            dev.updateStateOnServer(u"playbackOverview", value=self.finalDict['Overview'])
            dev.updateStateOnServer(u"playbackFilename", value=self.finalDict['Filename'])
            
            duration_seconds = int(self.finalDict['Duration']/10000000.00)
            duration_time = datetime.timedelta(seconds = duration_seconds)
            
            dev.updateStateOnServer(u"playbackDuration", value=str(duration_time))
            
            position_seconds = int(self.finalDict['TimePosition']/10000000.00)
            position_time = datetime.timedelta(seconds = position_seconds)         
            dev.updateStateOnServer(u"playbackPosition", value=str(position_time))
                        
            dev.updateStateOnServer(u"playbackThumb", value="http://"+dev.pluginProps['sourceXML']+"/Items/"+self.finalDict['BackdropItemId']+"/Images/Primary")
            dev.updateStateOnServer(u"playbackFanart", value="http://"+dev.pluginProps['sourceXML']+"/Items/"+self.finalDict['BackdropItemId']+"/Images/Backdrop")
            

            
            if self.finalDict['IsPaused']:
                dev.updateStateOnServer(u"playbackState", value=u"Paused")
                dev.updateStateImageOnServer(indigo.kStateImageSel.AvPaused)
            else:
                dev.updateStateOnServer(u"playbackState", value=u"Playing")
                dev.updateStateImageOnServer(indigo.kStateImageSel.AvPlaying)
        else:
            dev.updateStateOnServer(u"playbackState", value=u"False")
            dev.updateStateImageOnServer(indigo.kStateImageSel.AvStopped)  
            dev.updateStateOnServer(u"playbackThumb", value="")
            dev.updateStateOnServer(u"playbackFanart", value="")                                     
            dev.updateStateOnServer(u"playbackTitle", value="")
            dev.updateStateOnServer(u"playbackFilename", value="")
            dev.updateStateOnServer(u"playbackMediatype", value="")
            dev.updateStateOnServer(u"playbackOverview", value="")
            dev.updateStateOnServer(u"playbackDuration", value="")
            dev.updateStateOnServer(u"playbackPosition", value="")
            
    def refreshDataAction(self, valuesDict):
        """
        The refreshDataAction() method refreshes data for all devices based on
        a plugin menu call.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataAction() method called.")
        self.refreshData()
        return True

    def refreshData(self):
        """
        The refreshData() method controls the updating of all plugin
        devices.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshData() method called.")

        try:
            # Check to see if there have been any devices created.
            if indigo.devices.itervalues(filter="self"):
                if self.debugLevel >= 2:
                    self.debugLog(u"Updating data...")

                for dev in indigo.devices.itervalues(filter="self"):
                    self.refreshDataForDev(dev)

            else:
                indigo.server.log(u"No Emby Client devices have been created.")

            return True

        except Exception as error:
            self.errorLog(u"Error refreshing devices. Please check settings.")
            self.errorLog(unicode(error))
            return False

    def refreshDataForDev(self, dev):

        if dev.configured:
            if self.debugLevel >= 2:
                self.debugLog(u"Found configured device: {0}".format(dev.name))

            if dev.enabled:
                if self.debugLevel >= 2:
                    self.debugLog(u"   {0} is enabled.".format(dev.name))

                # Get the data.
                if self.debugLevel >= 2:
                    self.debugLog(u"Refreshing device: {0}".format(dev.name))
                self.rawData = self.getTheData(dev)

                # Throw the data to the appropriate module to flatten it.
                dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Processing")

                self.finalDict = self.rawData

                    # Put the final values into the device states.
                self.parseStateValues(dev)
            else:
                if self.debugLevel >= 2:
                    self.debugLog(u"    Disabled: {0}".format(dev.name))

    def refreshDataForDevAction(self, valuesDict):
        """
        The refreshDataForDevAction() method refreshes data for a selected device based on
        a plugin menu call.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"refreshDataForDevAction() method called.")

        dev = indigo.devices[valuesDict.deviceId]

        self.refreshDataForDev(dev)
        return True

    def stopSleep(self, start_sleep):
        """
        The stopSleep() method accounts for changes to the user upload interval
        preference. The plugin checks every 2 seconds to see if the sleep
        interval should be updated.
        """
        try:
            total_sleep = float(self.pluginPrefs.get('configMenuUploadInterval', 300))
        except:
            total_sleep = iTimer  # TODO: Note variable iTimer is an unresolved reference.
        if t.time() - start_sleep > total_sleep:
            return True
        return False


    def toggleDebugEnabled(self):
        """
        Toggle debug on/off.
        """
        if self.debugLevel >= 2:
            self.debugLog(u"toggleDebugEnabled() method called.")
        if not self.debug:
            self.debug = True
            self.pluginPrefs['showDebugInfo'] = True
            indigo.server.log(u"Debugging on.")
            self.debugLog(u"Debug level: {0}".format(self.debugLevel))

        else:
            self.debug = False
            self.pluginPrefs['showDebugInfo'] = False
            indigo.server.log(u"Debugging off.")
