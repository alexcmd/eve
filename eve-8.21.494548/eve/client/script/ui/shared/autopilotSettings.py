#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/autopilotSettings.py
import uicls
import uiconst
import form
import localization
import blue
import listentry
import util
import uthread

class AutopilotSettings(uicls.Window):
    __guid__ = 'form.AutopilotSettings'
    default_windowID = 'AutopilotSettings'
    default_width = 600
    default_height = 450
    default_topParentHeight = 0
    default_minSize = (100, 140)
    default_iconNum = 'ui_12_64_3'
    default_caption = 'UI/Map/MapPallet/ManageAutopilotRoute'
    __notifyevents__ = ['OnDestinationSet', 'OnAvoidanceItemsChanged']

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.isChangingOrder = False
        self.loadedTab = None
        self.waypointBtns = uicls.ButtonGroup(parent=self.sr.main, btns=[[localization.GetByLabel('UI/Map/MapPallet/btnOptimizeRoute'),
          sm.GetService('autoPilot').OptimizeRoute,
          (),
          66]])
        self.sr.waypointopt = uicls.Container(name='waypointopt', parent=self.sr.main, align=uiconst.TOBOTTOM, clipChildren=True, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         0))
        self.sr.scroll2 = uicls.Scroll(parent=self.sr.main, padding=const.defaultPadding)
        self.sr.scroll2.sr.id = 'autopilotSettings'
        self.sr.scroll2.sr.content.OnDropData = self.MoveWaypoints
        uicls.EveLabelMedium(text=localization.GetByLabel('UI/Map/MapPallet/lblChangeWaypointPriority'), parent=self.sr.waypointopt, pos=(3, 2, 0, 0))
        checkbox = uicls.Checkbox(text=localization.GetByLabel('UI/Map/MapPallet/cbExpandWaypoints'), parent=self.sr.waypointopt, configName='expandwaypoints', retval=None, checked=settings.user.ui.Get('expandwaypoints', 1), callback=self.OnCheckboxWaypoints, align=uiconst.TOPLEFT, pos=(1, 18, 140, 0))
        checkbox.data = {'key': 'expandwaypoints',
         'retval': None}
        self.sr.waypointopt.height = checkbox.height + 22
        autopilottabs = uicls.TabGroup(name='tabparent', parent=self.sr.main, idx=0)
        autopilottabs.Startup([[localization.GetByLabel('UI/Map/MapPallet/tabWaypoints'),
          self.sr.scroll2,
          self,
          'waypointconf',
          self.sr.waypointopt], [localization.GetByLabel('UI/Map/MapPallet/tabMapAdvoidance'),
          self.sr.scroll2,
          self,
          'avoidconf',
          None]], 'autopilottabs', autoselecttab=1)
        self.sr.autopilottabs = autopilottabs

    def Load(self, key):
        self.SetHint()
        self.waypointBtns.display = False
        if key == 'waypointconf':
            self.waypointBtns.display = True
            self.LoadWaypoints()
        elif key == 'avoidconf':
            self.LoadAvoidance()
        if self.destroyed:
            return
        self.loadedTab = key

    def MoveWaypoints(self, dragObj, entries, orderID = -1, *args):
        self.ChangeWaypointSorting(orderID=orderID)

    def ChangeWaypointSorting(self, orderID = -1, *args):
        if self.isChangingOrder:
            return
        try:
            self.isChangingOrder = True
            sel = self.sr.scroll2.GetSelected()
            starmapSvc = sm.GetService('starmap')
            if not len(sel):
                return
            waypoints = starmapSvc.GetWaypoints()
            waypointIndex = sel[0].orderID
            if waypointIndex < 0:
                return
            if waypointIndex > len(waypoints):
                return
            waypoint = waypoints[waypointIndex]
            del waypoints[waypointIndex]
            if waypointIndex < orderID:
                orderID -= 1
            if orderID == -1:
                orderID = len(waypoints)
            waypoints.insert(orderID, waypoint)
            starmapSvc.SetWaypoints(waypoints)
        finally:
            self.isChangingOrder = False

    def OnCheckboxWaypoints(self, checkbox):
        val = checkbox.data['retval']
        if val is None:
            val = checkbox.checked
        settings.user.ui.Set('expandwaypoints', val)
        self.LoadWaypoints()

    def LoadWaypoints(self, *args):
        mapSvc = sm.GetService('map')
        starmapSvc = sm.GetService('starmap')
        waypoints = starmapSvc.GetWaypoints()
        tmplst = []
        fromID = eve.session.solarsystemid2
        scrolllist = []
        actualID = 0
        selectedItem = None
        if waypoints and len(waypoints):
            self.SetHint()
            counter = 0
            currentPlace = mapSvc.GetItem(eve.session.solarsystemid2)
            opts = {'itemID': currentPlace.itemID,
             'typeID': currentPlace.typeID,
             'label': localization.GetByLabel('UI/Map/MapPallet/lblCurrentLocation', locationName=currentPlace.itemName),
             'orderID': -1,
             'actualID': 0}
            scrolllist.append(listentry.Get('Item', opts))
            for waypointID in waypoints:
                blue.pyos.BeNice()
                actualID = actualID + 1
                each = mapSvc.GetItem(waypointID)
                description = localization.GetByLabel('UI/Map/MapPallet/lblActiveColorCategory', activeLabel=cfg.invtypes.Get(each.typeID).name)
                wasID = each.itemID
                while wasID:
                    wasID = mapSvc.GetParent(wasID)
                    if wasID:
                        item = mapSvc.GetItem(wasID)
                        if item is not None:
                            description = description + ' / ' + item.itemName

                if settings.user.ui.Get('expandwaypoints', 1) == 1:
                    solarsystems = starmapSvc.GetRouteFromWaypoints([waypointID], fromID)
                    if len(solarsystems):
                        for solarsystemID in solarsystems[1:-1]:
                            actualID = actualID + 1
                            sunItem = mapSvc.GetItem(solarsystemID)
                            scrolllist.append(listentry.Get('AutoPilotItem', {'itemID': solarsystemID,
                             'typeID': sunItem.typeID,
                             'label': localization.GetByLabel('UI/Map/MapPallet/lblWaypointListEntryNoCount', itemName=sunItem.itemName),
                             'orderID': -1,
                             'actualID': actualID}))

                lblTxt = localization.GetByLabel('UI/Map/MapPallet/lblWaypointListEntry', counter=counter + 1, itemName=each.itemName, description=description)
                scrolllist.append(listentry.Get('AutoPilotItem', {'itemID': waypointID,
                 'typeID': each.typeID,
                 'label': lblTxt,
                 'orderID': counter,
                 'actualID': actualID,
                 'canDrag': 1}))
                if self.sr.Get('selectedWaypoint', None) is not None and self.sr.selectedWaypoint < len(waypoints) and waypointID == waypoints[self.sr.selectedWaypoint]:
                    selectedItem = actualID
                counter = counter + 1
                fromID = waypointID

        if self == None:
            return
        destinationPath = starmapSvc.GetDestinationPath()
        self.sr.scroll2.Load(contentList=scrolllist)
        if not len(scrolllist):
            self.SetHint(localization.GetByLabel('UI/Map/MapPallet/hintNoWaypoints'))
        if selectedItem is not None:
            self.sr.scroll2.SetSelected(selectedItem)

    def LoadAvoidance(self, *args):
        mapSvc = sm.StartService('map')
        items = sm.StartService('pathfinder').GetAvoidanceItems()
        scrolllist = []
        if items and len(items):
            self.SetHint()
            counter = 0
            for itemsID in items:
                blue.pyos.BeNice()
                each = mapSvc.GetItem(itemsID)
                description = localization.GetByLabel('UI/Map/MapPallet/lblActiveColorCategory', activeLabel=cfg.invgroups.Get(each.typeID).name)
                wasID = each.itemID
                while wasID:
                    wasID = mapSvc.GetParent(wasID)
                    if wasID:
                        item = mapSvc.GetItem(wasID)
                        if item is not None:
                            description = description + ' / ' + item.itemName

                scrolllist.append(listentry.Get('Item', {'itemID': itemsID,
                 'typeID': each.typeID,
                 'label': localization.GetByLabel('UI/Map/MapPallet/lblAdvoidanceListEntry', itemName=each.itemName, description=description)}))

        self.sr.scroll2.Load(contentList=scrolllist)
        if not len(scrolllist):
            self.SetHint(localization.GetByLabel('UI/Map/MapPallet/hintNoAdvoidanceItems'))

    def SetHint(self, hintstr = None):
        if self.sr.scroll2:
            self.sr.scroll2.ShowHint(hintstr)

    def OnDestinationSet(self, *args):
        if self.sr.autopilottabs.GetSelectedArgs() == 'waypointconf':
            self.LoadWaypoints()

    def OnAvoidanceItemsChanged(self):
        if self.sr.autopilottabs.GetSelectedArgs() == 'avoidconf':
            self.LoadAvoidance()