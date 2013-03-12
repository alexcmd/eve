#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/infoPanels/infoPanelRoute.py
import uicls
import uiconst
import util
import blue
import localization
import infoPanel
import uiutil
import ccConst
import uthread
import base
import random
import form
import weakref
from collections import deque
ROUTE_MARKERSIZE = 8
ROUTE_MARKERGAP = 2
ROUTE_MARKERTYPE_NORMAL = 0
ROUTE_MARKERTYPE_STATION = 1
ROUTE_MARKERTYPE_WAYPOINT = 2
NEOCOM_PANELWIDTH = 328
FRAME_WIDTH = 20
FRAME_SEPERATION = 10
IDLE_ROUTEMARKER_ALPHA = 0.75

class InfoPanelRoute(uicls.InfoPanelBase):
    __guid__ = 'uicls.InfoPanelRoute'
    default_name = 'InfoPanelRoute'
    panelTypeID = infoPanel.PANEL_ROUTE
    label = 'UI/InfoWindow/TabNames/Route'
    default_iconTexturePath = 'res:/UI/Texture/Classes/InfoPanels/Route.png'
    hasSettings = True
    __notifyevents__ = ['OnDestinationSet',
     'OnUIRefresh',
     'OnAutoPilotOn',
     'OnAutoPilotOff']

    def ApplyAttributes(self, attributes):
        uicls.InfoPanelBase.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.routeData = None
        self.sliderLabel = None
        self.toAnimate = []
        self.utilMenu = None
        self.header = self.headerCls(parent=self.headerCont, align=uiconst.CENTERLEFT)
        self.headerCompact = self.headerCls(name='headerCompact', parent=self.headerCont, align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL, opacity=0.0)
        self.headerCompact.SetRightAlphaFade(infoPanel.PANELWIDTH - infoPanel.LEFTPAD, self.HEADER_FADE_WIDTH)
        self.noDestinationLabel = uicls.EveLabelMedium(name='noDestinationLabel', parent=self.mainCont, text=localization.GetByLabel('UI/Inflight/NoDestination'), align=uiconst.TOTOP, state=uiconst.UI_HIDDEN)
        bgColor = (1, 1, 1, 0.15)
        self.currentParent = uicls.Container(name='currentParent', parent=self.mainCont, align=uiconst.TOTOP, padBottom=12, height=19)
        self.currentTrace = uicls.EveLabelMedium(name='currentTrace', parent=self.currentParent, align=uiconst.CENTER, state=uiconst.UI_NORMAL, width=infoPanel.PANELWIDTH - infoPanel.LEFTPAD, left=1)
        uicls.Fill(parent=self.currentParent, color=bgColor)
        currentPointer = uicls.Sprite(parent=self.currentParent, texturePath='res:/UI/Texture/classes/LocationInfo/pointerDown.png', pos=(0, -10, 10, 10), state=uiconst.UI_DISABLED, align=uiconst.BOTTOMLEFT, color=bgColor, idx=0)
        frame = uicls.Frame(parent=self.currentParent, frameConst=ccConst.FRAME_SOFTSHADE, color=(0, 0, 0, 0.25), padding=(-5, -5, -5, -10))
        self.markersParent = uicls.Container(name='markersParent', parent=self.mainCont, align=uiconst.TOTOP)
        self.endParent = uicls.Container(name='endParent', parent=self.mainCont, align=uiconst.TOTOP, padTop=12, height=19)
        self.endTrace = uicls.EveLabelMedium(name='endTrace', parent=self.endParent, align=uiconst.CENTER, state=uiconst.UI_NORMAL, width=NEOCOM_PANELWIDTH - FRAME_WIDTH * 2, left=1)
        uicls.Fill(parent=self.endParent, color=bgColor)
        self.endPointer = uicls.Sprite(parent=self.endParent, texturePath='res:/UI/Texture/classes/LocationInfo/pointerUp.png', pos=(0, -10, 10, 10), state=uiconst.UI_DISABLED, color=bgColor, idx=0)
        frame = uicls.Frame(parent=self.endParent, frameConst=ccConst.FRAME_SOFTSHADE, color=(0, 0, 0, 0.25), padding=(-5, -5, -5, -10))

    def GetSettingsMenu(self, parent):
        self.utilMenu = weakref.ref(parent)
        parent.AddCheckBox(localization.GetByLabel('UI/Map/MapPallet/AutopilotActive'), sm.GetService('autoPilot').GetState(), callback=self.OnCheckBoxAutopilotActive)
        parent.AddCheckBox(localization.GetByLabel('UI/Map/MapPallet/ShowRoutePathInSpace'), settings.user.ui.Get('routeVisualizationEnabled', True), callback=sm.GetService('sceneManager').ToggleRouteVisualization)
        pfRouteType = settings.char.ui.Get('pfRouteType', 'safe')
        parent.AddRadioButton(localization.GetByLabel('UI/Map/MapPallet/cbPreferShorter'), pfRouteType == 'shortest', callback=(self.OnRadioBtnRouteType, 'shortest'))
        parent.AddRadioButton(localization.GetByLabel('UI/Map/MapPallet/cbPreferSafer'), pfRouteType == 'safe', callback=(self.OnRadioBtnRouteType, 'safe'))
        parent.AddRadioButton(localization.GetByLabel('UI/Map/MapPallet/cbPreferRisky'), pfRouteType == 'unsafe', callback=(self.OnRadioBtnRouteType, 'unsafe'))
        sliderCont = uicls.Container(name='sliderCont', parent=parent, align=uiconst.TOTOP, height=18, padding=(17, 0, 0, 0))
        self.securitySlider = uicls.Slider(parent=sliderCont, align=uiconst.TOLEFT, width=100, name='pfPenalty', state=uiconst.UI_NORMAL, minValue=1, maxValue=100, labelDecimalPlaces=0, startVal=settings.char.ui.Get('pfPenalty', 50.0), showLabel=False, onsetvaluefunc=self.OnSecuritySlider, endsliderfunc=self.OnSecuritySliderEnd, hint=localization.GetByLabel('UI/Map/MapPallet/hintSecurityPeneltySlider'), padLeft=5)
        self.sliderLabel = uicls.EveLabelSmall(parent=sliderCont, align=uiconst.TOALL, padLeft=5, top=3)
        self.UpdateSliderLabel(self.securitySlider.value)
        parent.AddSpace()
        parent.AddCheckBox(localization.GetByLabel('UI/Map/MapPallet/cbAdvoidPodkill'), settings.char.ui.Get('pfAvoidPodKill', 0), callback=self.OnCheckBoxAvoidPodKill)
        parent.AddCheckBox(localization.GetByLabel('UI/Map/MapPallet/cbAdvoidSystemsOnList'), settings.char.ui.Get('pfAvoidSystems', 1), callback=self.OnCheckBoxAvoidSystems)
        parent.AddCheckBox(localization.GetByLabel('UI/Map/MapPallet/cbDisableAtEachWaypoint'), settings.user.ui.Get('autopilot_stop_at_each_waypoint', 0) == 0, callback=self.OnCheckBoxDisableAtEachWaypoint)
        parent.AddDivider()
        starmapSvc = sm.GetService('starmap')
        waypoints = starmapSvc.GetWaypoints()
        if len(waypoints) > 0:
            parent.AddButton(localization.GetByLabel('UI/Neocom/ClearAllAutopilotWaypoints'), starmapSvc.ClearWaypoints, toggleMode=False)
        if len(waypoints) > 1:
            parent.AddButton(localization.GetByLabel('UI/Map/MapPallet/OptimizeRoute'), sm.GetService('autoPilot').OptimizeRoute, toggleMode=False)
        parent.AddButton(localization.GetByLabel('UI/Map/MapPallet/ManageRoute'), form.AutopilotSettings.Open, toggleMode=False)

    def OnRadioBtnRouteType(self, routeType):
        sm.GetService('pathfinder').SetRouteType(routeType)
        sm.GetService('starmap').UpdateRoute()

    def OnCheckBoxAutopilotActive(self):
        autoPilotSvc = sm.GetService('autoPilot')
        if autoPilotSvc.GetState():
            autoPilotSvc.SetOff()
        else:
            autoPilotSvc.SetOn()

    def OnCheckBoxShowRoutePath(self):
        pass

    def OnCheckBoxAvoidPodKill(self):
        val = not settings.char.ui.Get('pfAvoidPodKill', 0)
        if val:
            eve.Message('MapAutoPilotAvoidPodkillZones')
        sm.GetService('pathfinder').SetPodKillAvoidance(val)
        sm.GetService('starmap').UpdateRoute()

    def OnCheckBoxAvoidSystems(self):
        val = not settings.char.ui.Get('pfAvoidSystems', 0)
        if val:
            eve.Message('MapAutoPilotAvoidSystems')
        sm.GetService('pathfinder').SetSystemAvoidance(val)
        sm.GetService('starmap').UpdateRoute()

    def OnCheckBoxDisableAtEachWaypoint(self):
        val = not settings.user.ui.Get('autopilot_stop_at_each_waypoint', 0)
        settings.user.ui.Set('autopilot_stop_at_each_waypoint', val)

    def OnSecuritySlider(self, slider):
        self.UpdateSliderLabel(slider.value)

    def OnSecuritySliderEnd(self, slider):
        settings.char.ui.Set('pfPenalty', slider.value)
        uthread.new(self._OnSecuritySliderEnd)
        self.UpdateSliderLabel(slider.value)

    def UpdateSliderLabel(self, value):
        if self.sliderLabel:
            self.sliderLabel.text = '%s %i' % (localization.GetByLabel('UI/Map/MapPallet/lblSecurityPenelity'), value)

    def _OnSecuritySliderEnd(self):
        sm.GetService('pathfinder').MakeDirty()
        sm.GetService('starmap').UpdateRoute()

    def ConstructNormal(self):
        self.UpdateRoute()

    def ConstructCompact(self):
        self.UpdateHeaderText()

    def OnDestinationSet(self, destination):
        self.UpdateRoute(animate=bool(destination))

    def UpdateRoute(self, animate = False):
        self.routeData = sm.GetService('starmap').GetAutopilotRoute()
        self.UpdateHeaderText()
        if not session.solarsystemid2:
            return
        if self.mode != infoPanel.MODE_NORMAL:
            return
        if not self.routeData or self.routeData == [None]:
            if self.markersParent:
                self.currentParent.Hide()
                self.endParent.Hide()
                self.markersParent.Hide()
            self.noDestinationLabel.Show()
            return
        self.noDestinationLabel.Hide()
        planetView = sm.GetService('viewState').IsViewActive('planet')
        autoPilotActive = sm.GetService('autoPilot').GetState()
        updatingRouteData = getattr(self, 'updatingRouteData', None)
        if updatingRouteData == (autoPilotActive, planetView, self.routeData):
            return
        oldRouteIDs = [ child.solarSystemID for child in self.markersParent.children ]
        self.toAnimate = []
        self.markersParent.Flush()
        self.updatingRouteData = (autoPilotActive, planetView, self.routeData[:])
        self.currentParent.Show()
        self.endParent.Show()
        self.markersParent.Show()
        self.currentTrace.text = '<center>' + sm.GetService('infoPanel').GetSolarSystemTrace(self.routeData[0], localization.GetByLabel('UI/Neocom/Autopilot/NextSystemInRoute'))
        self.currentParent.height = max(19, self.currentTrace.textheight + 4)
        routeIDs = []
        lastStationSystemID = None
        for i, id in enumerate(self.routeData):
            isLast = i == len(self.routeData) - 1
            if util.IsSolarSystem(id) and not isLast and not util.IsSolarSystem(self.routeData[i + 1]):
                continue
            if util.IsSolarSystem(id) and lastStationSystemID == id:
                continue
            if util.IsStation(id):
                lastStationSystemID = cfg.stations.Get(id).solarSystemID
            else:
                lastStationSystemID = None
            routeIDs.append(id)

        maxWidth = infoPanel.PANELWIDTH - self.mainCont.padLeft
        markerX = 0
        markerY = 0
        waypoints = deque(sm.GetService('starmap').GetWaypoints())
        nextWaypoint = waypoints.popleft() if waypoints else None
        for i, destinationID in enumerate(routeIDs):
            if destinationID == nextWaypoint:
                isWaypoint = True
                nextWaypoint = waypoints.popleft() if waypoints else None
            else:
                isWaypoint = False
            if util.IsSolarSystem(destinationID):
                isStation = False
                solarSystemID = destinationID
            elif util.IsStation(destinationID):
                isStation = True
                solarSystemID = cfg.stations.Get(destinationID).solarSystemID
            else:
                self.LogError('ConstructRoute: Unknown item. I can only handle solar systems and stations, you gave me', destinationID)
            if len(self.markersParent.children) > i:
                systemIcon = self.markersParent.children[i]
                systemIcon.left = markerX
                systemIcon.top = markerY
            else:
                systemIcon = uicls.AutopilotDestinationIcon(parent=self.markersParent, pos=(markerX,
                 markerY,
                 ROUTE_MARKERSIZE,
                 ROUTE_MARKERSIZE), solarSystemID=solarSystemID, destinationID=destinationID, idx=i)
                if i >= len(oldRouteIDs) or solarSystemID != oldRouteIDs[i]:
                    self.toAnimate.append(systemIcon)
            systemIcon.SetSolarSystemAndDestinationID(solarSystemID, destinationID)
            if isStation:
                systemIcon.SetMarkerType(ROUTE_MARKERTYPE_STATION)
            elif isWaypoint:
                systemIcon.SetMarkerType(ROUTE_MARKERTYPE_WAYPOINT)
            else:
                systemIcon.SetMarkerType(ROUTE_MARKERTYPE_NORMAL)
            self.endPointer.left = markerX
            markerParHeight = markerY + ROUTE_MARKERSIZE + ROUTE_MARKERGAP
            if animate:
                uicore.animations.MorphScalar(self.markersParent, 'height', self.markersParent.height, markerParHeight, duration=0.3)
            else:
                self.markersParent.height = markerParHeight
            markerX += ROUTE_MARKERGAP + ROUTE_MARKERSIZE
            if markerX + ROUTE_MARKERSIZE > maxWidth:
                markerX = 0
                markerY += ROUTE_MARKERGAP + ROUTE_MARKERSIZE
            if len(routeIDs) > 1:
                endTrace = self.endTrace
                endTrace.text = '<center>' + sm.GetService('infoPanel').GetSolarSystemTrace(routeIDs[-1], localization.GetByLabel('UI/Neocom/Autopilot/CurrentDestination'))
                self.endParent.height = max(19, endTrace.textheight + 4)
                self.endParent.Show()
            else:
                self.endParent.Hide()

        self.updatingRouteData = None
        if animate:
            uthread.new(self.AnimateRouteIn)

    def UpdateHeaderText(self):
        routeData = sm.GetService('starmap').GetAutopilotRoute()
        if self.mode == infoPanel.MODE_NORMAL:
            numJumps = self._GetNumJumps(routeData)
            if numJumps:
                subHeader = localization.GetByLabel('UI/Market/MarketQuote/NumberOfJumps', num=numJumps)
            else:
                subHeader = ''
            self.header.text = '<color=white>%s <fontsize=12></b>%s' % (localization.GetByLabel('UI/InfoWindow/TabNames/Route'), subHeader)
        elif routeData:
            self.headerCompact.text = sm.GetService('infoPanel').GetSolarSystemTrace(routeData[0], localization.GetByLabel('UI/Neocom/Autopilot/CurrentDestination'))
        else:
            self.headerCompact.text = localization.GetByLabel('UI/Inflight/NoDestination')

    def OnStartModeChanged(self, oldMode):
        uthread.new(self._OnStartModeChanged, oldMode)

    def _OnStartModeChanged(self, oldMode):
        if self.mode == infoPanel.MODE_NORMAL:
            if oldMode:
                self.headerCompact.Disable()
                uicore.animations.FadeOut(self.headerCompact, duration=0.3, sleep=True)
                uicore.animations.FadeIn(self.header, duration=0.3)
            else:
                self.header.opacity = 1.0
                self.headerCompact.opacity = 0.0
        elif self.mode == infoPanel.MODE_COMPACT:
            if oldMode:
                uicore.animations.FadeOut(self.header, duration=0.3, sleep=True)
                uicore.animations.FadeIn(self.headerCompact, duration=0.3)
                self.headerCompact.Enable()
            else:
                self.header.opacity = 0.0
                self.headerCompact.opacity = 1.0

    def AnimateRouteIn(self):
        if not self.toAnimate:
            return
        random.shuffle(self.toAnimate)
        kOffset = 0.6 / len(self.toAnimate)
        for i, icon in enumerate(self.toAnimate):
            uicore.animations.SpMaskIn(icon.icon, timeOffset=i * kOffset, loops=3, duration=0.05)

    def _GetNumJumps(self, routeData):
        if not routeData:
            return 0
        ids = []
        lastID = None
        for id in routeData:
            if util.IsStation(id):
                id = cfg.stations.Get(id).solarSystemID
            if id != lastID:
                ids.append(id)
            lastID = id

        numJumps = len(ids)
        if ids and ids[0] == session.solarsystemid2:
            numJumps -= 1
        return numJumps

    def OnUIRefresh(self):
        self.UpdateRoute()

    def OnAutoPilotOn(self):
        if self.utilMenu and self.utilMenu():
            self.utilMenu().ReloadMenu()

    def OnAutoPilotOff(self):
        if self.utilMenu and self.utilMenu():
            self.utilMenu().ReloadMenu()


class AutopilotDestinationIcon(uicls.Container):
    __guid__ = 'uicls.AutopilotDestinationIcon'
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    isDragObject = True

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.icon = uicls.Sprite(parent=self, pos=(0, 0, 10, 10), state=uiconst.UI_DISABLED, shadowOffset=(0, 1), shadowColor=(0, 0, 0, 0.2))
        self.markerType = None
        self.solarSystemID = None
        self.destinationID = None
        self.hiliteTimer = None

    def SetMarkerType(self, markerType):
        if self.markerType == markerType:
            return
        if markerType == ROUTE_MARKERTYPE_WAYPOINT:
            self.icon.LoadTexture('res:/UI/Texture/classes/LocationInfo/waypointMarker.png')
        elif markerType == ROUTE_MARKERTYPE_STATION:
            self.icon.LoadTexture('res:/UI/Texture/classes/LocationInfo/stationMarker.png')
        else:
            self.icon.LoadTexture('res:/UI/Texture/classes/LocationInfo/normalMarker.png')
        self.markerType = markerType

    def SetSolarSystemAndDestinationID(self, solarSystemID, destinationID):
        if self.solarSystemID == solarSystemID and self.destinationID == destinationID:
            return
        c = sm.GetService('map').GetSystemColor(solarSystemID)
        self.icon.SetRGB(c.r, c.g, c.b, IDLE_ROUTEMARKER_ALPHA)
        self.solarSystemID = solarSystemID
        self.destinationID = destinationID

    def OnMouseEnter(self, *args):
        uicore.animations.FadeTo(self.icon, startVal=self.icon.color.a, endVal=1.0, duration=0.125, loops=1)
        if self.hiliteTimer is None:
            self.hiliteTimer = base.AutoTimer(111, self.CheckIfMouseOver)

    def CheckIfMouseOver(self, *args):
        if uicore.uilib.mouseOver == self:
            return
        uicore.animations.FadeTo(self.icon, startVal=self.icon.color.a, endVal=IDLE_ROUTEMARKER_ALPHA, duration=0.5, loops=1)
        self.hiliteTimer = None

    def OnMouseExit(self, *args):
        self.CheckIfMouseOver()

    def GetHint(self, *args):
        ret = sm.GetService('infoPanel').GetSolarSystemTrace(self.destinationID, traceFontSize=None)
        if util.IsStation(self.destinationID):
            ret += '<br>' + cfg.evelocations.Get(self.destinationID).name
        return ret

    def GetMenu(self, *args):
        if util.IsSolarSystem(self.destinationID):
            return sm.GetService('menu').GetMenuFormItemIDTypeID(self.destinationID, const.typeSolarSystem)
        if util.IsStation(self.destinationID):
            station = sm.StartService('ui').GetStation(self.destinationID)
            return sm.GetService('menu').GetMenuFormItemIDTypeID(self.destinationID, station.stationTypeID)

    def OnClick(self, *args):
        if util.IsSolarSystem(self.destinationID):
            sm.GetService('info').ShowInfo(const.typeSolarSystem, self.destinationID)
        elif util.IsStation(self.destinationID):
            station = sm.StartService('ui').GetStation(self.destinationID)
            sm.GetService('info').ShowInfo(station.stationTypeID, self.destinationID)

    def GetDragData(self, *args):
        entry = util.KeyVal()
        entry.__guid__ = 'xtriui.ListSurroundingsBtn'
        entry.itemID = self.destinationID
        entry.label = cfg.evelocations.Get(self.destinationID).name
        if util.IsSolarSystem(self.destinationID):
            entry.typeID = const.typeSolarSystem
        else:
            station = sm.StartService('ui').GetStation(self.destinationID)
            entry.typeID = station.stationTypeID
        return [entry]