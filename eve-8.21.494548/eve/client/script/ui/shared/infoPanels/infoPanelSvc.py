#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/infoPanels/infoPanelSvc.py
import service
import infoPanel
import uicls
import uiconst
import collections
import uthread
import blue
import uiutil
import util
import localization
import crimewatchTimers
import log
from infoPanel import PANEL_LOCATION_INFO, PANEL_ROUTE, PANEL_MISSIONS, PANEL_INCURSIONS, PANEL_FACTIONAL_WARFARE, PANEL_PLANETARY_INTERACTION
from infoPanel import MODE_COLLAPSED, MODE_COMPACT, MODE_NORMAL

class InfoPanelSvc(service.Service):
    __update_on_reload__ = 1
    __guid__ = 'svc.infoPanel'
    __notifyevents__ = ['OnSessionChanged',
     'OnViewStateChanged',
     'OnAgentMissionChange',
     'OnSovereigntyChanged',
     'OnSystemStatusChanged',
     'OnEntitySelectionChanged',
     'OnPostCfgDataChanged']

    def Run(self, *args):
        self.sidePanel = None
        self.infoPanelContainer = None
        self.sessionTimer = None
        self.sessionTimerUpdatePending = False

    def Reload(self):
        if self.sidePanel:
            self.sidePanel.Close()
        if self.sessionTimer:
            self.sessionTimer.Close()
        self.ConstructSidePanel()

    def ConstructSidePanel(self):
        self.sidePanel = uicls.Container(parent=uicore.layer.sidePanels, name='sidePanel', align=uiconst.TOLEFT, width=infoPanel.PANELWIDTH, padding=(0, 12, 0, 0))
        self.sidePanel.cacheContents = True
        self.combatTimerContainer = crimewatchTimers.TimerContainer(parent=self.sidePanel, left=infoPanel.LEFTPAD)
        self.infoPanelContainer = uicls.InfoPanelContainer(parent=self.sidePanel, align=uiconst.TOTOP)
        self.sessionTimer = uicls.SessionTimeIndicator(parent=self.sidePanel, pos=(16, 35, 24, 24), state=uiconst.UI_HIDDEN, align=uiconst.TOPLEFT)
        if self.sessionTimerUpdatePending:
            self.UpdateSessionTimer()

    def UpdateSessionTimer(self):
        if settings.user.ui.Get('showSessionTimer', 0):
            if self.sessionTimer:
                uthread.new(self.sessionTimer.AnimSessionChange)
                self.sessionTimerUpdatePending = False
            else:
                self.sessionTimerUpdatePending = True

    def ShowHideSidePanel(self, hide = 1, *args):
        if self.sidePanel is not None and not self.sidePanel.destroyed:
            if hide:
                self.sidePanel.state = uiconst.UI_HIDDEN
            else:
                self.sidePanel.state = uiconst.UI_PICKCHILDREN

    def GetCurrentPanelClasses(self):
        panelSettings = self.GetPanelModeSettings()
        ret = []
        for panel in panelSettings:
            cls = self.GetPanelClassByPanelTypeID(panel[0])
            if cls.IsAvailable():
                ret.append(cls)

        return ret

    def GetCurrentPanelTypes(self):
        return [ panel.panelTypeID for panel in self.GetCurrentPanelClasses() ]

    def GetPanelClassByPanelTypeID(self, panelTypeID):
        if panelTypeID == PANEL_LOCATION_INFO:
            return uicls.InfoPanelLocationInfo
        if panelTypeID == PANEL_ROUTE:
            return uicls.InfoPanelRoute
        if panelTypeID == PANEL_INCURSIONS:
            return uicls.InfoPanelIncursions
        if panelTypeID == PANEL_MISSIONS:
            return uicls.InfoPanelMissions
        if panelTypeID == PANEL_FACTIONAL_WARFARE:
            return uicls.InfoPanelFactionalWarfare
        if panelTypeID == PANEL_PLANETARY_INTERACTION:
            return uicls.InfoPanelPlanetaryInteraction

    def GetModeForPanel(self, panelTypeID):
        panelSettings = self.GetPanelModeSettings()
        settingsEntry = self.GetPanelSettingsEntryByTypeID(panelTypeID)
        if settingsEntry:
            return settingsEntry[1]
        cls = self.GetPanelClassByPanelTypeID(panelTypeID)
        return cls.default_mode

    def GetPanelSettingsEntryByTypeID(self, panelTypeID):
        panelSettings = self.GetPanelModeSettings()
        for settingsEntry in panelSettings:
            if settingsEntry[0] == panelTypeID:
                return settingsEntry

    def GetPanelModeSettings(self):
        panels = settings.char.ui.Get(self.GetCurrentPanelSettingsID(), self.GetCurrentDefaultPanelSettings())
        panels = [ panel for panel in panels if panel[0] in infoPanel.PANELTYPES ]
        panelTypeIDs = [ panel[0] for panel in panels ]
        for panelTypeID in infoPanel.PANELTYPES:
            if panelTypeID not in panelTypeIDs:
                cls = self.GetPanelClassByPanelTypeID(panelTypeID)
                panels.append([panelTypeID, cls.default_mode])

        return panels

    def SavePanelModeSetting(self, panelTypeID, mode):
        panelSettings = self.GetPanelModeSettings()
        panelSettingsEntry = self.GetPanelSettingsEntryByTypeID(panelTypeID)
        panelSettingsEntry[1] = mode
        settings.char.ui.Set(self.GetCurrentPanelSettingsID(), panelSettings)
        sm.ScatterEvent('OnInfoPanelSettingChanged', panelTypeID, mode)

    def GetCurrentPanelSettingsID(self):
        currViewName = sm.GetService('viewState').GetCurrentView().name
        return 'InfoPanelModes_%s' % currViewName

    def GetCurrentDefaultPanelSettings(self):
        currViewName = sm.GetService('viewState').GetCurrentView().name
        if currViewName == 'planet':
            return [[PANEL_LOCATION_INFO, MODE_COMPACT], [PANEL_PLANETARY_INTERACTION, MODE_NORMAL]]
        elif currViewName in ('starmap', 'systemmap'):
            return [[PANEL_LOCATION_INFO, MODE_NORMAL], [PANEL_ROUTE, MODE_NORMAL]]
        else:
            if currViewName not in ('hangar', 'station', 'inflight'):
                log.LogWarn('InfoPanelSvc.GetCurrentDefaultPanelSettings: Unhandled viewstate: %s' % currViewName)
            return [[PANEL_LOCATION_INFO, MODE_NORMAL],
             [PANEL_ROUTE, MODE_NORMAL],
             [PANEL_INCURSIONS, MODE_NORMAL],
             [PANEL_MISSIONS, MODE_NORMAL],
             [PANEL_FACTIONAL_WARFARE, MODE_NORMAL]]

    def CheckAllPanelsFit(self, triggeredByPanel = None):
        if self.infoPanelContainer:
            uthread.new(self._CheckAllPanelsFit, triggeredByPanel)

    def _CheckAllPanelsFit(self, triggeredByPanel = None):
        panels = self.GetPanelModeSettings()[:]
        panels.reverse()
        numPanels = len(self.GetCurrentPanelClasses())
        for mode in (MODE_COMPACT, MODE_COLLAPSED):
            for panelTypeID, panelMode in panels:
                if panelMode == MODE_COLLAPSED:
                    continue
                if not self.infoPanelContainer.IsLastPanelClipped():
                    return
                if panelTypeID == triggeredByPanel:
                    continue
                panel = self.GetPanelByTypeID(panelTypeID)
                if panel:
                    panel.SetMode(mode)

    def MovePanelInFrontOf(self, infoPanelCls, oldTypeID = None):
        panelSettings = self.GetPanelModeSettings()
        entry = self.GetPanelSettingsEntryByTypeID(infoPanelCls.panelTypeID)
        if oldTypeID:
            idx = panelSettings.index(self.GetPanelSettingsEntryByTypeID(oldTypeID))
        else:
            idx = -1
        oldIdx = panelSettings.index(self.GetPanelSettingsEntryByTypeID(infoPanelCls.panelTypeID))
        if idx > oldIdx:
            idx -= 1
        if oldIdx == idx:
            return
        panelSettings = self.GetPanelModeSettings()
        panelSettings.pop(oldIdx)
        panelSettings.insert(idx, entry)
        settings.char.ui.Set(self.GetCurrentPanelSettingsID(), panelSettings)
        self.ReconstructAllPanels(animate=True)

    def GetPanelByTypeID(self, panelTypeID):
        if self.infoPanelContainer:
            return self.infoPanelContainer.GetPanelByTypeID(panelTypeID)

    def GetPanelButtonByTypeID(self, panelTypeID):
        if self.infoPanelContainer:
            return self.infoPanelContainer.GetPanelButtonByTypeID(panelTypeID)

    def OnPanelContainerIconPressed(self, panelTypeID):
        panel = self.GetPanelByTypeID(panelTypeID)
        if panel:
            if panel.isInModeTransition:
                return
            if panel.mode == MODE_COLLAPSED:
                panel.SetMode(MODE_NORMAL)
            elif panel.isCollapsable:
                panel.SetMode(MODE_COLLAPSED)
            elif panel.mode == MODE_NORMAL:
                panel.SetMode(MODE_COMPACT)
            else:
                panel.SetMode(MODE_NORMAL)

    def OnViewStateChanged(self, oldView, newView):
        if not session.charid:
            return
        if not self.sidePanel:
            self.ConstructSidePanel()
        else:
            self.ReconstructAllPanels()

    def ReconstructAllPanels(self, animate = False):
        if not session.charid:
            return
        if not self.sidePanel:
            self.ConstructSidePanel()
        elif self.infoPanelContainer:
            self.infoPanelContainer.Reconstruct(animate)
        self.CheckAllPanelsFit()

    def UpdateAllPanels(self):
        if not session.charid or not self.sidePanel:
            return
        sm.ChainEvent('ProcessUpdateInfoPanel', None)

    def UpdateTopIcons(self):
        if self.infoPanelContainer:
            self.infoPanelContainer.ConstructTopIcons()

    def OnAgentMissionChange(self, what, agentID, tutorialID = None, *args):
        self.UpdateMissionsPanel()

    def OnSessionChanged(self, isRemote, sess, change):
        if not session.charid:
            return
        self.UpdateMissionsPanel()
        self.UpdateSessionTimer()

    def OnSovereigntyChanged(self, solarSystemID, allianceID):
        self.UpdateAllPanels()

    def OnSystemStatusChanged(self, *args):
        self.UpdateAllPanels()

    def OnEntitySelectionChanged(self, entityID):
        self.UpdateAllPanels()

    def OnPostCfgDataChanged(self, what, data):
        if what == 'evelocations':
            self.UpdateAllPanels()

    def UpdateMissionsPanel(self):
        uthread.new(self.UpdatePanel, PANEL_MISSIONS)

    def UpdateFactionalWarfarePanel(self):
        self.UpdatePanel(PANEL_FACTIONAL_WARFARE)

    def UpdateIncursionsPanel(self):
        self.UpdatePanel(PANEL_INCURSIONS)

    def UpdatePanel(self, panelTypeID):
        if not session.charid:
            return
        sm.ChainEvent('ProcessUpdateInfoPanel', panelTypeID)
        if not self.infoPanelContainer:
            return
        panel = self.GetPanelByTypeID(panelTypeID)
        if not panel:
            self.ReconstructAllPanels()
        elif panel and not panel.IsAvailable():
            self.infoPanelContainer.ClosePanel(panelTypeID)
        self.UpdateTopIcons()

    def GetAgentMissions(self, *args):
        allMissionsList = []
        missions = sm.GetService('journal').GetMyAgentJournalDetails()[0]
        HOMEBASE = 0
        NOTHOMEBASE = 1
        if missions:
            for mission in missions:
                missionState, importantMission, missionType, missionNameID, agentID, expirationTime, bookmarks, remoteOfferable, remoteCompletable, contentID = mission
                if missionState != const.agentMissionStateAccepted or expirationTime and expirationTime < blue.os.GetWallclockTime():
                    continue
                homeBaseBms = []
                otherBms = []
                foundHomeBaseBm = False
                for bm in bookmarks:
                    if bm.locationType == 'agenthomebase':
                        homeBaseBms.append((HOMEBASE, bm))
                    elif 'isAgentBase' in bm.__dict__ and bm.isAgentBase:
                        foundHomeBaseBm = True
                        otherBms.append((HOMEBASE, bm))
                    else:
                        otherBms.append((NOTHOMEBASE, bm))

                bookmarksIwant = otherBms
                if not foundHomeBaseBm:
                    bookmarksIwant.extend(homeBaseBms)
                bookmarksIwant = uiutil.SortListOfTuples(bookmarksIwant)
                bmInfo = uiutil.Bunch(missionNameID=missionNameID, bookmarks=bookmarksIwant, agentID=agentID)
                allMissionsList.append((expirationTime, bmInfo))

            allMissionsList = uiutil.SortListOfTuples(allMissionsList)
        return allMissionsList

    def GetSolarSystemTrace(self, itemID, altText = None, traceFontSize = 12):
        if util.IsStation(itemID):
            solarSystemID = cfg.stations.Get(itemID).solarSystemID
        else:
            solarSystemID = itemID
        try:
            sec, col = util.FmtSystemSecStatus(sm.GetService('map').GetSecurityStatus(solarSystemID), 1)
            col.a = 1.0
            securityLabel = "</b> <color=%s><hint='%s'>%s</hint></color>" % (util.StrFromColor(col), localization.GetByLabel('UI/Map/StarMap/SecurityStatus'), sec)
        except KeyError:
            self.LogError('Neocom failed to get security status for item', solarSystemID, 'displaying BROKEN')
            log.LogException()
            sys.exc_clear()
            securityLabel = ''

        constellationID = cfg.solarsystems.Get(solarSystemID).constellationID
        regionID = cfg.constellations.Get(constellationID).regionID
        if altText:
            solarSystemAlt = " alt='%s'" % altText
        else:
            solarSystemAlt = ''
        locationTrace = '<url=showinfo:%s//%s%s>%s</url>%s' % (const.typeSolarSystem,
         solarSystemID,
         solarSystemAlt,
         cfg.evelocations.Get(solarSystemID).locationName,
         securityLabel)
        if traceFontSize:
            locationTrace += '<fontsize=12>'
        if not util.IsWormholeRegion(regionID):
            seperator = '<fontsize=%(fontsize)s> </fontsize>&lt;<fontsize=%(fontsize)s> </fontsize>' % {'fontsize': 8}
            locationTrace += seperator
            locationTrace += '<url=showinfo:%s//%s>%s</url>' % (const.typeConstellation, constellationID, cfg.evelocations.Get(constellationID).locationName)
            locationTrace += seperator
            locationTrace += '<url=showinfo:%s//%s>%s</url>' % (const.typeRegion, regionID, cfg.evelocations.Get(regionID).locationName)
        return locationTrace

    def GetLocationInfoSettings(self):
        inView = settings.char.windows.Get('neocomLocationInfo_3', None)
        if inView is None:
            inView = ['nearest', 'sovereignty']
        return inView

    def GetSolarSystemStatusText(self, systemStatus = None, returnNone = False):
        if systemStatus is None:
            systemStatus = sm.StartService('facwar').GetSystemStatus()
        xtra = ''
        if systemStatus == const.contestionStateCaptured:
            xtra = localization.GetByLabel('UI/Neocom/SystemLost')
        elif systemStatus == const.contestionStateVulnerable:
            xtra = localization.GetByLabel('UI/Neocom/Vulnerable')
        elif systemStatus == const.contestionStateContested:
            xtra = localization.GetByLabel('UI/Neocom/Contested')
        elif systemStatus == const.contestionStateNone and returnNone:
            xtra = localization.GetByLabel('UI/Neocom/Uncontested')
        return xtra