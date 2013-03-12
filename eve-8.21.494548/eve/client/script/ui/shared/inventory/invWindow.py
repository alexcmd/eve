#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/inventory/invWindow.py
import uicls
import uiconst
import util
import uiutil
import blue
import invCont
import invCtrl
import uthread
import uix
import log
import localization
import form
import state
import service
import telemetry
from math import pi
import base
import collections
import bracketUtils
CONTAINERGROUPS = (const.groupCargoContainer,
 const.groupSecureCargoContainer,
 const.groupAuditLogSecureContainer,
 const.groupFreightContainer)
NO_DISTANCE_SHOWN = ['POSCorpHangar',
 'POSStrontiumBay',
 'POSFuelBay',
 'POSStructureChargesStorage',
 'POSStructureChargeCrystal']
HISTORY_LENGTH = 50
TREE_DEFAULT_WIDTH = 160

def SortData(data):
    data.sort(key=lambda x: x.GetLabel().lower())


def GetTreeViewEntryClassByDataType(treeData):
    treeEntryCls = uicls.TreeViewEntry
    if treeData:
        clsName = getattr(treeData, 'clsName', None)
        if clsName in ('ShipMaintenanceBay', 'ShipFleetHangar') and treeData.invController.itemID == util.GetActiveShip():
            treeEntryCls = uicls.TreeViewEntryAccessConfig
        elif clsName in ('StationCorpHangar', 'POSCorpHangar', 'StationContainer'):
            treeEntryCls = uicls.TreeViewEntryAccessRestricted
    return treeEntryCls


def GetContainerDataFromItems(items, parent = None):
    data = []
    for item in items:
        if item.typeID == const.typePlasticWrap and item.singleton:
            data.append(uiutil.TreeDataPlasticWrap(parent=parent, clsName='StationContainer', itemID=item.itemID, typeID=item.typeID))
        elif item.groupID in CONTAINERGROUPS and item.singleton:
            data.append(uiutil.TreeDataInv(parent=parent, clsName='StationContainer', itemID=item.itemID, typeID=item.typeID))

    cfg.evelocations.Prime([ d.invController.itemID for d in data ])
    SortData(data)
    return data


class HistoryBuffer():
    __guid__ = 'uiutil.HistoryBuffer'

    def __init__(self, maxLen = None):
        self.maxLen = maxLen
        self.deque = collections.deque(maxlen=self.maxLen)
        self.idx = None

    def Append(self, data):
        if len(self.deque) and self.idx is not None:
            self.deque = collections.deque(list(self.deque)[:self.idx + 1], maxlen=self.maxLen)
        if not len(self.deque) or data != self.deque[-1]:
            self.deque.append(data)
        self.idx = len(self.deque) - 1

    def GoBack(self):
        if self.IsBackEnabled():
            self.idx -= 1
            return self.deque[self.idx]

    def GoForward(self):
        if self.IsForwardEnabled():
            self.idx += 1
            return self.deque[self.idx]

    def IsBackEnabled(self):
        return len(self.deque) > 1 and self.idx > 0

    def IsForwardEnabled(self):
        return len(self.deque) > 1 and self.idx < len(self.deque) - 1


class Inventory(uicls.Window):
    __guid__ = 'form.Inventory'
    __notifyevents__ = ['OnSessionChanged',
     'OnItemNameChange',
     'OnMultipleItemChange',
     'ProcessActiveShipChanged',
     'OnBeforeActiveShipChanged',
     'OnOfficeRentalChanged',
     'OnStateChange',
     'OnInvContDragEnter',
     'OnInvContDragExit',
     'DoBallsAdded',
     'DoBallRemove',
     'ProcessTempInvLocationAdded',
     'ProcessTempInvLocationRemoved',
     'OnSlimItemChange',
     'OnInvFiltersChanged',
     'OnInvContRefreshed',
     'OnCapacityChange',
     'OnWreckLootAll',
     'OnShowFullInvTreeChanged']
    default_windowID = ('Inventory', None)
    default_width = 600
    default_height = 450
    default_topParentHeight = 0
    default_minSize = (100, 140)
    default_iconNum = 'ui_12_64_3'
    default_isCompactable = True
    default_caption = None

    def ApplyAttributes(self, attributes):
        self.currInvID = attributes.Get('invID', None)
        self.rootInvID = attributes.Get('rootInvID', self.currInvID)
        self.invController = invCtrl.GetInvCtrlFromInvID(self.currInvID)
        uicls.Window.ApplyAttributes(self, attributes)
        sm.GetService('inv').Register(self)
        self.treeEntryByID = {}
        self.tempTreeEntryByID = {}
        self.dragHoverThread = None
        self.refreshTreeThread = None
        self.updateSelectedItemsThread = None
        self.updateSelectedItemsPending = None
        self.invCont = None
        self.filterEntries = []
        self.loadingTreeView = False
        self.loadingInvCont = False
        self.dragOpenNewWindowCookie = None
        self.treeData = None
        self.treeDataTemp = None
        self.containersInRangeUpdater = None
        self.history = uiutil.HistoryBuffer(HISTORY_LENGTH)
        self.breadcrumbInvIDs = []
        if session.stationid2:
            invCtrl.StationItems().GetItems()
        self.dividerCont = uicls.DragResizeCont(name='dividerCont', settingsID='invTreeViewWidth_%s' % self.GetWindowSettingsID(), parent=self.sr.main, align=uiconst.TOLEFT, minSize=50, defaultSize=TREE_DEFAULT_WIDTH, clipChildren=True, onResizeCallback=self.OnDividerContResize)
        uthread.new(self.OnDividerContResize)
        self.treeTopCont = uicls.Container(name='treeTopCont', parent=self.dividerCont.mainCont, align=uiconst.TOTOP, height=20, padBottom=1)
        uicls.Line(parent=self.treeTopCont, align=uiconst.TOBOTTOM, color=(1.0, 1.0, 1.0, 0.1))
        uicls.Fill(parent=self.treeTopCont, color=(0.5, 0.5, 0.5, 0.1))
        uicls.UtilMenu(menuAlign=uiconst.TOPLEFT, parent=self.treeTopCont, align=uiconst.CENTERLEFT, GetUtilMenu=self.InventorySettings, texturePath='res:/UI/Texture/Icons/73_16_50.png', pos=(4, 0, 14, 14))
        uicls.Label(parent=self.treeTopCont, text=localization.GetByLabel('UI/Inventory/Index'), align=uiconst.CENTERLEFT, left=20, color=(0.5, 0.5, 0.5, 1.0))
        self.treeBottomCont = uicls.DragResizeCont(name='treeBottomCont', parent=self.dividerCont.mainCont, settingsID='invFiltersHeight_%s' % self.GetWindowSettingsID(), align=uiconst.TOBOTTOM, state=uiconst.UI_PICKCHILDREN, minSize=100, maxSize=0.5, defaultSize=150, padBottom=5)
        self.filterHeaderCont = uicls.Container(name='filterHeaderCont', parent=self.treeBottomCont, align=uiconst.TOTOP, height=22, state=uiconst.UI_NORMAL)
        self.filterHeaderCont.OnDblClick = self.OnExpandFiltersBtn
        uicls.GradientSprite(bgParent=self.filterHeaderCont, rotation=-pi / 2, rgbData=[(0, (0.3, 0.3, 0.3))], alphaData=[(0, 0.5), (0.9, 0.15)])
        filtersEnabledBtn = uicls.Container(name='filtersEnabledBtn', parent=self.filterHeaderCont, align=uiconst.TORIGHT, state=uiconst.UI_NORMAL, width=24, pickRadius=7)
        self.createFilterBtn = uicls.ButtonIcon(name='createFilterBtn', parent=self.filterHeaderCont, align=uiconst.TORIGHT, width=self.filterHeaderCont.height, iconSize=9, texturePath='res:/UI/Texture/Icons/Plus.png', func=self.OnCreateFilterBtn)
        filtersEnabledBtn.OnClick = self.OnFiltersEnabledBtnClicked
        self.filtersEnabledBtnColor = uicls.Sprite(bgParent=filtersEnabledBtn, texturePath='res:/UI/Texture/CharacterCreation/radiobuttonColor.dds', color=(0, 1.0, 0, 0.0))
        uicls.Sprite(bgParent=filtersEnabledBtn, texturePath='res:/UI/Texture/CharacterCreation/radiobuttonBack.dds', opacity=0.4)
        uicls.Sprite(bgParent=filtersEnabledBtn, texturePath='res:/UI/Texture/CharacterCreation/radiobuttonShadow.dds', color=(0.4, 0.4, 0.4, 0.4))
        labelCont = uicls.Container(name='labelCont', parent=self.filterHeaderCont, clipChildren=True)
        label = uicls.Label(left=22, parent=labelCont, text=localization.GetByLabel('UI/Inventory/MyFilters'), align=uiconst.CENTERLEFT)
        self.expandFiltersBtn = uicls.ButtonIcon(name='expandFiltersBtn', parent=labelCont, align=uiconst.TOLEFT, iconSize=7, texturePath='res:/UI/Texture/classes/Neocom/arrowDown.png', width=22, func=self.OnExpandFiltersBtn)
        self.filterCont = uicls.ScrollContainer(name='filterCont', parent=self.treeBottomCont, align=uiconst.TOALL, height=0.2)
        uicls.GradientSprite(bgParent=self.filterCont, rotation=-pi / 2, rgbData=[(0, (0.3, 0.3, 0.3))], alphaData=[(0, 0.2), (0.7, 0.2), (0.9, 0)])
        self.tree = uicls.ScrollContainer(name='tree', parent=self.dividerCont.mainCont, padTop=1)
        self.tree.GetMenu = self.GetMenu
        uicls.GradientSprite(bgParent=self.tree, rotation=-pi / 2, rgbData=[(0, (0.3, 0.3, 0.3))], alphaData=[(0, 0.2), (0.7, 0.2), (0.9, 0)])
        self.tree.Paste = self.Paste
        self.rightCont = uicls.Container(name='rightCont', parent=self.sr.main, padRight=const.defaultPadding, clipChildren=True)
        self.noInventoryLabel = uicls.EveCaptionMedium(name='noInventoryLabel', parent=self.rightCont, state=uiconst.UI_HIDDEN, text=localization.GetByLabel('UI/Inventory/NoInventoryLocationSelected'), pos=(17, 78, 0, 0), opacity=0.5)
        self.topRightCont1 = uicls.Container(name='topRightcont1', parent=self.rightCont, align=uiconst.TOTOP, height=20, clipChildren=True)
        uicls.Line(parent=self.topRightCont1, align=uiconst.TOBOTTOM, color=(1.0, 1.0, 1.0, 0.1), padLeft=-4)
        uicls.GradientSprite(parent=self.topRightCont1, align=uiconst.TOALL, state=uiconst.UI_DISABLED, rgbData=[(0, (0.5, 0.5, 0.5))], alphaData=[(0, 0.0), (0.1, 0.1)])
        self.topRightCont2 = uicls.Container(name='topRightCont2', parent=self.rightCont, align=uiconst.TOTOP, height=24, padBottom=1, clipChildren=True)
        self.bottomRightCont = uicls.Container(name='bottomRightcont', parent=self.rightCont, align=uiconst.TOBOTTOM, height=40, clipChildren=True)
        self.specialActionsCont = uicls.ContainerAutoSize(name='specialActionsCont', parent=self.bottomRightCont, align=uiconst.TOLEFT, padding=(1, 10, 2, 10))
        self.bottomRightLabelCont = uicls.Container(name='bottomRightLabelCont', parent=self.bottomRightCont, clipChildren=True)
        self.expandTreeBtn = uicls.ButtonIcon(name='expandTreeBtn', parent=self.topRightCont1, align=uiconst.TOLEFT, width=20, iconSize=7, texturePath='res:/UI/Texture/classes/Neocom/arrowDown.png', func=self.OnExpandTreeBtn)
        cont = uicls.Container(parent=self.topRightCont1, clipChildren=True)
        self.viewBtns = uicls.InvContViewBtns(parent=cont, top=2, align=uiconst.TORIGHT, controller=self)
        self.goForwardBtn = uicls.ButtonIcon(name='goForwardBtn', parent=cont, align=uiconst.TORIGHT, width=16, iconSize=16, padRight=5, texturePath='res:/UI/Texture/icons/38_16_224.png', func=self.OnForward, hint=localization.GetByLabel('UI/Control/EveWindow/Next'))
        self.goBackBtn = uicls.ButtonIcon(name='goBackBtn', parent=cont, align=uiconst.TORIGHT, width=16, iconSize=16, texturePath='res:/UI/Texture/icons/38_16_223.png', func=self.OnBack, hint=localization.GetByLabel('UI/Control/EveWindow/Previous'))
        self.UpdateHistoryButtons()
        self.subCaptionCont = uicls.Container(name='subCaptionCont', parent=cont, clipChildren=True)
        self.subCaptionLabel = uicls.Label(name='subCaptionLabel', parent=self.subCaptionCont, align=uiconst.CENTERLEFT, fontsize=11, state=uiconst.UI_NORMAL)
        self.subCaptionCont._OnResize = self.UpdateSubCaptionLabel
        self.quickFilter = uicls.InvContQuickFilter(parent=self.topRightCont2, align=uiconst.TORIGHT, width=120)
        self.capacityGauge = uicls.InvContCapacityGauge(parent=self.topRightCont2, align=uiconst.TOALL, padding=(2, 5, 4, 4))
        self.totalPriceLabel = uicls.Label(name='totalPriceLabel', parent=self.bottomRightLabelCont, align=uiconst.BOTTOMRIGHT, left=5, top=4)
        self.numItemsLabel = uicls.Label(name='numItemsLabel', parent=self.bottomRightLabelCont, align=uiconst.BOTTOMRIGHT, left=5, top=20)
        isExpanded = self.IsInvTreeExpanded(getDefault=False)
        self.isTreeExpandedStateDetermined = False if isExpanded is None else True
        if not isExpanded:
            self.CollapseTree(animate=False)
        else:
            self.ExpandTree(animate=False)
        if not settings.user.ui.Get('invFiltersExpanded_%s' % self.GetWindowSettingsID(), False):
            self.CollapseFilters(animate=False)
        else:
            self.ExpandFilters(animate=False)
        if not self.currInvID:
            self.currInvID = settings.user.ui.Get('invLastOpenContainerData_%s' % self.GetWindowSettingsID(), None)
        self.ShowInvContLoadingWheel()
        uthread.new(self.ConstructFilters)
        uthread.new(self.RefreshTree)

    def InventorySettings(self, menuParent):
        openSecondary = settings.user.ui.Get('openSecondaryInv', False)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Inventory/AlwaysOpenSeparate'), checked=openSecondary, callback=(self.OnSettingChangedSecondaryWnd, not openSecondary))
        keepQuickFilterInput = settings.user.ui.Get('keepInvQuickFilterInput', False)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Inventory/KeepQuickFilterValue'), checked=keepQuickFilterInput, callback=(self.OnSettingChangedKeepQuickFilter, not keepQuickFilterInput))
        alwaysShowFullTree = settings.user.ui.Get('alwaysShowFullInvTree', False)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Inventory/AlwaysShowFullTree'), checked=alwaysShowFullTree, callback=(self.OnSettingChangedAlwaysShowFullTree, not alwaysShowFullTree))

    def OnSettingChangedSecondaryWnd(self, openSecondary, *args):
        settings.user.ui.Set('openSecondaryInv', openSecondary)

    def OnSettingChangedKeepQuickFilter(self, keepQuickFilterInput, *args):
        settings.user.ui.Set('keepInvQuickFilterInput', keepQuickFilterInput)

    def OnSettingChangedAlwaysShowFullTree(self, alwaysShowFullTree, *args):
        settings.user.ui.Set('alwaysShowFullInvTree', alwaysShowFullTree)
        sm.ScatterEvent('OnShowFullInvTreeChanged')

    def OnShowFullInvTreeChanged(self):
        self.RefreshTree()

    def GetRegisteredPositionAndSize(self):
        return self.GetRegisteredPositionAndSizeByClass(self.windowID)

    def RegisterPositionAndSize(self, key = None, windowID = None):
        windowID = self.windowID[0]
        uicls.Window.RegisterPositionAndSize(self, key, windowID)

    def OnCreateFilterBtn(self, *args):
        sm.GetService('itemFilter').CreateFilter()

    def ShowTreeLoadingWheel(self):
        if self.loadingTreeView:
            return
        self.loadingTreeView = True
        uthread.new(self._ShowTreeLoadingWheel)

    def _ShowTreeLoadingWheel(self):
        blue.synchro.SleepWallclock(500)
        wheelCont = uicls.Container(parent=self.dividerCont.mainCont)
        wheel = uicls.LoadingWheel(parent=wheelCont, align=uiconst.CENTER)
        while self.loadingTreeView:
            blue.synchro.Yield()

        wheelCont.Close()

    def HideTreeLoadingWheel(self):
        self.loadingTreeView = False

    def ShowInvContLoadingWheel(self):
        if self.loadingInvCont:
            return
        self.loadingInvCont = True
        uthread.new(self._ShowInvContLoadingWheel)

    def _ShowInvContLoadingWheel(self):
        blue.synchro.SleepWallclock(500)
        wheel = uicls.LoadingWheel(parent=self.rightCont, align=uiconst.CENTER)
        while self.loadingInvCont:
            blue.synchro.Yield()

        wheel.Close()

    def HideInvContLoadingWheel(self):
        self.loadingInvCont = False

    def OnInvFiltersChanged(self):
        self.ConstructFilters()
        self.UpdateFilters()

    @telemetry.ZONE_METHOD
    def ConstructFilters(self):
        for filterEntry in self.filterEntries:
            filterEntry.Close()

        self.filterEntries = []
        for filt in sm.GetService('itemFilter').GetFilters():
            filterEntry = uicls.FilterEntry(parent=self.filterCont, filter=filt, eventListener=self)
            self.filterEntries.append(filterEntry)

    def RemoveTreeEntry(self, entry, byUser = False, checkRemoveParent = False):
        parent = entry.data.GetParent()
        if entry.childCont:
            for childEntry in entry.childCont.children[:]:
                self.RemoveTreeEntry(childEntry)

        invID = entry.data.GetID()
        sm.GetService('inv').RemoveTemporaryInvLocation(invID, byUser)
        if invID == self.rootInvID:
            self.Close()
            return
        if invID in self.treeEntryByID:
            self.treeEntryByID.pop(invID)
        if invID in self.tempTreeEntryByID:
            self.tempTreeEntryByID.pop(invID)
        if entry.data in self.treeData.GetChildren():
            self.treeData.RemoveChild(entry.data)
        if invID == self.currInvID:
            if not self.IsInvTreeExpanded():
                self.Close()
                return
            self.ShowInvContainer(self.GetDefaultInvID())
        entry.Close()
        if checkRemoveParent and isinstance(parent, uiutil.TreeDataInvFolder) and not parent.GetChildren():
            parEntry = self.treeEntryByID.get(parent.GetID(), None)
            if parEntry:
                self.RemoveTreeEntry(parEntry, checkRemoveParent=True)

    def OnInvContScrollSelectionChanged(self, nodes):
        items = []
        for node in nodes:
            items.append(node.rec)

        self.UpdateSelectedItems(items)

    @telemetry.ZONE_METHOD
    def UpdateSelectedItems(self, items = None):
        if not session.IsItSafe():
            return
        if not self.invCont:
            return
        self.updateSelectedItemsPending = items or []
        if self.updateSelectedItemsThread:
            return
        self.updateSelectedItemsThread = uthread.new(self._UpdateSelectedItems)

    @telemetry.ZONE_METHOD
    def _UpdateSelectedItems(self):
        if self.destroyed:
            return
        try:
            while self.updateSelectedItemsPending is not None:
                if session.mutating:
                    break
                items = self.updateSelectedItemsPending
                if not items and self.invCont:
                    iskItems = self.invCont.items
                    self.UpdateIskPriceLabel(iskItems)
                else:
                    self.UpdateIskPriceLabel(items)
                self.capacityGauge.SetSecondaryVolume(items)
                self.capacityGauge.SetAdditionalVolume()
                self.UpdateNumberOfItems(items)
                self.updateSelectedItemsPending = None
                blue.synchro.SleepWallclock(500)

        finally:
            self.updateSelectedItemsThread = None

    def SetInvContViewMode(self, value):
        if self.invCont:
            self.invCont.ChangeViewMode(value)
        self.UpdateSelectedItems()

    @telemetry.ZONE_METHOD
    def UpdateNumberOfItems(self, items = None):
        items = items or []
        numFiltered = self.invCont.numFilteredItems
        if numFiltered:
            text = '<color=#FF00FF00>'
            numFilteredTxt = localization.GetByLabel('UI/Inventory/NumFiltered', numFiltered=numFiltered)
        else:
            text = numFilteredTxt = ''
        numTotal = len(self.invCont.invController.GetItems()) - numFiltered
        numSelected = len(items)
        if numSelected:
            text += localization.GetByLabel('UI/Inventory/NumItemsAndSelected', numItems=numTotal, numSelected=numSelected, numFilteredTxt=numFilteredTxt)
        else:
            text += localization.GetByLabel('UI/Inventory/NumItems', numItems=numTotal, numFilteredTxt=numFilteredTxt)
        self.numItemsLabel.text = text

    def OnInvContDragEnter(self, invID, nodes):
        if not session.IsItSafe():
            return
        if invID != self.currInvID or self.invCont is None:
            return
        items = []
        itemIDs = [ item.itemID for item in self.invCont.invController.GetItems() ]
        for node in nodes:
            if getattr(node, 'item', None):
                if self.invController.IsItemHereVolume(node.item):
                    return
                items.append(node.item)

        self.capacityGauge.SetAdditionalVolume(items)

    def OnInvContDragExit(self, invID, nodes):
        if not session.IsItSafe():
            return
        self.capacityGauge.SetAdditionalVolume()

    @telemetry.ZONE_METHOD
    def UpdateIskPriceLabel(self, items):
        total = 0
        for item in items:
            if item is None:
                continue
            price = util.GetAveragePrice(item)
            if price:
                total += price * item.stacksize

        text = localization.GetByLabel('UI/Inventory/EstIskPrice', iskString=util.FmtISKAndRound(total, False))
        self.totalPriceLabel.text = text

    def UpdateSpecialActionButtons(self):
        self.specialActionsCont.Flush()
        actions = self.invCont.invController.GetSpecialActions()
        for label, func, name in actions:
            button = uicls.Button(parent=self.specialActionsCont, label=label, func=func, align=uiconst.TOLEFT, name=name)
            self.invCont.RegisterSpecialActionButton(button)

    def RegisterID(self, entry, id):
        if id in self.treeEntryByID:
            raise ValueError('Duplicate inventory location ids: %s' % repr(id))
        self.treeEntryByID[id] = entry

    def UnregisterID(self, id):
        if id in self.treeEntryByID:
            self.treeEntryByID.pop(id)

    def OnTreeViewClick(self, entry, *args):
        if session.solarsystemid and hasattr(entry.data, 'GetItemID'):
            itemID = entry.data.GetItemID()
            bp = sm.GetService('michelle').GetBallpark()
            if bp and itemID in bp.slimItems:
                sm.GetService('state').SetState(itemID, state.selected, 1)
                if uicore.cmd.ExecuteCombatCommand(itemID, uiconst.UI_CLICK):
                    return
        if hasattr(entry.data, 'OpenNewWindow') and uicore.uilib.Key(uiconst.VK_SHIFT) and entry.canAccess:
            entry.data.OpenNewWindow()
        elif isinstance(entry.data, uiutil.TreeDataInv) and entry.data.HasInvCont():
            self.ShowInvContainer(entry.data.GetID())
        elif entry.data.HasChildren():
            entry.ToggleChildren()

    def OnTreeViewDblClick(self, entry, *args):
        if isinstance(entry.data, uiutil.TreeDataInv) and entry.data.HasInvCont():
            if settings.user.ui.Get('openSecondaryInv', False) and entry.canAccess:
                entry.data.OpenNewWindow()
            else:
                entry.ToggleChildren()

    def OnTreeViewMouseEnter(self, entry, *args):
        if not session.solarsystemid:
            return
        if hasattr(entry.data, 'GetItemID'):
            sm.GetService('state').SetState(entry.data.GetItemID(), state.mouseOver, 1)

    def OnTreeViewMouseExit(self, entry, *args):
        if not session.solarsystemid:
            return
        if hasattr(entry.data, 'GetItemID'):
            sm.GetService('state').SetState(entry.data.GetItemID(), state.mouseOver, 0)

    def OnTreeViewDragEnter(self, entry, dragObj, nodes):
        self.dragHoverThread = uthread.new(self._OnTreeViewDragEnter, entry, dragObj, nodes)

    def OnTreeViewDragExit(self, entry, dragObj, nodes):
        sm.ScatterEvent('OnInvContDragExit', dragObj, nodes)
        if self.dragHoverThread:
            self.dragHoverThread.kill()
            self.dragHoverThread = None

    def _OnTreeViewDragEnter(self, entry, dragObj, nodes):
        blue.synchro.SleepWallclock(1000)
        if uicore.uilib.mouseOver == entry and uicore.uilib.leftbtn:
            entry.ToggleChildren(True)

    def OnTreeViewGetDragData(self, entry):
        self.dragOpenNewWindowCookie = uicore.uilib.RegisterForTriuiEvents(uiconst.UI_MOUSEMOVEDRAG, self.OnGlobalDragExit, entry)

    def OnGlobalDragExit(self, entry, *args):
        if not uicore.IsDragging():
            return False
        else:
            mo = uicore.uilib.mouseOver
            if uiutil.IsUnder(mo, self) or mo == self:
                return True
            if entry.canAccess and hasattr(entry.data, 'OpenNewWindow'):
                entry.CancelDrag()
                windowID = form.Inventory.GetWindowIDFromInvID(entry.data.GetID())
                wnd = uicore.registry.GetWindow(windowID)
                if wnd and wnd.InStack():
                    wnd.GetStack().RemoveWnd(wnd, (0, 5), dragging=True)
                elif wnd:
                    uthread.new(wnd._OpenDraggingThread)
                else:
                    uthread.new(entry.data.OpenNewWindow, True)
            return False

    @telemetry.ZONE_METHOD
    def ShowInvContainer(self, invID, branchHistory = True):
        if invID and not self.IsInvIDLegit(invID):
            invID = self.GetDefaultInvID(startFromInvID=invID)
            if invID not in self.treeEntryByID:
                invID = None
        if invID is None:
            if self.invCont:
                self.invCont.Close()
                self.invCont = None
            self.noInventoryLabel.Show()
            self.HideInvContLoadingWheel()
            self.ExpandTree(animate=False)
            return
        self.noInventoryLabel.Hide()
        if self.invCont is not None and invID == self.invCont.invController.GetInvID():
            return
        entry = self.treeEntryByID.get(invID, None)
        if entry is None:
            return
        try:
            entry.data.invController.GetItems()
        except UserError:
            self.HideInvContLoadingWheel()
            if not self.invCont:
                self.ShowInvContainer(self.GetDefaultInvID())
            raise 

        if self.invCont:
            self.invCont.Close()
        self.ShowInvContLoadingWheel()
        if settings.user.ui.Get('keepInvQuickFilterInput', False):
            quickFilterInput = self.quickFilter.GetQuickFilterInput()
        else:
            quickFilterInput = None
        self.invCont = entry.data.GetInvCont(parent=self.rightCont, activeFilters=self.GetActiveFilters(), name=self.GetWindowSettingsID(), quickFilterInput=quickFilterInput)
        self.invController = self.invCont.invController
        self.HideInvContLoadingWheel()
        self.capacityGauge.SetInvCont(self.invCont)
        self.invCont.scroll.OnSelectionChange = self.OnInvContScrollSelectionChanged
        self.UpdateIskPriceLabel(self.invCont.invController.GetItems())
        self.UpdateSpecialActionButtons()
        self.quickFilter.SetInvCont(self.invCont)
        self.viewBtns.UpdateButtons(['icons', 'details', 'list'].index(self.invCont.viewMode))
        if branchHistory:
            self.history.Append(invID)
            self.UpdateHistoryButtons()
        self.currInvID = invID
        self.RegisterLastOpenInvID(invID)
        self.UpdateSelectedState()
        self.UpdateSubCaptionLabel()
        self.UpdateNumberOfItems()
        self.UpdateCapacityGaugeCompactMode()

    def GetMenu(self):
        m = []
        if session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            m.append(('GM / WM Extras', ('isDynamic', self.GetGMMenu, ())))
        m.extend(uicls.Window.GetMenu(self))
        return m

    def GetGMMenu(self):
        return [('Clear client inventory cache', sm.GetService('invCache').InvalidateCache, ()), ('Toggle inventory priming debug mode (Red means primed)', self.ToggleInventoryPrimingDebug, ())]

    def ToggleInventoryPrimingDebug(self):
        isOn = settings.user.ui.Get('invPrimingDebugMode', False)
        settings.user.ui.Set('invPrimingDebugMode', not isOn)

    def OnBack(self):
        invID = self.history.GoBack()
        if invID:
            if invID in self.treeEntryByID:
                if uicore.uilib.mouseOver != self.goBackBtn:
                    self.goBackBtn.Blink()
                self.ShowInvContainer(invID, branchHistory=False)
            else:
                self.history.GoForward()
            self.UpdateHistoryButtons()

    def OnForward(self):
        invID = self.history.GoForward()
        if invID:
            if invID in self.treeEntryByID:
                if uicore.uilib.mouseOver != self.goForwardBtn:
                    self.goForwardBtn.Blink()
                self.ShowInvContainer(invID, branchHistory=False)
            else:
                self.history.GoBack()
            self.UpdateHistoryButtons()

    def UpdateHistoryButtons(self):
        if self.history.IsBackEnabled():
            self.goBackBtn.Enable()
        else:
            self.goBackBtn.Disable()
        if self.history.IsForwardEnabled():
            self.goForwardBtn.Enable()
        else:
            self.goForwardBtn.Disable()

    def OnResize_(self, *args):
        if self.InStack():
            width = self.GetStack().width
        else:
            width = self.width
        self.dividerCont.SetMaxSize(width - 10)
        self.treeBottomCont.UpdateSize()

    def OnDividerContResize(self):
        minWidth, minHeight = self.default_minSize
        minWidth = max(self.dividerCont.width + 10, minWidth)
        minSize = (minWidth, minHeight)
        self.SetMinSize(minSize)

    def RegisterLastOpenInvID(self, invID):
        settings.user.ui.Set('invLastOpenContainerData_%s' % self.GetWindowSettingsID(), invID)

    def SetSingleFilter(self, selectedEntry):
        for entry in self.filterEntries:
            if entry != selectedEntry:
                entry.checkbox.SetChecked(False)

    def DeselectAllFilters(self):
        for entry in self.filterEntries:
            entry.checkbox.SetChecked(False)

    def UpdateFilters(self):
        if self.invCont:
            self.SetActiveFilters(self.GetActiveFilters())

    def SetActiveFilters(self, filters):
        self.invCont.SetFilters(filters)
        if filters:
            uicore.animations.FadeIn(self.filtersEnabledBtnColor, 0.9, curveType=uiconst.ANIM_OVERSHOT)
        else:
            uicore.animations.FadeOut(self.filtersEnabledBtnColor)

    def OnInvContRefreshed(self, invCont):
        if self.invCont == invCont:
            self.UpdateSelectedItems()

    def GetActiveFilters(self):
        filters = []
        for filterEntry in self.filterEntries:
            flt = filterEntry.GetFilter()
            if flt:
                filters.append(flt)

        return filters

    def UpdateSubCaptionLabel(self, *args):
        entry = self.treeEntryByID.get(self.currInvID, None)
        if not entry:
            return
        currData = entry.data
        dataList = currData.GetAncestors()
        dataList.append(currData)
        self.breadcrumbInvIDs = []
        text = ''
        for i, data in enumerate(dataList[1:]):
            if data != currData:
                text += '<url=localsvc:service=inv&method=OnBreadcrumbTextClicked&linkNum=%d&windowID1=%s&windowID2=%s>' % (i, self.windowID[0], self.windowID[1])
                text += '<color=#55FFFFFF>' + data.GetLabel() + ' > </color></url>'
                self.breadcrumbInvIDs.append(data.GetID())
            else:
                text += data.GetLabel()

        w, h = self.subCaptionCont.GetAbsoluteSize()
        lw, lh = uicls.Label.MeasureTextSize(text)
        if w < lw:
            text = entry.data.GetLabel()
        self.subCaptionLabel.SetText(text)

    def OnBreadcrumbLinkClicked(self, linkNum):
        invID = self.breadcrumbInvIDs[linkNum]
        if self.IsInvIDLegit(invID):
            self.ShowInvContainer(invID)

    def GetNeocomGroupIcon(self):
        return 'ui_1337_64_15'

    def GetNeocomGroupLabel(self):
        return localization.GetByLabel('UI/Neocom/InventoryBtn')

    def GetDefaultWndIcon(self):
        if self.invController:
            return self.invController.GetIconName()
        return self.default_iconNum

    def GetWindowSettingsID(self):
        if isinstance(self.windowID, tuple):
            return self.windowID[0]
        else:
            return self.windowID

    @staticmethod
    def GetWindowIDFromInvID(invID = None):
        if invID is None:
            if session.stationid2:
                return ('InventoryStation', None)
            else:
                return ('InventorySpace', None)
        else:
            invCtrlName = invID[0]
            if invID == ('ShipCargo', util.GetActiveShip()):
                return ('ActiveShipCargo', None)
            if invCtrlName in ('StationContainer', 'ShipCargo', 'ShipDroneBay'):
                return ('%s_%s' % invID, invID[1])
            if invCtrlName in ('StationCorpHangar', 'POSCorpHangar'):
                return ('%s_%s_%s' % invID, None)
            if invCtrlName in 'StationCorpHangars':
                return ('%s_%s' % invID, None)
            return ('%s' % invID[0], invID[1])

    @staticmethod
    def OpenOrShow(invID = None, usePrimary = True, toggle = False, openFromWnd = None, **kw):
        if uicore.uilib.Key(uiconst.VK_SHIFT) or settings.user.ui.Get('openSecondaryInv', False):
            usePrimary = False
            openFromWnd = None
        if usePrimary and (not form.Inventory.IsPrimaryInvTreeExpanded() or form.Inventory.IsPrimaryInvCompacted()):
            usePrimary = False
        if openFromWnd:
            if not isinstance(openFromWnd, form.Inventory):
                openFromWnd = None
            else:
                usePrimary = False
        if invID:
            invController = invCtrl.GetInvCtrlFromInvID(invID)
            if invController and not invController.IsPrimed():
                invController.GetItems()
        if invID and not usePrimary:
            if invID == ('ShipCargo', util.GetActiveShip()):
                cls = form.ActiveShipCargo
            else:
                cls = getattr(form, invID[0], form.Inventory)
            windowID = form.Inventory.GetWindowIDFromInvID(invID)
            scope = None
            rootInvID = invID
        else:
            cls = form.InventoryPrimary
            windowID = form.Inventory.GetWindowIDFromInvID(None)
            if session.stationid2:
                scope = 'station'
            else:
                scope = 'space'
            rootInvID = None
        if toggle:
            wnd = cls.ToggleOpenClose(windowID=windowID, scope=scope, invID=invID, rootInvID=rootInvID, **kw)
        else:
            if openFromWnd:
                wnd = openFromWnd
            else:
                wnd = cls.GetIfOpen(windowID=windowID)
            if wnd:
                wnd.Maximize()
                if wnd.currInvID != invID:
                    if invID not in wnd.treeEntryByID:
                        wnd.RefreshTree(invID)
                    else:
                        wnd.ShowInvContainer(invID)
            else:
                wnd = cls.Open(windowID=windowID, scope=scope, invID=invID, rootInvID=rootInvID, **kw)
        if wnd:
            wnd.ScrollToActiveEntry()
        return wnd

    def ScrollToActiveEntry(self):
        uthread.new(self._ScrollToActiveEntry)

    def _ScrollToActiveEntry(self):
        blue.synchro.Yield()
        entry = self.treeEntryByID.get(self.currInvID, None)
        if not entry:
            return
        _, topEntry = entry.GetAbsolutePosition()
        _, topScroll, _, height = self.tree.mainCont.GetAbsolute()
        denum = height - entry.topRightCont.height
        if denum:
            fraction = float(topEntry - topScroll) / denum
            self.tree.ScrollToVertical(fraction)

    def OnDropData(self, dragObj, nodes):
        if self.invCont:
            return self.invCont.OnDropData(dragObj, nodes)

    def OnTreeViewDropData(self, entry, obj, nodes):
        if self.dragHoverThread:
            self.dragHoverThread.kill()
            self.dragHoverThread = None
        if self.dragOpenNewWindowCookie:
            uicore.uilib.UnregisterForTriuiEvents(self.dragOpenNewWindowCookie)
            self.dragOpenNewWindowCookie = None
        if isinstance(entry.data, uiutil.TreeDataInv):
            sm.ScatterEvent('OnInvContDragExit', obj, nodes)
            uthread.new(self._MoveItems, entry, nodes)

    def _MoveItems(self, entry, nodes):
        if not nodes:
            return
        if isinstance(nodes[0], uiutil.TreeDataInv):
            item = nodes[0].invController.GetInventoryItem()
        else:
            item = getattr(nodes[0], 'item', None)
        if item and entry.data.invController.IsItemHere(item):
            return
        if entry.data.invController.OnDropData(nodes):
            entry.Blink()

    def GetTreeEntryByItemID(self, itemID):
        ret = []
        for id, entry in self.treeEntryByID.iteritems():
            if hasattr(entry.data, 'GetItemID') and entry.data.GetItemID() == itemID:
                ret.append(entry)

        return ret

    @telemetry.ZONE_METHOD
    def GetInvLocationTreeData(self):
        data = []
        shipID = util.GetActiveShip()
        typeID = None
        if shipID:
            if session.stationid2:
                activeShip = invCtrl.StationShips().GetActiveShip()
                if activeShip:
                    typeID = activeShip.typeID
            else:
                godmaLoc = sm.GetService('clientDogmaIM').GetDogmaLocation()
                if shipID in godmaLoc.dogmaItems:
                    typeID = godmaLoc.dogmaItems[shipID].typeID
            if typeID:
                data.append(uiutil.TreeDataShip(clsName='ShipCargo', itemID=shipID, typeID=typeID, cmdName='OpenCargoHoldOfActiveShip'))
        if session.stationid2:
            stationData = []
            shipsData = []
            activeShipID = util.GetActiveShip()
            singletonShips = [ ship for ship in invCtrl.StationShips().GetItems() if ship.singleton == 1 and ship.itemID != activeShipID ]
            cfg.evelocations.Prime([ ship.itemID for ship in singletonShips ])
            for ship in singletonShips:
                shipsData.append(uiutil.TreeDataShip(clsName='ShipCargo', itemID=ship.itemID, typeID=ship.typeID))

            SortData(shipsData)
            data.append(uiutil.TreeDataInv(clsName='StationShips', itemID=session.stationid2, children=shipsData, cmdName='OpenShipHangar'))
            containersData = GetContainerDataFromItems(invCtrl.StationItems().GetItems())
            data.append(uiutil.TreeDataInv(clsName='StationItems', itemID=session.stationid2, children=containersData, cmdName='OpenHangarFloor'))
            if sm.GetService('corp').GetOffice() is not None:
                forceCollapsedMembers = not (self.rootInvID and self.rootInvID[0] in ('StationCorpMember', 'StationCorpMembers'))
                forceCollapsed = not (self.rootInvID and self.rootInvID[0] in ('StationCorpHangar', 'StationCorpHangars'))
                data.append(uiutil.TreeDataStationCorp(forceCollapsed=forceCollapsed, forceCollapsedMembers=forceCollapsedMembers))
            deliveryRoles = const.corpRoleAccountant | const.corpRoleJuniorAccountant | const.corpRoleTrader
            if session.corprole & deliveryRoles > 0:
                data.append(uiutil.TreeDataInv(clsName='StationCorpDeliveries', itemID=session.stationid2, cmdName='OpenCorpDeliveries'))
        elif session.solarsystemid:
            starbaseData = []
            defensesData = []
            industryData = []
            hangarData = []
            infrastrcutureData = []
            bp = sm.GetService('michelle').GetBallpark()
            if bp:
                for slimItem in bp.slimItems.values():
                    itemID = slimItem.itemID
                    groupID = slimItem.groupID
                    haveAccess = bool(slimItem) and (slimItem.ownerID == session.charid or slimItem.ownerID == session.corpid or session.allianceid and slimItem.allianceID == session.allianceid)
                    isAnchored = not bp.balls[itemID].isFree
                    if not haveAccess or not isAnchored:
                        continue
                    if groupID == const.groupControlTower:
                        towerData = [uiutil.TreeDataInv(clsName='POSStrontiumBay', itemID=itemID), uiutil.TreeDataInv(clsName='POSFuelBay', itemID=itemID)]
                        starbaseData.append(uiutil.TreeDataCelestialParent(clsName='BaseCelestialContainer', itemID=itemID, children=towerData, iconName='ui_7_64_10'))
                    elif groupID == const.groupCorporateHangarArray:
                        hangarData.append(uiutil.TreeDataPOSCorp(slimItem=slimItem))
                    elif groupID == const.groupAssemblyArray:
                        industryData.append(uiutil.TreeDataPOSCorp(slimItem=slimItem))
                    elif groupID == const.groupMobileLaboratory:
                        industryData.append(uiutil.TreeDataPOSCorp(slimItem=slimItem))
                    elif groupID == const.groupJumpPortalArray:
                        infrastrcutureData.append(uiutil.TreeDataInv(clsName='POSJumpBridge', itemID=itemID))
                    elif groupID in (const.groupMobileMissileSentry, const.groupMobileProjectileSentry, const.groupMobileHybridSentry):
                        defensesData.append(uiutil.TreeDataInv(clsName='POSStructureCharges', itemID=itemID))
                    elif groupID == const.groupMobileLaserSentry:
                        sentryData = [uiutil.TreeDataInv(clsName='POSStructureChargeCrystal', itemID=itemID), uiutil.TreeDataInv(clsName='POSStructureChargesStorage', itemID=itemID, label=localization.GetByLabel('UI/Inflight/POS/AccessPOSCrystalStorageError'), iconName='ui_8_64_1')]
                        defensesData.append(uiutil.TreeDataCelestialParent(clsName='BaseCelestialContainer', itemID=itemID, children=sentryData, iconName='ui_13_64_9'))
                    elif groupID == const.groupShipMaintenanceArray:
                        hangarData.append(uiutil.TreeDataInv(clsName='POSShipMaintenanceArray', itemID=itemID))
                    elif groupID == const.groupSilo:
                        industryData.append(uiutil.TreeDataInv(clsName='POSSilo', itemID=itemID))
                    elif groupID == const.groupMobileReactor:
                        industryData.append(uiutil.TreeDataInv(clsName='POSMobileReactor', itemID=itemID))
                    elif groupID == const.groupRefiningArray:
                        industryData.append(uiutil.TreeDataInv(clsName='POSRefinery', itemID=itemID))
                    elif groupID in (const.groupConstructionPlatform, const.groupStationUpgradePlatform, const.groupStationImprovementPlatform):
                        industryData.append(uiutil.TreeDataInv(clsName='POSConstructionPlatform', itemID=itemID))

            if industryData:
                SortData(industryData)
                starbaseData.append(uiutil.TreeDataInvFolder(label=localization.GetByLabel('UI/Inventory/POSGroupIndustry'), children=industryData, icon='ui_33_128_2'))
            if hangarData:
                SortData(hangarData)
                starbaseData.append(uiutil.TreeDataInvFolder(label=localization.GetByLabel('UI/Inventory/POSGroupStorage'), children=hangarData, icon='ui_26_64_13'))
            if infrastrcutureData:
                SortData(infrastrcutureData)
                starbaseData.append(uiutil.TreeDataInvFolder(label=localization.GetByLabel('UI/Inventory/POSGroupInfrastructure'), children=infrastrcutureData, icon='ui_57_64_18'))
            if defensesData:
                SortData(defensesData)
                starbaseData.append(uiutil.TreeDataInvFolder(label=localization.GetByLabel('UI/Inventory/POSGroupDefenses'), children=defensesData, icon='ui_5_64_13'))
            if starbaseData:
                data.append(uiutil.TreeDataInvFolder(label=localization.GetByLabel('UI/Inventory/StarbaseStructures'), children=starbaseData, icon='ui_3_64_13'))
        return TreeData(children=data)

    def GetInvLocationTreeDataTemp(self):
        data = []
        tmpLocations = sm.GetService('inv').GetTemporaryInvLocations().copy()
        for invName, itemID in tmpLocations:
            if self.rootInvID in tmpLocations and self.rootInvID != (invName, itemID):
                continue
            if itemID == util.GetActiveShip():
                sm.GetService('inv').RemoveTemporaryInvLocation((invName, itemID))
                continue
            else:
                cls = self.GetTreeDataClassByInvName(invName)
                data.append(cls(invName, itemID=itemID, isRemovable=True))

        return TreeData(children=data)

    def ProcessTempInvLocationAdded(self, invID):
        if invID in self.treeEntryByID:
            return
        if self.rootInvID in sm.GetService('inv').GetTemporaryInvLocations():
            return
        invName, itemID = invID
        cls = self.GetTreeDataClassByInvName(invName)
        data = cls(invName, parent=self.treeDataTemp, itemID=itemID, isRemovable=True)
        self.treeDataTemp.AddChild(data)
        cls = GetTreeViewEntryClassByDataType(data)
        entry = cls(parent=self.tree, level=0, eventListener=self, data=data, settingsID=self.GetWindowSettingsID())
        self.UpdateCelestialEntryStatus(entry)

    def GetTreeDataClassByInvName(self, invName):
        if invName == 'ShipFleetHangar':
            return uiutil.TreeDataFleetHangar
        elif invName == 'ShipMaintenanceBay':
            return uiutil.TreeDataShipMaintenanceBay
        else:
            return uiutil.TreeDataInv

    def ProcessTempInvLocationRemoved(self, invID, byUser):
        if invID == self.currInvID and not byUser:
            self.Close()
        else:
            entry = self.treeEntryByID.get(invID, None)
            if entry:
                if self.treeDataTemp:
                    self.treeDataTemp.RemoveChild(entry.data)
                if entry.data.IsRemovable():
                    self.RemoveTreeEntry(entry)

    def OnSessionChanged(self, isRemote, sess, change):
        if change.keys() == ['shipid']:
            return
        self.RefreshTree()

    def _IsInventoryItem(self, item):
        if item.groupID in CONTAINERGROUPS:
            return True
        if item.categoryID == const.categoryShip:
            return True
        return False

    @telemetry.ZONE_METHOD
    def OnMultipleItemChange(self, items, change):
        self.UpdateSelectedItems()

    @telemetry.ZONE_METHOD
    def OnInvChangeAny(self, item = None, change = None):
        if not self._IsInventoryItem(item):
            return
        if item.itemID == util.GetActiveShip():
            return
        if item.categoryID == const.categoryShip and session.solarsystemid:
            return
        if const.ixSingleton in change:
            self.RefreshTree()
            return
        if not item.singleton:
            return
        if const.ixLocationID in change or const.ixFlag in change:
            if session.stationid and item.categoryID == const.categoryShip:
                if session.charid in (item.ownerID, change.get(const.ixOwnerID, None)):
                    self.RefreshTree()
            elif session.solarsystemid and item.groupID in CONTAINERGROUPS:
                ownerIDs = (item.ownerID, change.get(const.ixOwnerID, None))
                if ownerIDs[0] == ownerIDs[1] == session.corpid:
                    return
                if session.corpid in ownerIDs and session.charid not in ownerIDs:
                    return
                self.RefreshTree()
            else:
                self.RefreshTree()
        if const.ixOwnerID in change and item.typeID == const.typePlasticWrap:
            self.RefreshTree()

    @telemetry.ZONE_METHOD
    def RemoveItem(self, item):
        if session.solarsystemid and not self.invController.GetItems():
            itemID = self.invController.itemID
            bp = sm.GetService('michelle').GetBallpark()
            if bp and itemID in bp.slimItems:
                slimItem = bp.slimItems[itemID]
                if slimItem.groupID in invCtrl.LOOT_GROUPS:
                    self.RemoveWreckEntryOrClose()

    def OnWreckLootAll(self, invID, items):
        if invID == self.currInvID:
            self.RemoveWreckEntryOrClose()
        treeEntry = self.treeEntryByID.get(('ShipCargo', util.GetActiveShip()))
        if treeEntry and items:
            treeEntry.Blink()

    def RemoveWreckEntryOrClose(self):
        if self.IsInvTreeExpanded():
            entry = self.treeEntryByID.get(self.currInvID, None)
            if entry:
                self.SwitchToOtherLootable(entry)
                if entry.data.IsRemovable():
                    self.RemoveTreeEntry(entry, byUser=True)
        else:
            self.CloseByUser()

    def SwitchToOtherLootable(self, oldEntry):
        lootableData = [ data for data in self.treeDataTemp.GetChildren() if data.GetID()[0] in ('ItemWreck', 'ItemFloatingCargo') ]
        if oldEntry.data not in lootableData:
            return
        idx = lootableData.index(oldEntry.data)
        lootableData.remove(oldEntry.data)
        if lootableData:
            newIdx = min(len(lootableData) - 1, idx)
            invID = lootableData[newIdx].GetID()
            self.ShowInvContainer(invID)

    def OnStateChange(self, itemID, flag, isSet, *args):
        if flag == state.flagWreckEmpty:
            invID = self.currInvID
            entries = self.GetTreeEntryByItemID(itemID)
            for entry in entries:
                self.RemoveTreeEntry(entry)

    def OnSlimItemChange(self, oldSlim, newSlim):
        if util.IsStructure(newSlim.categoryID):
            if oldSlim.posState != newSlim.posState:
                self.RefreshTree()

    def OnCapacityChange(self, itemID):
        if self.invController and itemID == self.invController.itemID:
            self.UpdateSelectedItems()
            self.capacityGauge.RefreshCapacity()

    def DoBallsAdded(self, data):
        for ball, slimItem in data:
            if slimItem.categoryID == const.categoryStructure:
                self.RefreshTree()
                return

    def DoBallRemove(self, ball, slimItem, terminal):
        uthread.new(self._DoBallRemove, ball, slimItem, terminal)

    def _DoBallRemove(self, ball, slimItem, terminal):
        invID = ('ShipCargo', util.GetActiveShip())
        for entry in self.GetTreeEntryByItemID(slimItem.itemID):
            if entry.data.GetID() == invID:
                continue
            if entry.data.IsDescendantOf(invID):
                continue
            self.RemoveTreeEntry(entry, checkRemoveParent=True)

    def OnFiltersEnabledBtnClicked(self, *args):
        for filterEntry in self.filterEntries:
            filterEntry.checkbox.SetChecked(False)

    def OnItemNameChange(self, *args):
        self.RefreshTree()

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        self.RefreshTree()

    def Compact(self):
        uicls.Window.Compact(self)
        for cont in self.GetCompactToggleContainers():
            cont.Hide()

        if self.IsInvTreeExpanded():
            self.sr.main.padding = (3, 3, 0, 4)
        else:
            self.sr.main.padding = (-1, 3, 0, 4)
        self.UpdateCapacityGaugeCompactMode()
        self.DeselectAllFilters()
        if self.invCont:
            self.quickFilter.ClearFilter()

    def UnCompact(self):
        uicls.Window.UnCompact(self)
        for cont in self.GetCompactToggleContainers():
            cont.Show()

        self.sr.main.padding = 1
        self.UpdateCapacityGaugeCompactMode()

    def UpdateCapacityGaugeCompactMode(self):
        if self.invController is None:
            return
        if self.IsCompact():
            if self.invController.hasCapacity:
                self.topRightCont2.Show()
                self.capacityGauge.padding = (1, 0, 0, 0)
                self.capacityGauge.HideLabel()
                self.topRightCont2.height = 5
            else:
                self.topRightCont2.Hide()
        else:
            self.topRightCont2.Show()
            if self.invController.hasCapacity:
                self.capacityGauge.padding = (2, 5, 4, 4)
                self.capacityGauge.ShowLabel()
                self.topRightCont2.height = 24

    def GetCompactToggleContainers(self):
        return (self.topRightCont1,
         self.quickFilter,
         self.dividerCont,
         self.bottomRightCont)

    def OnExpandFiltersBtn(self, *args):
        if self.filterCont.pickState == uiconst.TR2_SPS_ON:
            self.CollapseFilters()
        else:
            self.ExpandFilters()

    def ExpandFilters(self, animate = True):
        self.expandFiltersBtn.icon.rotation = 0
        self.expandFiltersBtn.Disable()
        self.treeBottomCont.EnableDragResize()
        self.treeBottomCont.minSize = 100
        self.treeBottomCont.maxSize = 0.5
        if animate:
            self.tree.DisableScrollbars()
            height = settings.user.ui.Get('invFiltersHeight_%s' % self.GetWindowSettingsID(), 150)
            height = max(self.treeBottomCont.GetMinSize(), min(self.treeBottomCont.GetMaxSize(), height))
            uicore.animations.MorphScalar(self.treeBottomCont, 'height', self.treeBottomCont.height, height, duration=0.3)
            uicore.animations.FadeIn(self.filterCont, duration=0.3, sleep=True)
            self.tree.EnableScrollbars()
        self.expandFiltersBtn.Enable()
        self.filterCont.EnableScrollbars()
        self.filterCont.Enable()
        settings.user.ui.Set('invFiltersExpanded_%s' % self.GetWindowSettingsID(), True)

    def CollapseFilters(self, animate = True):
        self.filterCont.Disable()
        self.expandFiltersBtn.Disable()
        self.expandFiltersBtn.icon.rotation = pi
        self.treeBottomCont.DisableDragResize()
        self.treeBottomCont.minSize = self.treeBottomCont.maxSize = self.filterHeaderCont.height
        self.filterCont.DisableScrollbars()
        if animate:
            self.tree.DisableScrollbars()
            uicore.animations.MorphScalar(self.treeBottomCont, 'height', self.treeBottomCont.height, self.filterHeaderCont.height, duration=0.3)
            uicore.animations.FadeOut(self.filterCont, duration=0.3, sleep=True)
            self.tree.EnableScrollbars()
        else:
            self.treeBottomCont.height = self.filterHeaderCont.height
        self.treeBottomCont.height = self.filterHeaderCont.height
        self.expandFiltersBtn.Enable()
        settings.user.ui.Set('invFiltersExpanded_%s' % self.GetWindowSettingsID(), False)

    def Paste(self, value):
        if self.invCont:
            self.invCont.Paste(value)

    def OnOfficeRentalChanged(self, *args):
        self.RefreshTree()

    @telemetry.ZONE_METHOD
    def RefreshTree(self, invID = None):
        if invID:
            self.currInvID = invID
        if self.refreshTreeThread:
            self.refreshTreeThread.kill()
        self.refreshTreeThread = uthread.new(self._RefreshTree)

    @telemetry.ZONE_METHOD
    def _RefreshTree(self):
        if self.destroyed:
            return
        if self.invCont:
            self.invCont.Disable()
        self.tree.Disable()
        try:
            self.ConstructTree()
        finally:
            self.tree.Enable()
            if self.invCont:
                self.invCont.Enable()

        self.UpdateRangeUpdater()
        self.UpdateSubCaptionLabel()

    def IsInvIDLegit(self, invID):
        data = self.treeData.GetDescendants().get(invID, None)
        if data is None:
            data = self.treeDataTemp.GetDescendants().get(invID, None)
        if invID == self.treeData.GetID():
            data = self.treeData
        return data is not None and isinstance(data, TreeDataInv) and data.HasInvCont()

    def GetDefaultInvID(self, startFromInvID = None):
        treeData = None
        if startFromInvID:
            treeData = self.treeData.GetChildByID(startFromInvID) or self.treeData
        else:
            treeData = self.treeData
        invID = self._GetDefaultInvID([treeData])
        if startFromInvID and invID is None:
            return self.GetDefaultInvID()
        else:
            return invID

    def _IsValidDefaultInvID(self, data):
        if isinstance(data, TreeDataInv) and data.HasInvCont():
            invController = invCtrl.GetInvCtrlFromInvID(data.GetID())
            if invController.IsInRange():
                return True
        return False

    def _GetDefaultInvID(self, dataNodes):
        settingsInvID = settings.user.ui.Get('invLastOpenContainerData_%s' % self.GetWindowSettingsID(), None)
        if settingsInvID:
            for data in dataNodes:
                if data.GetID() == settingsInvID and self._IsValidDefaultInvID(data):
                    return data.GetID()

        for data in dataNodes:
            if self._IsValidDefaultInvID(data):
                return data.GetID()
            if data.HasChildren():
                ret = self._GetDefaultInvID(data.GetChildren())
                if ret:
                    return ret

    def ConstructTree(self):
        self.treeEntryByID = {}
        self.tree.Flush()
        self.ShowTreeLoadingWheel()
        try:
            self.treeData = self.GetInvLocationTreeData()
        except RuntimeError as e:
            if e.args[0] == 'CharacterNotAtStation':
                return
            raise 

        self.treeDataTemp = self.GetInvLocationTreeDataTemp()
        if not self._caption and self.rootInvID:
            data = self.GetTreeDataByInvID(self.rootInvID)
            if data:
                self.SetCaption(data.GetLabel())
        if self.currInvID is None or not self.IsInvIDLegit(self.currInvID):
            self.currInvID = self.GetDefaultInvID(self.currInvID)
            if self.currInvID:
                invCtrl.GetInvCtrlFromInvID(self.currInvID).GetItems()
                self.treeData = self.GetInvLocationTreeData()
        if self.rootInvID and not settings.user.ui.Get('alwaysShowFullInvTree', False):
            tempData = self.treeDataTemp.GetChildByID(self.rootInvID)
            rootNodes = []
            if tempData:
                self.treeData = tempData
                rootNodes.append(self.treeData)
            else:
                childData = self.treeData.GetChildByID(self.rootInvID)
                if childData:
                    self.treeData = childData
                rootNodes.append(self.treeData)
                rootNodes.extend(self.treeDataTemp.GetChildren())
        else:
            rootNodes = self.treeData.GetChildren()
            rootNodes.extend(self.treeDataTemp.GetChildren())
        if not self.isTreeExpandedStateDetermined:
            self.isTreeExpandedStateDetermined = True
            if self.IsInvTreeExpanded():
                self.ExpandTree(animate=False)
        self.tree.opacity = 0.0
        for data in rootNodes:
            cls = GetTreeViewEntryClassByDataType(data)
            entry = cls(parent=self.tree, level=0, eventListener=self, data=data, settingsID=self.GetWindowSettingsID())

        self.HideTreeLoadingWheel()
        uicore.animations.FadeIn(self.tree, duration=0.2)
        if self.currInvID:
            self.UpdateSelectedState()
            self.ScrollToActiveEntry()
        if self.rootInvID is not None and self.rootInvID not in self.treeEntryByID:
            self.Close()
        else:
            self.ShowInvContainer(self.currInvID)

    def UpdateSelectedState(self):
        selectedIDs = self.treeData.GetPathToDescendant(self.currInvID) or self.treeDataTemp.GetPathToDescendant(self.currInvID) or []
        selectedIDs = [ node.GetID() for node in selectedIDs ]
        if selectedIDs:
            for entry in self.treeEntryByID.values():
                entry.Update(selectedIDs=selectedIDs)

    def UpdateRangeUpdater(self):
        if session.solarsystemid is None and self.containersInRangeUpdater:
            self.containersInRangeUpdater.kill()
            self.containersInRangeUpdater = None
        elif not self.containersInRangeUpdater:
            self.containersInRangeUpdater = uthread.new(self.UpdateTreeViewEntriesInRange)

    def UpdateTreeViewEntriesInRange(self):
        while not self.destroyed:
            if session.solarsystemid is None:
                self.containersInRangeUpdater = None
                return
            self._UpdateTreeViewEntriesInRange()

    def _UpdateTreeViewEntriesInRange(self):
        for entry in self.treeEntryByID.values():
            if not entry.display or entry.IsClippedBy(self.tree):
                continue
            self.UpdateCelestialEntryStatus(entry)
            blue.pyos.BeNice()

        blue.synchro.Sleep(500)

    def UpdateCelestialEntryStatus(self, entry):
        if hasattr(entry.data, 'GetLabelWithDistance'):
            entry.label.text = entry.data.GetLabelWithDistance()
        invController = getattr(entry.data, 'invController', None)
        if invController is None:
            canAccess = True
        else:
            canAccess = invController.IsInRange()
            if isinstance(entry.data.invController, (invCtrl.ItemWreck, invCtrl.ItemFloatingCargo)):
                data = entry.data
                entry.icon.LoadIcon(data.GetIcon(), ignoreSize=True)
                slimItem = sm.GetService('michelle').GetBallpark().slimItems[data.invController.itemID]
                entry.iconColor = bracketUtils.GetIconColor(slimItem)
        entry.SetAccessability(canAccess)

    def OnExpandTreeBtn(self, *args):
        if self.dividerCont.pickState:
            self.CollapseTree()
        else:
            self.ExpandTree()
        self.OnDividerContResize()

    def GetTreeDataByInvID(self, invID):
        for root in (self.treeData, self.treeDataTemp):
            data = root.GetChildByID(invID)
            if data:
                return data

    def SetInvTreeExpandedSetting(self, isExpanded):
        if self.isTreeExpandedStateDetermined:
            settings.user.ui.Set('invTreeExpanded_%s' % self.GetWindowSettingsID(), isExpanded)

    def IsInvTreeExpanded(self, getDefault = True):
        return settings.user.ui.Get('invTreeExpanded_%s' % self.GetWindowSettingsID(), self.GetDefaultInvTreeExpanded())

    @staticmethod
    def IsPrimaryInvTreeExpanded():
        windowID = form.Inventory.GetWindowIDFromInvID(None)
        return bool(settings.user.ui.Get('invTreeExpanded_%s' % windowID[0], True))

    @staticmethod
    def IsPrimaryInvCompacted():
        windowID = form.Inventory.GetWindowIDFromInvID(None)
        return uicore.registry.GetRegisteredWindowState(windowID[0], 'compact')

    def GetDefaultInvTreeExpanded(self):
        if not self.rootInvID:
            return True
        if not self.treeData:
            return None
        data = self.treeData.GetChildByID(self.rootInvID)
        if data:
            return data.HasChildren()

    def ExpandTree(self, animate = True):
        self.expandTreeBtn.icon.rotation = -pi / 2
        self.expandTreeBtn.Disable()
        width = settings.user.ui.Get('invTreeViewWidth_%s' % self.GetWindowSettingsID(), TREE_DEFAULT_WIDTH)
        if animate:
            uicore.animations.MorphScalar(self.dividerCont, 'width', self.dividerCont.width, width, duration=0.3)
            uicore.animations.MorphScalar(self.rightCont, 'padLeft', 4, 0, duration=0.3)
            uicore.animations.FadeIn(self.dividerCont, duration=0.3, sleep=True)
        else:
            self.dividerCont.width = width
            self.rightCont.padLeft = 4
        self.rightCont.padLeft = 0
        self.expandTreeBtn.Enable()
        self.dividerCont.Enable()
        self.SetInvTreeExpandedSetting(True)

    def CollapseTree(self, animate = True):
        self.dividerCont.Disable()
        self.expandTreeBtn.Disable()
        self.expandTreeBtn.icon.rotation = pi / 2
        if animate:
            uicore.animations.MorphScalar(self.dividerCont, 'width', self.dividerCont.width, 0.0, duration=0.3)
            uicore.animations.MorphScalar(self.rightCont, 'padLeft', 0, 4, duration=0.3)
            uicore.animations.FadeOut(self.dividerCont, duration=0.3, sleep=True)
        else:
            self.rightCont.padLeft = 4
            self.dividerCont.width = 0
        self.expandTreeBtn.Enable()
        self.SetInvTreeExpandedSetting(False)


class InventoryPrimary(Inventory):
    __guid__ = 'form.InventoryPrimary'
    default_windowID = ('InventoryPrimary', None)
    default_caption = 'UI/Neocom/InventoryBtn'

    def GetDefaultWndIcon(self):
        return self.default_iconNum

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        if self.currInvID == ('ShipCargo', oldShipID):
            invID = ('ShipCargo', shipID)
        else:
            invID = None
        self.RefreshTree(invID)


class StationItems(Inventory):
    __guid__ = 'form.StationItems'
    default_windowID = ('StationItems', None)
    default_scope = 'station'
    default_iconNum = invCtrl.StationItems.iconName

    @classmethod
    def OnDropDataCls(cls, dragObj, nodes):
        return invCtrl.StationItems().OnDropData(nodes)


class StationShips(Inventory):
    __guid__ = 'form.StationShips'
    default_windowID = ('StationShips', None)
    default_scope = 'station'
    default_iconNum = invCtrl.StationShips.iconName

    @classmethod
    def OnDropDataCls(cls, dragObj, nodes):
        return invCtrl.StationShips().OnDropData(nodes)


class StationCorpHangars(Inventory):
    __guid__ = 'form.StationCorpHangars'
    default_windowID = ('StationCorpHangars', None)
    default_scope = 'station'
    default_iconNum = 'ui_1337_64_12'

    def GetDefaultWndIcon(self):
        return self.default_iconNum


class StationCorpDeliveries(Inventory):
    __guid__ = 'form.StationCorpDeliveries'
    default_windowID = ('StationCorpDeliveries', None)
    default_scope = 'station'
    default_iconNum = invCtrl.StationCorpDeliveries.iconName

    @classmethod
    def OnDropDataCls(cls, dragObj, nodes):
        return invCtrl.StationCorpDeliveries().OnDropData(nodes)


class ActiveShipCargo(Inventory):
    __guid__ = 'form.ActiveShipCargo'
    default_windowID = ('ActiveShipCargo', None)
    default_iconNum = 'ui_1337_64_14'
    default_caption = 'UI/Neocom/ActiveShipCargoBtn'

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        self.rootInvID = ('ShipCargo', shipID)
        self.RefreshTree()

    def GetDefaultWndIcon(self):
        return self.default_iconNum

    @classmethod
    def OnDropDataCls(cls, dragObj, nodes):
        return invCtrl.ShipCargo(util.GetActiveShip()).OnDropData(nodes)


class TreeViewEntry(uicls.ContainerAutoSize):
    __guid__ = 'uicls.TreeViewEntry'
    default_name = 'TreeViewEntry'
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL
    default_settingsID = ''
    LEFTPUSH = 10
    default_height = 22
    isDragObject = True
    noAccessColor = (0.33, 0.33, 0.33, 1.0)
    iconColor = util.Color.WHITE

    @telemetry.ZONE_METHOD
    def ApplyAttributes(self, attributes):
        uicls.ContainerAutoSize.ApplyAttributes(self, attributes)
        self.level = attributes.get('level', 0)
        self.data = attributes.get('data')
        self.eventListener = attributes.get('eventListener', None)
        self.parentEntry = attributes.get('parentEntry', None)
        self.settingsID = attributes.get('settingsID', self.default_settingsID)
        self.childrenInitialized = False
        self.isToggling = False
        self.canAccess = True
        self.isSelected = False
        self.childSelectedBG = False
        self.icon = None
        self.childCont = None
        self.topRightCont = uicls.Container(name='topCont', parent=self, align=uiconst.TOTOP, height=self.default_height)
        self.topRightCont.GetDragData = self.GetDragData
        left = self.GetSpacerContWidth()
        if self.data.IsRemovable():
            removeBtn = uicls.Sprite(texturePath='res:/UI/Texture/icons/73_16_210.png', parent=self.topRightCont, align=uiconst.CENTERLEFT, width=16, height=16, left=left, hint=localization.GetByLabel('UI/Common/Buttons/Close'))
            left += 20
            removeBtn.OnClick = self.Remove
        icon = self.data.GetIcon()
        if icon:
            iconSize = self.height - 2
            self.icon = uicls.Icon(icon=icon, parent=self.topRightCont, pos=(left,
             0,
             iconSize,
             iconSize), align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, ignoreSize=True)
            left += iconSize
        self.label = uicls.Label(parent=self.topRightCont, align=uiconst.CENTERLEFT, text=self.data.GetLabel(), left=left + 4)
        self.UpdateLabel()
        self.hoverBG = None
        self.selectedBG = None
        self.blinkBG = None
        if self.data.HasChildren():
            self.spacerCont = uicls.Container(name='spacerCont', parent=self.topRightCont, align=uiconst.TOLEFT, width=self.GetSpacerContWidth())
            self.toggleBtn = uicls.Container(name='toggleBtn', parent=self.spacerCont, align=uiconst.CENTERRIGHT, width=16, height=16, state=uiconst.UI_HIDDEN)
            self.toggleBtn.OnClick = self.OnToggleBtnClick
            self.toggleBtn.OnDblClick = lambda : None
            self.toggleBtnSprite = uicls.Sprite(bgParent=self.toggleBtn, texturePath='res:/UI/Texture/classes/Neocom/arrowDown.png', rotation=pi / 2, padding=(4, 4, 5, 5))
            expandChildren = False
            if not self.data.IsForceCollapsed():
                toggleSettingsDict = settings.user.ui.Get('invTreeViewEntryToggle_%s' % self.settingsID, {})
                expandChildren = toggleSettingsDict.get(self.data.GetID(), self.level < 1)
                self.ConstructChildren()
            else:
                self.toggleBtn.state = uiconst.UI_NORMAL
            self.ShowChildCont(expandChildren, animate=False)
        else:
            self.ShowChildCont(False, animate=False)
        self.eventListener.RegisterID(self, self.data.GetID())

    def GetSpacerContWidth(self):
        return (1 + self.level) * self.LEFTPUSH + 8

    def Close(self):
        self.eventListener.UnregisterID(self.data.GetID())
        if self.parentEntry and self.data in self.parentEntry.data._children:
            self.parentEntry.data._children.remove(self.data)
        uicls.ContainerAutoSize.Close(self)

    @telemetry.ZONE_METHOD
    def ConstructChildren(self):
        self.childrenInitialized = True
        children = self.data.GetChildren()
        if self.destroyed:
            return
        if self.childCont is None:
            self.childCont = uicls.ContainerAutoSize(parent=self, name='childCont', align=uiconst.TOTOP, clipChildren=True, state=uiconst.UI_HIDDEN)
        if children:
            for child in children:
                cls = GetTreeViewEntryClassByDataType(child)
                child = cls(parent=self.childCont, parentEntry=self, level=self.level + 1, eventListener=self.eventListener, data=child, settingsID=self.settingsID, state=uiconst.UI_HIDDEN)
                child.UpdateLabel()

            if self.childCont.children:
                self.childCont.children[-1].padBottom = 5
            self.toggleBtn.state = uiconst.UI_NORMAL

    def ShowChildCont(self, show = True, animate = True):
        if self.childCont is None or self.childCont.display == show or not self.data.HasChildren():
            return
        for child in self.childCont.children:
            child.display = show

        self.isToggling = True
        if animate:
            if show:
                self.childCont.display = True
                uicore.animations.Tr2DRotateTo(self.toggleBtnSprite, pi / 2, 0.0, duration=0.15)
                self.childCont.DisableAutoSize()
                _, height = self.childCont.GetAutoSize()
                uicore.animations.FadeIn(self.childCont, duration=0.3)
                uicore.animations.MorphScalar(self.childCont, 'height', self.childCont.height, height, duration=0.15, sleep=True)
                self.childCont.EnableAutoSize()
            else:
                uicore.animations.Tr2DRotateTo(self.toggleBtnSprite, 0.0, pi / 2, duration=0.15)
                self.childCont.DisableAutoSize()
                uicore.animations.FadeOut(self.childCont, duration=0.15)
                uicore.animations.MorphScalar(self.childCont, 'height', self.childCont.height, 0, duration=0.15, sleep=True)
                self.childCont.display = False
            self.toggleBtn.Enable()
        else:
            self.childCont.display = show
            if show:
                self.toggleBtnSprite.rotation = 0.0
                self.childCont.opacity = 1.0
            else:
                self.toggleBtnSprite.rotation = pi / 2
                self.childCont.DisableAutoSize()
                self.childCont.opacity = 0.0
        self.isToggling = False

    def Update(self, selectedIDs):
        invID = self.data.GetID()
        isSelected = selectedIDs[-1] == invID
        isChildSelected = not isSelected and invID in selectedIDs
        self.SetSelected(isSelected, isChildSelected)

    def SetSelected(self, isSelected, isChildSelected):
        self.isSelected = isSelected
        if isSelected or self.selectedBG:
            self.CheckConstructSelectedBG()
            self.selectedBG.display = isSelected
        self.UpdateLabel()
        if isChildSelected:
            if not self.childSelectedBG:
                self.childSelectedBG = uicls.GradientSprite(bgParent=self.spacerCont, rotation=0, rgbData=[(0, (0.5, 0.5, 0.5))], alphaData=[(0, 0.2), (1.0, 0.0)], padBottom=1)
            else:
                self.childSelectedBG.Show()
        elif self.childSelectedBG:
            self.childSelectedBG.Hide()
        if isSelected and self.parentEntry:
            self.parentEntry.ExpandFromRoot()

    @telemetry.ZONE_METHOD
    def UpdateLabel(self):
        if self.isSelected and self.canAccess:
            self.label.color = util.Color.WHITE
        elif self.canAccess:
            self.label.color = uicls.Label.default_color
        else:
            self.label.color = self.noAccessColor
        if session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            if settings.user.ui.Get('invPrimingDebugMode', False) and hasattr(self.data, 'invController') and self.data.invController.IsPrimed():
                self.label.color = util.Color.RED

    def ExpandFromRoot(self):
        self.ToggleChildren(forceShow=True)
        if self.parentEntry:
            self.parentEntry.ExpandFromRoot()

    def OnClick(self, *args):
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewClick'):
            self.eventListener.OnTreeViewClick(self, *args)

    def OnDblClick(self, *args):
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewDblClick'):
            self.eventListener.OnTreeViewDblClick(self, *args)

    def OnToggleBtnClick(self, *args):
        if not self.isToggling:
            self.ToggleChildren()

    def ToggleChildren(self, forceShow = False):
        show = forceShow or self.childCont is None or not self.childCont.display
        toggleSettingsDict = settings.user.ui.Get('invTreeViewEntryToggle_%s' % self.settingsID, {})
        toggleSettingsDict[self.data.GetID()] = show
        settings.user.ui.Set('invTreeViewEntryToggle_%s' % self.settingsID, toggleSettingsDict)
        if not self.data.HasChildren():
            return
        if not self.childrenInitialized:
            self.ConstructChildren()
        self.ShowChildCont(show)

    def GetMenu(self):
        m = self.data.GetMenu()
        if session.role & service.ROLE_PROGRAMMER:
            idString = repr(self.data.GetID())
            m.append((idString, blue.pyos.SetClipboardData, (idString,)))
        if self.data.IsRemovable():
            m.append(None)
            m.append((localization.GetByLabel('UI/Common/Buttons/Close'), self.Remove, ()))
        return m

    def GetHint(self):
        return self.data.GetHint()

    def GetFullPathLabelList(self):
        labelTuple = [self.data.GetLabel()]
        if self.parentEntry:
            labelTuple = self.parentEntry.GetFullPathLabelList() + labelTuple
        return labelTuple

    def Remove(self, *args):
        self.eventListener.RemoveTreeEntry(self, byUser=True)

    def OnMouseDown(self, *args):
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewMouseDown'):
            self.eventListener.OnTreeViewMouseDown(self, *args)

    def OnMouseUp(self, *args):
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewMouseUp'):
            self.eventListener.OnTreeViewMouseUp(self, *args)

    def CheckConstructHoverBG(self):
        if self.hoverBG is None:
            self.hoverBG = uicls.Fill(bgParent=self.topRightCont, color=util.Color.WHITE, opacity=0.0)

    def CheckConstructSelectedBG(self):
        if self.selectedBG is None:
            self.selectedBG = uicls.Fill(bgParent=self.topRightCont, color=(1.0, 1.0, 1.0, 0.1), state=uiconst.UI_HIDDEN)

    def CheckConstructBlinkBG(self):
        if self.blinkBG is None:
            self.blinkBG = uicls.Fill(bgParent=self.topRightCont, color=(1.0, 1.0, 1.0, 0.0))

    def OnMouseEnter(self, *args):
        self.CheckConstructHoverBG()
        uicore.animations.FadeIn(self.hoverBG, 0.05, duration=0.1)
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewMouseEnter'):
            self.eventListener.OnTreeViewMouseEnter(self, *args)

    def OnMouseExit(self, *args):
        self.CheckConstructHoverBG()
        uicore.animations.FadeOut(self.hoverBG, duration=0.3)
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewMouseExit'):
            self.eventListener.OnTreeViewMouseExit(self, *args)

    def OnDropData(self, *args):
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewDropData'):
            self.eventListener.OnTreeViewDropData(self, *args)

    def OnDragEnter(self, dragObj, nodes):
        self.CheckConstructHoverBG()
        uicore.animations.FadeIn(self.hoverBG, 0.05, duration=0.1)
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewDragEnter'):
            self.eventListener.OnTreeViewDragEnter(self, dragObj, nodes)

    def GetDragData(self):
        if self.data.IsDraggable():
            self.eventListener.OnTreeViewGetDragData(self)
            return [self.data]

    def OnDragExit(self, *args):
        self.CheckConstructHoverBG()
        uicore.animations.FadeOut(self.hoverBG, duration=0.1)
        if self.eventListener and hasattr(self.eventListener, 'OnTreeViewDragExit'):
            self.eventListener.OnTreeViewDragExit(self, *args)

    def Blink(self):
        self.CheckConstructBlinkBG()
        uicore.animations.FadeTo(self.blinkBG, 0.0, 0.25, duration=0.25, curveType=uiconst.ANIM_WAVE, loops=2)

    @telemetry.ZONE_METHOD
    def SetAccessability(self, canAccess):
        self.canAccess = canAccess
        if self.icon:
            self.icon.color = self.iconColor if canAccess else util.Color(*self.iconColor).SetAlpha(0.5).GetRGBA()
        self.UpdateLabel()


class TreeViewEntryAccessConfig(TreeViewEntry):
    __guid__ = 'uicls.TreeViewEntryAccessConfig'

    def ApplyAttributes(self, attributes):
        self.iconCont = None
        TreeViewEntry.ApplyAttributes(self, attributes)
        self.iconCont = uicls.ContainerAutoSize(parent=self.topRightCont, align=uiconst.CENTERLEFT, height=16)
        self.fleetAccessBtn = uicls.ButtonIcon(name='fleetAccessBtn', parent=self.iconCont, align=uiconst.TOLEFT, width=14, iconSize=14, texturePath='res:/UI/Texture/classes/Inventory/fleetAccess.png', func=self.OnFleetAccessBtn)
        self.corpAccessBtn = uicls.ButtonIcon(name='corpAccessBtn', parent=self.iconCont, align=uiconst.TOLEFT, width=14, iconSize=12, texturePath='res:/UI/Texture/classes/Inventory/corpAccess.png', func=self.OnCorpAccessBtn)
        self.UpdateFleetIcon()
        self.UpdateCorpIcon()

    def OnFleetAccessBtn(self, *args):
        if self.data.clsName == 'ShipMaintenanceBay':
            sm.GetService('shipConfig').ToggleShipMaintenanceBayFleetAccess()
            self.PlayButtonSound(sm.GetService('shipConfig').IsShipMaintenanceBayFleetAccessAllowed())
        elif self.data.clsName == 'ShipFleetHangar':
            sm.GetService('shipConfig').ToggleFleetHangarFleetAccess()
            self.PlayButtonSound(sm.GetService('shipConfig').IsFleetHangarFleetAccessAllowed())
        self.UpdateFleetIcon()

    def UpdateFleetIcon(self):
        if self.data.clsName == 'ShipMaintenanceBay':
            isAllowed = sm.GetService('shipConfig').IsShipMaintenanceBayFleetAccessAllowed()
        elif self.data.clsName == 'ShipFleetHangar':
            isAllowed = sm.GetService('shipConfig').IsFleetHangarFleetAccessAllowed()
        if isAllowed:
            hint = localization.GetByLabel('UI/Inventory/DisableAccessToFleetMembers')
        else:
            hint = localization.GetByLabel('UI/Inventory/EnableAccessToFleetMembers')
        self._UpdateButton(self.fleetAccessBtn, isAllowed, hint)

    def OnCorpAccessBtn(self, *args):
        if self.data.clsName == 'ShipMaintenanceBay':
            sm.GetService('shipConfig').ToggleShipMaintenanceBayCorpAccess()
            self.PlayButtonSound(sm.GetService('shipConfig').IsShipMaintenanceBayCorpAccessAllowed())
        elif self.data.clsName == 'ShipFleetHangar':
            sm.GetService('shipConfig').ToggleFleetHangarCorpAccess()
            self.PlayButtonSound(sm.GetService('shipConfig').IsFleetHangarCorpAccessAllowed())
        self.UpdateCorpIcon()

    def UpdateCorpIcon(self):
        if self.data.clsName == 'ShipMaintenanceBay':
            isAllowed = sm.GetService('shipConfig').IsShipMaintenanceBayCorpAccessAllowed()
        elif self.data.clsName == 'ShipFleetHangar':
            isAllowed = sm.GetService('shipConfig').IsFleetHangarCorpAccessAllowed()
        if isAllowed:
            hint = localization.GetByLabel('UI/Inventory/DisableAccessToCorpMembers')
        else:
            hint = localization.GetByLabel('UI/Inventory/EnableAccessToCorpMembers')
        self._UpdateButton(self.corpAccessBtn, isAllowed, hint)

    def _UpdateButton(self, button, isAllowed, hint):
        if isAllowed:
            color = (0.1, 1.0, 0.1, 1.0)
        else:
            color = util.Color.GetGrayRGBA(1.0, 0.5)
        button.icon.SetRGB(*color)
        button.hint = hint

    def UpdateLabel(self):
        TreeViewEntry.UpdateLabel(self)
        if self.iconCont:
            self.iconCont.left = self.label.left + self.label.width + 3

    def PlayButtonSound(self, buttonState):
        if buttonState:
            sm.GetService('audio').SendUIEvent('msg_DiodeClick_play')
        else:
            sm.GetService('audio').SendUIEvent('msg_DiodeDeselect_play')


class TreeViewEntryAccessRestricted(TreeViewEntry):
    __guid__ = 'uicls.TreeViewEntryAccessRestricted'
    ICONSIZE = 16
    COLOR_RED = (0.867, 0.0, 0.0, 1.0)
    COLOR_YELLOW = (0.984, 0.702, 0.22, 1.0)

    def ApplyAttributes(self, attributes):
        self.iconCont = None
        TreeViewEntry.ApplyAttributes(self, attributes)
        canTake = self.data.CheckCanTake()
        canQuery = self.data.CheckCanQuery()
        if not canQuery:
            texturePath = 'res:/UI/Texture/classes/Inventory/restricted.png'
            hint = localization.GetByLabel('UI/Inventory/DropAccessOnly')
            color = self.COLOR_RED
        else:
            texturePath = 'res:/UI/Texture/classes/Inventory/readOnly.png'
            hint = localization.GetByLabel('UI/Inventory/ViewAccessOnly')
            color = self.COLOR_YELLOW
        if not canTake or not canQuery:
            self.iconCont = uicls.ContainerAutoSize(parent=self.topRightCont, align=uiconst.CENTERLEFT, height=self.ICONSIZE)
            icon = uicls.Sprite(name='restrictedIcon', parent=self.iconCont, align=uiconst.TOLEFT, texturePath=texturePath, width=self.ICONSIZE, color=color, hint=hint)

    def UpdateLabel(self):
        TreeViewEntry.UpdateLabel(self)
        if self.iconCont:
            self.iconCont.left = self.topRightCont.width + self.label.left + self.label.width + 3


class FilterEntry(uicls.Container):
    __guid__ = 'uicls.FilterEntry'
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL
    default_height = 22

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.eventListener = attributes.eventListener
        self.filter = attributes.filter
        filtName, allOrAny, conditions = self.filter
        self.checkbox = uicls.Checkbox(name='checkbox', parent=self, checked=False, callback=self.OnCheckbox, align=uiconst.CENTERLEFT, left=5)
        self.label = uicls.Label(parent=self, text=filtName, align=uiconst.CENTERLEFT, left=22)
        self.hoverBG = uicls.Fill(bgParent=self, color=util.Color.WHITE, opacity=0.0)

    def OnClick(self):
        self.checkbox.ToggleState()

    def OnDblClick(self):
        self.eventListener.SetSingleFilter(self)

    def OnMouseEnter(self, *args):
        uicore.animations.FadeIn(self.hoverBG, 0.05, duration=0.1)

    def OnMouseExit(self, *args):
        uicore.animations.FadeOut(self.hoverBG, duration=0.3)

    def GetFilter(self):
        if self.checkbox.checked:
            return self.filter

    def OnCheckbox(self, checkbox):
        self.eventListener.UpdateFilters()

    def GetMenu(self):
        m = []
        m.append((localization.GetByLabel('UI/Inventory/Filters/Edit'), self.EditFilter, [self.label.text]))
        m.append((localization.GetByLabel('UI/Commands/Remove'), sm.GetService('itemFilter').RemoveFilter, [self.label.text]))
        return m

    def EditFilter(self, filterName):
        self.eventListener.DeselectAllFilters()
        sm.GetService('itemFilter').EditFilter(filterName)


class TreeData():
    __guid__ = 'uiutil.TreeData'

    def __init__(self, label = None, parent = None, children = None, icon = None, isRemovable = False, **kw):
        self._label = label
        self._children = children or []
        self._parent = parent
        for child in self._children:
            child._parent = self

        self._kw = kw
        self._icon = icon
        self._isRemovable = isRemovable

    def GetParent(self):
        return self._parent

    def GetLabel(self):
        return self._label or ''

    def GetIcon(self):
        return self._icon

    def GetMenu(self):
        return []

    def GetHint(self):
        return None

    def GetID(self):
        return (self._label, tuple(self._kw.values()))

    def GetChildren(self):
        return self._children

    def AddChild(self, child):
        self._children.append(child)

    def RemoveChild(self, child):
        if child in self._children:
            self._children.remove(child)

    def GetChildByID(self, id, recursive = True):
        if id == self.GetID():
            return self
        if self.IsForceCollapsed():
            return None
        children = self.GetChildren()
        for child in children:
            if child.GetID() == id:
                return child

        for child in children:
            ret = child.GetChildByID(id)
            if ret:
                return ret

    def IsDraggable(self):
        return False

    def HasChildren(self):
        return bool(self._children)

    def IsRemovable(self):
        return self._isRemovable

    def IsForceCollapsed(self):
        return False

    def GetPathToDescendant(self, id, forceGetChildren = False):
        if self.GetID() == id:
            return [self]
        if self.HasChildren():
            if not forceGetChildren and self.IsForceCollapsed():
                return None
            for child in self.GetChildren():
                found = child.GetPathToDescendant(id, forceGetChildren)
                if found:
                    return [self] + found

    def GetAncestors(self):
        parent = self.GetParent()
        if parent:
            ancestors = parent.GetAncestors()
            ancestors.append(parent)
            return ancestors
        else:
            return []

    def GetDescendants(self, forceGetChildren = False):
        ret = {}
        if self.HasChildren():
            if not forceGetChildren and self.IsForceCollapsed():
                return {}
            for child in self.GetChildren():
                ret[child.GetID()] = child
                ret.update(child.GetDescendants())

        return ret

    def IsDescendantOf(self, invID):
        parent = self.GetParent()
        if not parent:
            return False
        if invID == parent.GetID():
            return True
        return parent.IsDescendantOf(invID)


class TreeDataInv(TreeData):
    __guid__ = 'uiutil.TreeDataInv'

    def __init__(self, clsName, parent = None, children = None, label = None, isRemovable = False, cmdName = None, iconName = None, **kw):
        uiutil.TreeData.__init__(self, parent=parent, children=children, label=label, isRemovable=isRemovable, **kw)
        self.clsName = clsName
        self.cmdName = cmdName
        self.iconName = iconName
        self.invController = getattr(invCtrl, clsName)(**kw)

    @telemetry.ZONE_METHOD
    def GetLabel(self):
        if self._label:
            return self._label
        else:
            return self.invController.GetName()

    @telemetry.ZONE_METHOD
    def GetLabelWithDistance(self):
        label = self.GetLabel()
        if session.solarsystemid is None or self.clsName in NO_DISTANCE_SHOWN or self.invController.itemID == util.GetActiveShip():
            return label
        if session.solarsystemid:
            ball = sm.GetService('michelle').GetBallpark().GetBall(self.invController.itemID)
            if not ball:
                return label
            dist = util.FmtDist(ball.surfaceDist, 1)
            return '%s <color=#66FFFFFF>%s</color>' % (label, dist)
        return label

    def GetIcon(self):
        if self.iconName:
            return self.iconName
        return self.invController.GetIconName()

    def GetMenu(self):
        m = self.invController.GetMenu()
        if self.invController.IsInRange():
            m += [(localization.GetByLabel('UI/Inventory/OpenInNewWindow'), self.OpenNewWindow, ())]
        return m

    def GetHint(self):
        if self.cmdName:
            shortcut = uicore.cmd.GetShortcutStringByFuncName(self.cmdName)
            if shortcut:
                return localization.GetByLabel('UI/Inventory/ShortcutBrackets', shortcut=shortcut)

    def GetID(self):
        return self.invController.GetInvID()

    def GetItemID(self):
        return self.invController.itemID

    def GetInvCont(self, **kw):
        kw.update(self._kw)
        return getattr(invCont, self.clsName)(**kw)

    def HasInvCont(self):
        return True

    def OpenNewWindow(self, openDragging = False):
        return form.Inventory.OpenOrShow(invID=self.GetID(), usePrimary=False, toggle=True, openDragging=openDragging, **self._kw)

    def IsForceCollapsed(self):
        return not self.invController.IsPrimed()

    def IsDraggable(self):
        return self.invController.IsInRange()

    def CheckCanQuery(self):
        if self.clsName == 'StationContainer':
            return self.GetParent().CheckCanTake()
        return self.invController.CheckCanQuery()

    def CheckCanTake(self):
        return self.invController.CheckCanTake()


class TreeDataPlasticWrap(TreeDataInv):
    __guid__ = 'uiutil.TreeDataPlasticWrap'

    def GetChildren(self):
        data = GetContainerDataFromItems(self.invController.GetItems(), parent=self)
        if not data:
            data = [uiutil.TreeData(parent=self, label=localization.GetByLabel('UI/Inventory/NoNestedContainers'), id='none_%s' % self.invController.itemID)]
        return data

    def HasChildren(self):
        return True


def GetSharedBayHint(invController):
    if invController.itemID != util.GetActiveShip():
        hint = cfg.evelocations.Get(invController.itemID).name
        ownerID = invController.GetOwnerID()
        if ownerID:
            hint += '<br>%s' % cfg.eveowners.Get(ownerID).name
        return hint


class TreeDataFleetHangar(TreeDataInv):
    __guid__ = 'uiutil.TreeDataFleetHangar'

    def GetChildren(self):
        return GetContainerDataFromItems(self.invController.GetItems(), parent=self)

    def HasChildren(self):
        for item in self.invController.GetItems():
            if item.groupID in CONTAINERGROUPS:
                return True

        return False

    def GetHint(self):
        return GetSharedBayHint(self.invController)


class TreeDataShipMaintenanceBay(TreeDataInv):
    __guid__ = 'uiutil.TreeDataShipMaintenanceBay'

    def GetHint(self):
        return GetSharedBayHint(self.invController)


class TreeDataCelestialParent(TreeDataInv):
    __guid__ = 'uiutil.TreeDataCelestialParent'

    def HasInvCont(self, **kw):
        return False

    def IsForceCollapsed(self):
        return False


class TreeDataInvFolder(TreeData):
    __guid__ = 'uiutil.TreeDataInvFolder'

    def OpenNewWindow(self, openDragging = False):
        return form.Inventory.OpenOrShow(invID=self.GetID(), usePrimary=False, toggle=True, openDragging=openDragging, iconNum=self.GetIcon(), **self._kw)

    def GetMenu(self):
        return [(localization.GetByLabel('UI/Inventory/OpenInNewWindow'), self.OpenNewWindow, ())]

    def HasChildren(self):
        return True

    @telemetry.ZONE_METHOD
    def GetLabelWithDistance(self):
        return self.GetLabel()

    def IsDraggable(self):
        return True


class TreeDataPOSCorp(TreeDataInvFolder):
    __guid__ = 'uiutil.TreeDataPOSCorp'

    def __init__(self, slimItem, **kw):
        TreeData.__init__(self, **kw)
        self.slimItem = slimItem
        self.invController = invCtrl.POSCorpHangar(self.slimItem.itemID)

    @telemetry.ZONE_METHOD
    def GetLabel(self):
        return uix.GetSlimItemName(self.slimItem)

    @telemetry.ZONE_METHOD
    def GetLabelWithDistance(self):
        label = self.GetLabel()
        bp = sm.GetService('michelle').GetBallpark()
        ball = bp.GetBall(self.invController.itemID)
        if not ball:
            return label
        dist = util.FmtDist(ball.surfaceDist, 1)
        return '%s <color=#66FFFFFF>%s</color>' % (label, dist)

    def GetIcon(self):
        return 'ui_7_64_6'

    def GetItemID(self):
        return self.slimItem.itemID

    def GetID(self):
        return ('POSCorpHangars', self.slimItem.itemID)

    def GetMenu(self):
        m = TreeDataInvFolder.GetMenu(self)
        m += sm.GetService('menu').GetMenuFormItemIDTypeID(self.slimItem.itemID, self.slimItem.typeID)
        return m

    def GetChildren(self):
        data = []
        itemID = self.slimItem.itemID
        for divID in xrange(7):
            data.append(uiutil.TreeDataInv(parent=self, clsName='POSCorpHangar', itemID=itemID, divisionID=divID))

        return data

    def IsDraggable(self):
        return self.invController.IsInRange()


class TreeDataShip(TreeDataInv):
    __guid__ = 'uiutil.TreeDataShip'

    def __init__(self, clsName, typeID, **kw):
        uiutil.TreeDataInv.__init__(self, clsName, **kw)
        self.typeID = typeID

    @telemetry.ZONE_METHOD
    def GetLabel(self):
        shipName = TreeDataInv.GetLabel(self)
        return localization.GetByLabel('UI/Inventory/ShipNameAndType', shipName=shipName, typeName=cfg.invtypes.Get(self.typeID).name)

    def GetHint(self):
        hint = TreeDataInv.GetHint(self)
        typeName = cfg.invtypes.Get(self.typeID).name
        if hint:
            return typeName + hint
        else:
            return typeName

    def HasChildren(self):
        return True

    def IsForceCollapsed(self):
        if self.invController.itemID == util.GetActiveShip():
            return False
        return TreeDataInv.IsForceCollapsed(self)

    def GetIcon(self):
        return self.invController.GetIconName(highliteIfActive=True)

    def GetChildren(self):
        shipData = []
        itemID = self.invController.itemID
        typeID = self.typeID
        if itemID == util.GetActiveShip():
            cmdName = 'OpenDroneBayOfActiveShip'
        else:
            cmdName = None
        godmaType = sm.GetService('godma').GetType(typeID)
        if godmaType.droneCapacity or godmaType.techLevel == 3:
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipDroneBay', itemID=itemID, cmdName=cmdName))
        godmaSM = sm.GetService('godma').GetStateManager()
        if bool(godmaSM.GetType(typeID).hasShipMaintenanceBay):
            shipData.append(uiutil.TreeDataShipMaintenanceBay(parent=self, clsName='ShipMaintenanceBay', itemID=itemID))
        if bool(godmaSM.GetType(typeID).hasFleetHangars):
            shipData.append(uiutil.TreeDataFleetHangar(parent=self, clsName='ShipFleetHangar', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialFuelBayCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipFuelBay', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialOreHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipOreHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialGasHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipGasHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialMineralHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipMineralHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialSalvageHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipSalvageHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialShipHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipShipHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialSmallShipHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipSmallShipHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialMediumShipHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipMediumShipHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialLargeShipHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipLargeShipHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialIndustrialShipHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipIndustrialShipHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialAmmoHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipAmmoHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialCommandCenterHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipCommandCenterHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialPlanetaryCommoditiesHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipPlanetaryCommoditiesHold', itemID=itemID))
        if bool(godmaSM.GetType(typeID).specialQuafeHoldCapacity):
            shipData.append(uiutil.TreeDataInv(parent=self, clsName='ShipQuafeHold', itemID=itemID))
        invController = invCtrl.ShipCargo(itemID=itemID)
        shipData += GetContainerDataFromItems(invController.GetItems(), parent=self)
        if not shipData:
            shipData.append(uiutil.TreeData(parent=self, label=localization.GetByLabel('UI/Inventory/NoAdditionalBays'), id='none_%s' % itemID))
        return shipData


class TreeDataStationCorp(TreeDataInvFolder):
    __guid__ = 'uiutil.TreeDataStationCorp'

    def __init__(self, forceCollapsed = True, forceCollapsedMembers = True, *args):
        self.itemID = sm.GetService('corp').GetOffice().itemID
        self.forceCollapsedMembers = forceCollapsedMembers
        self.forceCollapsed = forceCollapsed
        TreeDataInvFolder.__init__(self, *args)

    def GetChildren(self):
        if self._children:
            return self._children
        corpData = []
        for divID in xrange(7):
            invController = invCtrl.StationCorpHangar(self.itemID, divID)
            divData = []
            for item in invController.GetItems():
                if item.groupID in CONTAINERGROUPS and item.singleton:
                    divData.append(uiutil.TreeDataInv(clsName='StationContainer', itemID=item.itemID, typeID=item.typeID))

            cfg.evelocations.Prime([ d.invController.itemID for d in divData ])
            SortData(divData)
            corpData.append(uiutil.TreeDataInv(parent=self, clsName='StationCorpHangar', itemID=self.itemID, divisionID=divID, children=divData))

        securityOfficerRoles = session.corprole & const.corpRoleSecurityOfficer == const.corpRoleSecurityOfficer
        if securityOfficerRoles:
            memberData = sm.GetService('corpui').GetMemberHangarsData().keys()
            cfg.eveowners.Prime([ member[1] for member in memberData ])
            corpData.append(uiutil.TreeDataCorpMembers(parent=self, memberData=memberData, groupChildren=True, forceCollapsed=self.forceCollapsedMembers))
        self._children = corpData
        return corpData

    def HasChildren(self):
        return True

    def IsForceCollapsed(self):
        if self._children or not self.forceCollapsed:
            return False
        invController = invCtrl.StationCorpHangar(self.itemID, 0)
        return not invController.IsPrimed()

    def GetIcon(self):
        return 'ui_1337_64_12'

    @telemetry.ZONE_METHOD
    def GetLabel(self):
        return localization.GetByLabel('UI/Inventory/CorporationHangars')

    def GetID(self):
        return ('StationCorpHangars', self.itemID)


class TreeDataCorpMembers(TreeDataInvFolder):
    __guid__ = 'uiutil.TreeDataCorpMembers'

    def __init__(self, memberData, groupChildren = False, label = None, forceCollapsed = True, *args, **kw):
        if label is None:
            label = localization.GetByLabel('UI/Inventory/MemberHangars')
        self.memberData = memberData
        self.groupChildren = groupChildren
        self.memberData.sort(key=lambda x: cfg.eveowners.Get(x[0]).name.lower())
        self.forceCollapsed = forceCollapsed
        TreeData.__init__(self, label=label, *args, **kw)

    def GetID(self):
        return ('StationCorpMembers', self.GetLabel())

    def GetChildren(self):
        if self._children:
            return self._children
        data = []
        maxNumPerLevel = 50
        numMembers = len(self.memberData)
        if not self.groupChildren or numMembers <= maxNumPerLevel:
            for itemID, ownerID in self.memberData:
                if itemID == session.charid:
                    continue
                if util.IsDustCharacter(itemID):
                    continue
                if itemID == ownerID:
                    data.append(uiutil.TreeDataInv(parent=self, clsName='StationCorpMember', itemID=itemID, ownerID=ownerID))
                else:
                    data.append(uiutil.TreeDataInv(parent=self, clsName='StationOwnerView', itemID=itemID, ownerID=ownerID))

        else:
            currLetter = None
            levelData = []
            for itemID, ownerID in self.memberData:
                letter = cfg.eveowners.Get(ownerID).name[0].upper()
                if letter != currLetter:
                    if levelData:
                        data.append(uiutil.TreeDataCorpMembers(label=currLetter, memberData=levelData))
                    currLetter = letter
                    levelData = []
                levelData.append((itemID, ownerID))

            if levelData:
                data.append(uiutil.TreeDataCorpMembers(label=currLetter, memberData=levelData))
        if not data:
            data.append(uiutil.TreeData(label=localization.GetByLabel('UI/Inventory/NoCorpHangars')))
        self.forceCollapsed = False
        self._children = data
        return data

    def IsForceCollapsed(self):
        return self.forceCollapsed

    def GetIcon(self):
        return 'ui_7_64_11'