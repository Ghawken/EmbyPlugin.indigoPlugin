#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

"""
Emby Start Plugin
Authors: See (repo)

Works in combination with FrontViewAPI+ Emby Plugin to display info for
single Emby client.

"""

import datetime
#import simplejson
import time as t
import requests
import urllib.request
import os
import shutil
import sys
import logging

try:
    import indigo
except:
    pass

# Establish default plugin prefs; create them if they don't already exist.
kDefaultPluginPrefs = {
    u'configMenuPollInterval': "300",  # Frequency of refreshes.
    u'configMenuServerTimeout': "15",  # Server timeout limit.
    # u'refreshFreq': 300,  # Device-specific update frequency
    u'showDebugInfo': False,  # Verbose debug logging?
    u'configUpdaterForceUpdate': False,
    u'configUpdaterInterval': 24,
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
        self.prefServerTimeout = int(self.pluginPrefs.get('configMenuServerTimeout', "15"))
        self.configUpdaterInterval = self.pluginPrefs.get('configUpdaterInterval', 24)
        self.configUpdaterForceUpdate = self.pluginPrefs.get('configUpdaterForceUpdate', False)
        self.WaitInterval = 1

        # Convert old debugLevel scale to new scale if needed.
        # =============================================================
        if not isinstance(self.pluginPrefs['showDebugLevel'], int):
            if self.pluginPrefs['showDebugLevel'] == "High":
                self.pluginPrefs['showDebugLevel'] = 3
            elif self.pluginPrefs['showDebugLevel'] == "Medium":
                self.pluginPrefs['showDebugLevel'] = 2
            else:
                self.pluginPrefs['showDebugLevel'] = 1

        self.logger.info(u"")

        self.logger.info("{0:=^130}".format(" Initializing New Plugin Session "))
        self.logger.info("{0:<30} {1}".format("Plugin name:", pluginDisplayName))
        self.logger.info("{0:<30} {1}".format("Plugin version:", pluginVersion))
        self.logger.info("{0:<30} {1}".format("Plugin ID:", pluginId))
        self.logger.info("{0:<30} {1}".format("Indigo version:", indigo.server.version))
        self.logger.info("{0:<30} {1}".format("Python version:", sys.version.replace('\n', '')))
        self.logger.info("{0:<30} {1}".format("Python Directory:", sys.prefix.replace('\n', '')))
        self.logger.info("")
        self.logger.info("{0:=^130}".format(" End of Initializing "))

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
        dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Online")
        self.setStatestonil(dev)

    # Shut 'em down.
    def deviceStopComm(self, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"deviceStopComm() method called.")
        indigo.server.log(u"Stopping Emby device: " + dev.name)
        dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Disabled")

    def runConcurrentThread(self):
        if os.path.exists('/Library/Application Support/Perceptive Automation/images/EmbyPlugin') == 0:
            os.makedirs('/Library/Application Support/Perceptive Automation/images/EmbyPlugin')

        try:
            while True:

                if self.debugLevel >= 2:
                    self.debugLog(u" ")

                for dev in indigo.devices.iter(filter="self"):
                    if self.debugLevel >= 2 and self.debug:
                        self.debugLog(u"MainLoop:  {0}:".format(dev.name))
                    # self.debugLog(len(dev.states))
                    self.refreshDataForDev(dev)

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
        if os.path.exists('/Library/Application Support/Perceptive Automation/images/EmbyPlugin') == 0:
            os.makedirs('/Library/Application Support/Perceptive Automation/images/EmbyPlugin')

        # See if there is a plugin update and whether the user wants to be notified.
        try:
            self.sleep(1)
        except Exception as error:
            self.errorLog(u"Update checker error: {0}".format(error))

    def validatePrefsConfigUi(self, valuesDict):
        if self.debugLevel >= 2:
            self.debugLog(u"validatePrefsConfigUi() method called.")

        error_msg_dict = indigo.Dict()

        # self.errorLog(u"Plugin configuration error: ")

        return True, valuesDict

    def fixErrorState(self, dev):
        self.deviceNeedsUpdated = False
        dev.stateListOrDisplayStateIdChanged()
        update_time = t.strftime("%m/%d/%Y at %H:%M")
        dev.updateStateOnServer('deviceLastUpdated', value=update_time)
        if self.debugLevel >= 2:
            self.debugLog(u"Update Time method called.")
            # dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Offline")

    def getTheData(self, dev):
        """
        The getTheData() method is used to retrieve FrontView API Client Data
        """
        if self.debugLevel >= 2 and self.debug:
            self.debugLog(u"getTheData FrontViewAPI method called.")

        # dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Download")
        try:
            url = 'http://' + dev.pluginProps['sourceXML'] + '/FrontView?api_key='+str(dev.pluginProps['APIKEY'])
            r = requests.get(url,timeout=5)
            result = r.json()
            if self.debugLevel >= 2 and self.debug:
                self.debugLog(f"URL: {url}")
                self.debugLog(u"Result:" + str(result))
            self.WaitInterval = 1
            dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Online")
            dev.setErrorStateOnServer(None)
            # dev.updateStateOnServer('deviceTimestamp', value=t.time())
            return result

        except Exception as error:

            indigo.server.log(u"Error connecting to Device:" + dev.name)
            self.WaitInterval = 60
            if self.debugLevel >= 2  and self.debug:
                self.debugLog(u"Device is offline. No data to return. ")
            dev.updateStateOnServer('deviceIsOnline', value=False, uiValue="Offline")
            # dev.updateStateOnServer('deviceTimestamp', value=t.time())
            dev.setErrorStateOnServer(u'Offline')
            result = ""
            return result

    def remoteCall(self, pluginAction, dev, PlayAction):
        try:
            url = 'http://' + dev.pluginProps['sourceXML'] + '/FrontView/Play/' + PlayAction +'?api_key='+str(dev.pluginProps['APIkey'])
            r = requests.post(url)
        except Exception as error:
            self.errorLog(u"Error RemoteCall:" + str(error))
            return

    def RemotePlay(self, pluginAction, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: " + str(pluginAction))
        self.remoteCall(pluginAction, dev, "Unpause")
        return

    def RemotePlayPause(self, pluginAction, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: " + str(pluginAction))

        if dev.states['playbackState'] == "Playing":
            self.remoteCall(pluginAction, dev, "Pause")
        elif dev.states['playbackState'] == "Paused":
            self.remoteCall(pluginAction, dev, "Unpause")
        return

    def RemotePause(self, pluginAction, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: " + str(pluginAction))
        self.remoteCall(pluginAction, dev, "Pause")
        return

    def RemoteFastForward(self, pluginAction, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: " + str(pluginAction))
        self.remoteCall(pluginAction, dev, "FastForward")
        return

    def RemoteRewind(self, pluginAction, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: " + str(pluginAction))
        self.remoteCall(pluginAction, dev, "Rewind")
        return

    def RemoteStop(self, pluginAction, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: " + str(pluginAction))
        self.remoteCall(pluginAction, dev, "Stop")
        return

    def RemoteNextTrack(self, pluginAction, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: " + str(pluginAction))
        self.remoteCall(pluginAction, dev, "NextTrack")
        return

    def RemotePreviousTrack(self, pluginAction, dev):
        if self.debugLevel >= 2:
            self.debugLog(u"Action Called: " + str(pluginAction))
        self.remoteCall(pluginAction, dev, "PreviousTrack")
        return

    def processArt(self, dev):
        try:
            if self.finalDict['IsPlaying']:
                Thumbvalue = "http://" + dev.pluginProps['sourceXML'] + "/Items/" + self.finalDict[
                    'PrimaryItemId'] + "/Images/Primary"
                Fanartvalue = "http://" + dev.pluginProps['sourceXML'] + "/Items/" + self.finalDict[
                    'PrimaryItemId'] + "/Images/Backdrop"
                Logovalue = "http://" + dev.pluginProps['sourceXML'] + "/Items/" + self.finalDict[
                    'PrimaryItemId'] + "/Images/Logo"
            else:
                Thumbvalue = ""
                Fanartvalue = ""
                Logovalue = ""

            if self.debugLevel >= 2 and self.debug:
                self.debugLog("Thumb Value:" + str(Thumbvalue))
                self.debugLog("Thumb Current State:" + str(dev.states['playbackThumb']))
                self.debugLog("Logo Value:" + str(Logovalue))
                self.debugLog("Logo Current State:" + str(dev.states['playbackLogo']))
            # Check if Thumbvalue changed and make new file

            if str(Thumbvalue) != str(dev.states['playbackThumb']):

                if self.finalDict['IsPlaying']:
                    reqObj = urllib.request.Request(Thumbvalue)
                    fileObj = urllib.request.urlopen(reqObj)
                    localFile = open(
                        "/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Thumbnail_art.png", "wb")
                    localFile.write(fileObj.read())
                    localFile.close()
                    if self.debugLevel >= 2 and self.debug:
                        self.debugLog(u"----- New Thumbail file created -------")
                else:

                    if self.debugLevel >= 2 and self.debug:
                        self.debugLog(u"Nothing is playing - Replacing Thumb Artwork Files")
                    shutil.copy2("embyBlankThumb.png",
                                 "/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Thumbnail_art.png")

            if Fanartvalue != dev.states['playbackFanart']:

                if self.finalDict['IsPlaying']:
                    reqObj = urllib.request.Request(Fanartvalue)
                    fileObj = urllib.request.urlopen(reqObj)
                    localFile = open(
                        "/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Fanart_art.png", "wb")
                    localFile.write(fileObj.read())
                    localFile.close()
                    if self.debugLevel >= 2 and self.debug :
                        self.debugLog(u"------- New Fanart file created ------")
                else:
                    # if nothing playing delete the fanart files (else will continue to show wrong images)
                    # but this option - gives no URL error
                    # need to copy or create a blank png file - use shcopy - done.
                    if self.debugLevel >= 2  and self.debug:
                        self.debugLog(u"Nothing is playing - Replacing Fanart Files")
                    shutil.copy2("embyBlankFanart.png",
                                 "/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Fanart_art.png")
                # hutil.copy2("blank_art.jpg","/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Thumbnail_art.png")
                # os.remove("/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Thumbnail_art.png")
                # os.remove("/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Fanart_art.png")


            if str(Logovalue) != str(dev.states['playbackLogo']):
                try:
                    if self.finalDict['IsPlaying']:
                        reqObj = urllib.request.Request(Logovalue)
                        fileObj = urllib.request.urlopen(reqObj)
                        localFile = open(
                            "/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Logo_art.png", "wb")
                        localFile.write(fileObj.read())
                        localFile.close()
                        if self.debugLevel >= 2 and self.debug:
                            self.debugLog(u"----- New Logo file created -------")
                    else:
                        if self.debugLevel >= 2 and self.debug:
                            self.debugLog(u"Nothing is playing - Replacing Logo Artwork Files")
                        shutil.copy2("embyBlankLogo.png",
                                     "/Library/Application Support/Perceptive Automation/images/EmbyPlugin/Logo_art.png")
                except:
                    if self.debug:
                        self.debugLog(u'Error within Logo - likely no such file')
        except:
            self.debugLog(u"Error within Process Artwork")
        return

    def parseStateValues(self, dev):
        """
        The parseStateValues() method walks through the dict and assigns the
        corresponding value to each device state.
        """
        if self.debugLevel >= 2  and self.debug:
            self.debugLog(u"Saving Values method called.")

        if self.finalDict is not None:
            self.processArt(dev)

        if self.finalDict['IsPlaying']:
            if (self.finalDict['Filename'].endswith('theme.mp3') or self.finalDict['Filename'].endswith('theme.mp4')) and dev.pluginProps['ignoreTheme']:
                self.setStatestonil(dev)
                return
            dev.updateStateOnServer(u"playbackTitle", value=self.finalDict['Title'])
            dev.updateStateOnServer(u"playbackMediatype", value=self.finalDict['MediaType'])
            dev.updateStateOnServer(u"playbackOverview", value=self.finalDict['Overview'])
            dev.updateStateOnServer(u"playbackFilename", value=self.finalDict['Filename'])

            if self.finalDict['TimePosition'] == 0:
                if self.debugLevel >= 2 and self.debug:
                    self.debugLog(u"Time Position Equals 0: Changing to 1.")
                self.finalDict['TimePosition'] = 1

            if self.finalDict['Duration'] > 0:
                duration_seconds = int(self.finalDict['Duration'] / 10000000.00)
            elif self.finalDict['Duration'] == 0:
                if self.debugLevel >= 2 and self.debug:
                    self.debugLog(u"Duraton Position Equals 0: Changing to TimePosition.")
                duration_seconds = int(self.finalDict['TimePosition'] / 10000000.00)

            if duration_seconds == 0:
                duration_seconds = 1
                if self.debugLevel >= 2 and self.debug:
                    self.debugLog(u"Duration_Seconds Equals 0: Changing to 1.")

            duration_time = datetime.timedelta(seconds=duration_seconds)
            dev.updateStateOnServer(u"playbackDuration", value=str(duration_time))

            position_seconds = int(self.finalDict['TimePosition'] / 10000000.00)
            position_time = datetime.timedelta(seconds=position_seconds)
            dev.updateStateOnServer(u"playbackPosition", value=str(position_time))

            percentage = int(position_time.total_seconds() / duration_time.total_seconds() * 100)

            dev.updateStateOnServer(u'playbackPercentage', value=percentage)
            dev.updateStateOnServer(u"playbackThumb",
                                    value="http://" + dev.pluginProps['sourceXML'] + "/Items/" + self.finalDict[
                                        'PrimaryItemId'] + "/Images/Primary")
            dev.updateStateOnServer(u"playbackFanart",
                                    value="http://" + dev.pluginProps['sourceXML'] + "/Items/" + self.finalDict[
                                        'PrimaryItemId'] + "/Images/Backdrop")
            dev.updateStateOnServer(u"playbackLogo",
                                    value="http://" + dev.pluginProps['sourceXML'] + "/Items/" + self.finalDict[
                                        'PrimaryItemId'] + "/Images/Logo")
            if self.finalDict['IsPaused']:
                dev.updateStateOnServer(u"playbackState", value=u"Paused")
                dev.updateStateImageOnServer(indigo.kStateImageSel.AvPaused)
            else:
                dev.updateStateOnServer(u"playbackState", value=u"Playing")
                dev.updateStateImageOnServer(indigo.kStateImageSel.AvPlaying)
        elif dev.states['playbackFilename'] != "":
            if self.debugLevel >= 2 and self.debug:
                self.debugLog(u"Calling Setting States to nil.")
            self.setStatestonil(dev)


        dev.stateListOrDisplayStateIdChanged()
        update_time = t.strftime("%m/%d/%Y at %H:%M")
        dev.updateStateOnServer('deviceLastUpdated', value=update_time)
        # dev.updateStateOnServer('deviceTimestamp', value=t.time())

    def setStatestonil(self, dev):
        if self.debugLevel >= 2 and self.debug:
            self.debugLog(u'setStates to nil run')
        dev.updateStateOnServer(u"playbackState", value=u"False")
        dev.updateStateImageOnServer(indigo.kStateImageSel.AvStopped)
        dev.updateStateOnServer(u"playbackThumb", value="")
        dev.updateStateOnServer(u"playbackFanart", value="")
        dev.updateStateOnServer(u"playbackLogo", value="")
        dev.updateStateOnServer(u"playbackTitle", value="")
        dev.updateStateOnServer(u"playbackFilename", value="")
        dev.updateStateOnServer(u"playbackMediatype", value="")
        dev.updateStateOnServer(u"playbackOverview", value="")
        dev.updateStateOnServer(u"playbackDuration", value="")
        dev.updateStateOnServer(u"playbackPosition", value="")
        dev.updateStateOnServer(u"playbackPercentage", value="")


    def refreshDataAction(self, valuesDict):
        """
        The refreshDataAction() method refreshes data for all devices based on
        a plugin menu call.
        """
        if self.debugLevel >= 2 and self.debug:
            self.debugLog(u"refreshDataAction() method called.")
        self.refreshData()
        return True

    def refreshData(self):
        """
        The refreshData() method controls the updating of all plugin
        devices.
        """
        if self.debugLevel >= 2 and self.debug:
            self.debugLog(u"refreshData() method called.")

        try:
            # Check to see if there have been any devices created.
            if indigo.devices.iter(filter="self"):
                if self.debugLevel >= 2 and self.debug:
                    self.debugLog(u"Updating data...")

                for dev in indigo.devices.iter(filter="self"):
                    self.refreshDataForDev(dev)

            else:
                indigo.server.log(u"No Emby Client devices have been created.")

            return True

        except Exception as error:
            self.errorLog(u"Error refreshing devices. Please check settings.")
            self.errorLog(str(error))
            return False

    def refreshDataForDev(self, dev):

        if dev.configured:
            if self.debugLevel >= 2 and self.debug:
                self.debugLog(u"Found configured device: {0}".format(dev.name))

            if dev.enabled:
                if self.debugLevel >= 2 and self.debug:
                    self.debugLog(u"   {0} is enabled.".format(dev.name))

                # timeDifference = int(t.time()) - int(dev.states['deviceTimestamp'])
                # Change to using Last Updated setting - removing need for deviceTimestamp altogether

                timeDifference = int(t.time() - t.mktime(dev.lastChanged.timetuple()))
                if self.debugLevel >= 1 and self.debug:
                    self.debugLog(dev.name + u": Time Since Device Update = " + str(timeDifference))
                    # self.errorLog(str(dev.lastChanged))
                # Get the data.

                # If device is offline wait for 60 seconds until rechecking
                if dev.states['deviceIsOnline'] == False and timeDifference >= 60:
                    if self.debugLevel >= 2 and self.debug:
                        self.debugLog(u"Offline: Refreshing device: {0}".format(dev.name))
                    self.finalDict = self.getTheData(dev)

                # if device online normal time
                if dev.states['deviceIsOnline']:
                    if self.debugLevel >= 2 and self.debug:
                        self.debugLog(u"Online: Refreshing device: {0}".format(dev.name))
                    self.finalDict = self.getTheData(dev)

                    # Throw the data to the appropriate module to flatten it.
                    # dev.updateStateOnServer('deviceIsOnline', value=True, uiValue="Processing")
                    # self.finalDict = self.rawData

                    # Put the final values into the device states - only if online
                if dev.states['deviceIsOnline']:
                    self.parseStateValues(dev)
            else:
                if self.debugLevel >= 2 and self.debug:
                    self.debugLog(u"    Disabled: {0}".format(dev.name))

    def refreshDataForDevAction(self, valuesDict):
        """
        The refreshDataForDevAction() method refreshes data for a selected device based on
        a plugin menu call.
        """
        if self.debugLevel >= 2 and self.debug:
            self.debugLog(u"refreshDataForDevAction() method called.")

        dev = indigo.devices[valuesDict.deviceId]

        self.refreshDataForDev(dev)
        return True


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
