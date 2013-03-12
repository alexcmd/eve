#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/invControllers.py
import const
import uix
import uthread
import util
import sys
import uiconst
import log
import localization
import inventoryFlagsCommon
import uiutil
import telemetry
LOOT_GROUPS = (const.groupWreck,
 const.groupCargoContainer,
 const.groupSecureCargoContainer,
 const.groupAuditLogSecureContainer,
 const.groupFreightContainer,
 const.groupSpawnContainer,
 const.groupDeadspaceOverseersBelongings,
 const.groupMissionContainer)
ZERO_CAPACITY = util.Row(['capacity', 'used'], [0, 0.0])

class BaseInvContainer():
    __guid__ = 'invCtrl.BaseInvContainer'
    name = ''
    iconName = 'ui_3_64_13'
    locationFlag = None
    hasCapacity = False
    oneWay = False
    viewOnly = False
    scope = None
    isLockable = True
    filtersEnabled = True
    typeID = None

    def __init__(self, itemID = None, typeID = None):
        self.itemID = itemID
        self.typeID = typeID
        self.invID = (self.__class__.__name__, itemID)

    def GetInvID(self):
        return self.invID

    def GetName(self):
        return self.name

    def GetNameWithLocation(self):
        return localization.GetByLabel('UI/Inventory/BayAndLocationName', bayName=self.GetName(), locationName=cfg.evelocations.Get(self.itemID).name)

    def GetIconName(self):
        return self.iconName

    @telemetry.ZONE_METHOD
    def GetItems(self):
        try:
            return filter(self.IsItemHere, self._GetItems())
        except RuntimeError as e:
            if e[0] == 'CharacterNotAtStation':
                return []
            raise 

    @telemetry.ZONE_METHOD
    def _GetItems(self):
        if self.locationFlag:
            return self._GetInvCacheContainer().List(flag=self.locationFlag)
        else:
            return self._GetInvCacheContainer().List()

    def GetItem(self, itemID):
        for item in self.GetItems():
            if item.itemID == itemID:
                return item

    def GetScope(self):
        return self.scope

    def GetMenu(self):
        return sm.GetService('menu').InvItemMenu(self.GetInventoryItem())

    def _GetInvCacheContainer(self):
        return sm.GetService('invCache').GetInventoryFromId(self.itemID)

    def GetInventoryItem(self):
        item = sm.GetService('invCache').GetParentItemFromItemID(self.itemID)
        if not item:
            item = self._GetInvCacheContainer().GetItem()
        return item

    def GetTypeID(self):
        if self.typeID is None:
            self.typeID = self.GetInventoryItem().typeID
        return self.typeID

    def IsItemHere(self, item):
        raise NotImplementedError('IsItemHere must be implemented')

    def IsItemHereVolume(self, item):
        return self.IsItemHere(item)

    def IsInRange(self):
        return True

    def CheckCanQuery(self):
        return True

    def CheckCanTake(self):
        return True

    def IsPrimed(self):
        return sm.GetService('invCache').IsInventoryPrimedAndListed(self.itemID)

    def HasEnoughSpaceForItems(self, items):
        volume = 0.0
        for item in items:
            volume += cfg.GetItemVolume(item)

        cap = self.GetCapacity()
        remainingVolume = cap.capacity - cap.used
        return volume <= remainingVolume

    def DoesAcceptItem(self, item):
        if self.locationFlag and inventoryFlagsCommon.ShouldAllowAdd(self.locationFlag, item.categoryID, item.groupID, item.typeID) is not None:
            return False
        return True

    def IsBookmarkDroppingAllowed(self):
        raise UserError('CanOnlyCreateVoucherInPersonalHangar')
        return False

    def OnItemsViewed(self):
        pass

    def AddBookmarks(self, bookmarkIDs):
        flag = None
        if not self.CheckAndConfirmOneWayMove():
            return
        if self.locationFlag:
            flag = self.locationFlag
        else:
            flag = const.flagNone
        if flag == const.flagDroneBay:
            raise UserError('ItemCannotBeInDroneBay')
        isMove = not uicore.uilib.Key(uiconst.VK_SHIFT)
        self._GetInvCacheContainer().AddBookmarks(bookmarkIDs, flag, isMove)

    def __AddItem(self, itemID, sourceLocation, quantity, dividing = False):
        dropLocation = self._GetInvCacheContainer().GetItem().itemID
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        stateMgr = sm.StartService('godma').GetStateManager()
        item = dogmaLocation.dogmaItems.get(itemID)
        if dropLocation == sourceLocation and not dividing:
            if getattr(item, 'flagID', None):
                if item.flagID == self.locationFlag:
                    return
        if not dividing and not self.CheckAndConfirmOneWayMove():
            return
        if self.locationFlag:
            item = stateMgr.GetItem(itemID)
            if item and self.locationFlag == const.flagCargo and cfg.IsShipFittingFlag(item.flagID):
                containerArgs = self._GetContainerArgs()
                if item.categoryID == const.categoryCharge:
                    return dogmaLocation.UnloadChargeToContainer(item.locationID, item.itemID, containerArgs, self.locationFlag, quantity)
                if item.categoryID == const.categoryModule:
                    return stateMgr.UnloadModuleToContainer(item.locationID, item.itemID, containerArgs, self.locationFlag)
            else:
                return self._GetInvCacheContainer().Add(itemID, sourceLocation, qty=quantity, flag=self.locationFlag)
        else:
            lockFlag = None
            typeID = self.GetTypeID()
            if typeID and cfg.invtypes.Get(typeID).groupID == const.groupAuditLogSecureContainer:
                thisContainer = sm.GetService('invCache').GetInventoryFromId(self.itemID)
                thisContainerItem = thisContainer.GetItem()
                rolesAreNeeded = thisContainerItem is None or not util.IsStation(thisContainerItem.locationID) and thisContainerItem.locationID != session.shipid
                if rolesAreNeeded:
                    config = thisContainer.ALSCConfigGet()
                    lockFlag = const.flagLocked if bool(config & const.ALSCLockAddedItems) else const.flagUnlocked
                    if lockFlag == const.flagLocked and charsession.corprole & const.corpRoleEquipmentConfig == 0:
                        if eve.Message('ConfirmAddLockedItemToAuditContainer', {}, uiconst.OKCANCEL) != uiconst.ID_OK:
                            return
            return self._GetInvCacheContainer().Add(itemID, sourceLocation, qty=quantity, flag=self.locationFlag)

    def _AddItem(self, item, forceQuantity = False, sourceLocation = None):
        locationID = session.locationid
        for i in xrange(2):
            try:
                if locationID != session.locationid:
                    return
                itemQuantity = item.stacksize
                if itemQuantity == 1:
                    quantity = 1
                elif uicore.uilib.Key(uiconst.VK_SHIFT) or forceQuantity:
                    quantity = self.PromptUserForQuantity(item, itemQuantity, sourceLocation)
                else:
                    quantity = itemQuantity
                if not item.itemID or not quantity:
                    return
                if locationID != session.locationid:
                    return
                if sourceLocation is None:
                    sourceLocation = item.locationID
                return self.__AddItem(item.itemID, sourceLocation, quantity)
            except UserError as what:
                if what.args[0] in ('NotEnoughCargoSpace', 'NotEnoughCargoSpaceOverload', 'NotEnoughDroneBaySpace', 'NotEnoughDroneBaySpaceOverload', 'NoSpaceForThat', 'NoSpaceForThatOverload', 'NotEnoughChargeSpace', 'NotEnoughSpecialBaySpace', 'NotEnoughSpecialBaySpaceOverload', 'NotEnoughSpace'):
                    try:
                        cap = self.GetCapacity()
                    except UserError:
                        raise what

                    free = cap.capacity - cap.used
                    if free < 0:
                        raise 
                    if item.typeID == const.typePlasticWrap:
                        volume = sm.GetService('invCache').GetInventoryFromId(item.itemID).GetCapacity().used
                    else:
                        volume = cfg.GetItemVolume(item, 1)
                    maxQty = min(item.stacksize, int(free / (volume or 1)))
                    if maxQty <= 0:
                        if volume < 0.1:
                            req = 0.01
                        else:
                            req = volume
                        eve.Message('NotEnoughCargoSpaceFor1Unit', {'type': item.typeID,
                         'free': free,
                         'required': req})
                        return
                    if self._DBLessLimitationsCheck(what.args[0], item):
                        return
                    forceQuantity = 1
                else:
                    raise 
                sys.exc_clear()

    def PromptUserForQuantity(self, item, itemQuantity, sourceLocation = None):
        if self.locationFlag is not None and item.flagID != self.locationFlag or item.locationID != getattr(self._GetInvCacheContainer(), 'itemID', None):
            if self.hasCapacity:
                cap = self.GetCapacity()
                capacity = cap.capacity - cap.used
                itemvolume = cfg.GetItemVolume(item, 1) or 1
                maxQty = capacity / itemvolume + 1e-07
                maxQty = min(itemQuantity, int(maxQty))
            else:
                maxQty = itemQuantity
            if maxQty == itemQuantity:
                errmsg = localization.GetByLabel('UI/Common/NoMoreUnits')
            else:
                errmsg = localization.GetByLabel('UI/Common/NoRoomForMore')
            ret = uix.QtyPopup(int(maxQty), 0, int(maxQty), errmsg)
        else:
            ret = uix.QtyPopup(itemQuantity, 1, 1, None, localization.GetByLabel('UI/Inventory/ItemActions/DivideItemStack'))
        if item.locationID != session.stationid2:
            if not sm.GetService('invCache').IsInventoryPrimedAndListed(item.locationID):
                log.LogError('Item disappeared before we could add it', item)
                return
        if ret is not None:
            return ret['qty']

    def MultiMerge(self, data, mergeSourceID):
        if not self.CheckAndConfirmOneWayMove():
            return
        ret = None
        try:
            dataReduced = []
            for d in data:
                dataReduced.append((d[0], d[1], d[2]))

            self._GetInvCacheContainer().MultiMerge(dataReduced, mergeSourceID)
            return True
        except UserError as what:
            if len(data) == 1 and what.args[0] in ('NotEnoughCargoSpace', 'NotEnoughCargoSpaceOverload', 'NotEnoughDroneBaySpace', 'NotEnoughDroneBaySpaceOverload', 'NoSpaceForThat', 'NoSpaceForThatOverload', 'NotEnoughChargeSpace'):
                cap = self.GetCapacity()
                free = cap.capacity - cap.used
                if free < 0:
                    raise 
                item = data[0][3]
                if item.typeID == const.typePlasticWrap:
                    volume = sm.GetService('invCache').GetInventoryFromId(item.itemID).GetCapacity().used
                else:
                    volume = cfg.GetItemVolume(item, 1)
                maxQty = min(item.stacksize, int(free / (volume or 1)))
                if maxQty <= 0:
                    if volume < 0.01:
                        req = 0.01
                    else:
                        req = volume
                    eve.Message('NotEnoughCargoSpaceFor1Unit', {'type': item.typeID,
                     'free': free,
                     'required': req})
                    return
                if self._DBLessLimitationsCheck(what.args[0], item):
                    return
                if maxQty == item.stacksize:
                    errmsg = localization.GetByLabel('UI/Common/NoMoreUnits')
                else:
                    errmsg = localization.GetByLabel('UI/Common/NoRoomForMore')
                ret = uix.QtyPopup(int(maxQty), 0, int(maxQty), errmsg)
                if ret is None:
                    quantity = None
                else:
                    quantity = ret['qty']
                if quantity:
                    self._GetInvCacheContainer().MultiMerge([(data[0][0], data[0][1], quantity)], mergeSourceID)
                    return True
            else:
                raise 
            sys.exc_clear()

    def StackAll(self, securityCode = None):
        if not self.CheckAndConfirmOneWayMove():
            return
        if self.locationFlag:
            retval = self._GetInvCacheContainer().StackAll(self.locationFlag)
            return retval
        try:
            if securityCode is None:
                retval = self._GetInvCacheContainer().StackAll()
            else:
                retval = self._GetInvCacheContainer().StackAll(securityCode=securityCode)
            return retval
        except UserError as what:
            if what.args[0] == 'PermissionDenied':
                if securityCode:
                    caption = localization.GetByLabel('UI/Menusvc/IncorrectPassword')
                    label = localization.GetByLabel('UI/Menusvc/PleaseTryEnteringPasswordAgain')
                else:
                    caption = localization.GetByLabel('UI/Menusvc/PasswordRequired')
                    label = localization.GetByLabel('UI/Menusvc/PleaseEnterPassword')
                passw = uiutil.NamePopup(caption=caption, label=label, setvalue='', icon=-1, modal=1, btns=None, maxLength=50, passwordChar='*')
                if passw == '':
                    raise UserError('IgnoreToTop')
                else:
                    retval = self.StackAll(securityCode=passw['name'])
                    return retval
            else:
                raise 
            sys.exc_clear()

    def _DBLessLimitationsCheck(self, errorName, item):
        return False

    def GetCapacity(self):
        try:
            return self._GetInvCacheContainer().GetCapacity(self.locationFlag)
        except RuntimeError as e:
            if e[0] == 'CharacterNotAtStation':
                return ZERO_CAPACITY
            raise 

    def GetOwnerID(self):
        return self.GetInventoryItem().ownerID

    def _GetContainerArgs(self):
        return (self.itemID,)

    def OnDropData(self, nodes):
        bookmarkIDs = []
        items = []
        lockedNodes = [ node for node in nodes if getattr(node, 'locked', False) ]
        if lockedNodes:
            for node in lockedNodes:
                nodes.remove(node)

            uicore.Message('SomeLockedItemsNotMoved')
        for i, node in enumerate(nodes):
            if getattr(node, '__guid__', None) == 'listentry.PlaceEntry' and self.IsBookmarkDroppingAllowed():
                bookmarkIDs.append(node.bm.bookmarkID)
                continue
            if getattr(node, '__guid__', None) in ('xtriui.ShipUIModule', 'xtriui.InvItem', 'listentry.InvItem', 'xtriui.FittingSlot'):
                items.append(node.item)
            if isinstance(node, uiutil.TreeDataInv):
                items.append(node.invController.GetInventoryItem())

        if bookmarkIDs:
            if len(bookmarkIDs) > 5:
                eve.Message('CannotMoveBookmarks')
                return
            uthread.new(self.AddBookmarks, bookmarkIDs)
        return self.AddItems(items)

    def AddItems(self, items):
        if len(items) > 1:
            items = filter(self.DoesAcceptItem, items)
        if not items:
            return
        sourceLocation = items[0].locationID
        if self.itemID != sourceLocation and not sm.GetService('crimewatchSvc').CheckCanTakeItems(sourceLocation):
            sm.GetService('crimewatchSvc').SafetyActivated(const.shipSafetyLevelPartial)
            return
        if session.shipid and self.itemID == session.shipid:
            if self.itemID != sourceLocation and not sm.GetService('consider').ConfirmTakeIllicitGoods(items):
                return
        if len(items) == 1:
            item = items[0]
            if hasattr(item, 'flagID') and cfg.IsShipFittingFlag(item.flagID):
                if item.locationID == util.GetActiveShip():
                    if not self.CheckAndConfirmOneWayMove():
                        return
                    itemKey = item.itemID
                    locationID = item.locationID
                    dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
                    containerArgs = self._GetContainerArgs()
                    if item.categoryID == const.categoryCharge:
                        return dogmaLocation.UnloadChargeToContainer(locationID, itemKey, containerArgs, self.locationFlag)
                    if item.categoryID == const.categoryModule:
                        return dogmaLocation.UnloadModuleToContainer(locationID, itemKey, containerArgs, self.locationFlag)
            return self._AddItem(item, sourceLocation=sourceLocation)
        elif not self.CheckAndConfirmOneWayMove():
            return
        items.sort(key=lambda item: cfg.invtypes.Get(item.typeID).volume * item.stacksize)
        itemIDs = [ node.itemID for node in items ]
        dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        masters = dogmaLocation.GetAllSlaveModulesByMasterModule(sourceLocation)
        if masters:
            inBank = 0
            for itemID in itemIDs:
                if dogmaLocation.IsInWeaponBank(sourceLocation, itemID):
                    inBank = 1
                    break

            if inBank:
                ret = eve.Message('CustomQuestion', {'header': localization.GetByLabel('UI/Common/Confirm'),
                 'question': localization.GetByLabel('UI/Inventory/WeaponLinkUnfitMany')}, uiconst.YESNO)
                if ret != uiconst.ID_YES:
                    return
        for item in items:
            if item.categoryID == const.categoryCharge and cfg.IsShipFittingFlag(item.flagID):
                log.LogInfo('A module with a db item charge dropped from ship fitting into some container. Cannot use multimove, must remove charge first.')
                ret = [self._AddItem(item)]
                items.remove(item)
                for item in items:
                    ret.append(self._AddItem(item))

                return ret

        invCacheCont = self._GetInvCacheContainer()
        if self.locationFlag:
            return invCacheCont.MultiAdd(itemIDs, sourceLocation, flag=self.locationFlag)
        else:
            return invCacheCont.MultiAdd(itemIDs, sourceLocation, flag=const.flagNone)

    def CheckAndConfirmOneWayMove(self):
        if self.oneWay:
            return self.PromptOneWayMove()
        return True

    def PromptOneWayMove(self):
        return uicore.Message('ConfirmOneWayItemMove', {}, uiconst.OKCANCEL) == uiconst.ID_OK

    def GetSpecialActions(self):
        return []


class ShipCargo(BaseInvContainer):
    __guid__ = 'invCtrl.ShipCargo'
    hasCapacity = True
    locationFlag = const.flagCargo

    def __init__(self, itemID = None, typeID = None):
        self.itemID = itemID or util.GetActiveShip()
        self.invID = (self.__class__.__name__, self.itemID)
        self.name = localization.GetByLabel('UI/Common/CargoHold')

    def GetMenu(self):
        if self.itemID == util.GetActiveShip() and session.solarsystemid:
            return sm.GetService('menu').GetMenuFormItemIDTypeID(self.itemID, self.GetTypeID())
        else:
            return BaseInvContainer.GetMenu(self)

    def GetIconName(self, highliteIfActive = False):
        if highliteIfActive and self.itemID == util.GetActiveShip():
            return 'ui_1337_64_11'
        else:
            return 'ui_9_64_5'

    def GetScope(self):
        if self.itemID == util.GetActiveShip():
            return 'station_inflight'
        return 'station'

    def GetName(self):
        return cfg.evelocations.Get(self.itemID).name

    def _GetInvCacheContainer(self):
        return sm.GetService('invCache').GetInventoryFromId(self.itemID, locationID=session.stationid2)

    def IsItemHere(self, item):
        return item.locationID == self.itemID and item.flagID == self.locationFlag

    def IsBookmarkDroppingAllowed(self):
        return True


class BaseShipBay(BaseInvContainer):
    __guid__ = 'invCtrl.BaseShipBay'
    hasCapacity = True

    def IsItemHere(self, item):
        return item.locationID == self.itemID and item.flagID == self.locationFlag

    def GetName(self):
        return inventoryFlagsCommon.GetNameForFlag(self.locationFlag)

    def GetScope(self):
        if self.itemID == util.GetActiveShip():
            return 'station_inflight'
        else:
            return 'station'


class ShipDroneBay(BaseShipBay):
    __guid__ = 'invCtrl.ShipDroneBay'
    iconName = 'ui_11_64_16'
    locationFlag = const.flagDroneBay
    hasCapacity = True
    scope = 'station'


class ShipFuelBay(BaseShipBay):
    __guid__ = 'invCtrl.ShipFuelBay'
    locationFlag = const.flagSpecializedFuelBay
    iconName = 'ui_98_64_9'


class ShipOreHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipOreHold'
    locationFlag = const.flagSpecializedOreHold
    iconName = 'ui_24_64_1'


class ShipGasHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipGasHold'
    locationFlag = const.flagSpecializedGasHold
    iconName = 'ui_62_64_13'


class ShipMineralHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipMineralHold'
    locationFlag = const.flagSpecializedMineralHold
    iconName = 'ui_6_64_14'


class ShipSalvageHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipSalvageHold'
    locationFlag = const.flagSpecializedSalvageHold
    iconName = 'ui_10_64_3'


class ShipShipHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipShipHold'
    locationFlag = const.flagSpecializedShipHold
    iconName = 'ui_9_64_5'


class ShipSmallShipHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipSmallShipHold'
    locationFlag = const.flagSpecializedSmallShipHold
    iconName = 'ui_1337_64_7'


class ShipMediumShipHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipMediumShipHold'
    locationFlag = const.flagSpecializedMediumShipHold
    iconName = 'ui_1337_64_8'


class ShipLargeShipHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipLargeShipHold'
    locationFlag = const.flagSpecializedLargeShipHold
    iconName = 'ui_1337_64_9'


class ShipIndustrialShipHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipIndustrialShipHold'
    locationFlag = const.flagSpecializedIndustrialShipHold
    iconName = 'ui_1337_64_10'


class ShipAmmoHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipAmmoHold'
    locationFlag = const.flagSpecializedAmmoHold
    iconName = 'ui_43_64_13'


class ShipCommandCenterHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipCommandCenterHold'
    locationFlag = const.flagSpecializedCommandCenterHold
    iconName = 'ui_97_64_13'


class ShipPlanetaryCommoditiesHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipPlanetaryCommoditiesHold'
    locationFlag = const.flagSpecializedPlanetaryCommoditiesHold
    iconName = 'ui_96_64_10'


class ShipQuafeHold(BaseShipBay):
    __guid__ = 'invCtrl.ShipQuafeHold'
    locationFlag = const.flagQuafeBay


class BaseCorpContainer(BaseInvContainer):
    __guid__ = 'invCtrl.BaseCorpContainer'
    scope = 'station'
    oneWay = True
    iconName = 'ui_7_64_10'

    def __init__(self, itemID = None, divisionID = 0):
        self.itemID = itemID
        self.SetDivisionID(divisionID)
        if self.roles is not None:
            self.SetAccess()
        self.invID = (self.__class__.__name__, self.itemID, divisionID)

    def GetName(self):
        if self.divisionID is not None:
            divisions = sm.GetService('corp').GetDivisionNames()
            return divisions[self.divisionID + 1]
        else:
            return localization.GetByLabel('UI/Inventory/CorporationHangars')

    def SetDivisionID(self, divisionID):
        self.divisionID = divisionID
        self.locationFlag = {0: const.flagHangar,
         1: const.flagCorpSAG2,
         2: const.flagCorpSAG3,
         3: const.flagCorpSAG4,
         4: const.flagCorpSAG5,
         5: const.flagCorpSAG6,
         6: const.flagCorpSAG7}.get(divisionID, None)
        self.roles = {0: (const.corpRoleHangarCanQuery1, const.corpRoleHangarCanTake1),
         1: (const.corpRoleHangarCanQuery2, const.corpRoleHangarCanTake2),
         2: (const.corpRoleHangarCanQuery3, const.corpRoleHangarCanTake3),
         3: (const.corpRoleHangarCanQuery4, const.corpRoleHangarCanTake4),
         4: (const.corpRoleHangarCanQuery5, const.corpRoleHangarCanTake5),
         5: (const.corpRoleHangarCanQuery6, const.corpRoleHangarCanTake6),
         6: (const.corpRoleHangarCanQuery7, const.corpRoleHangarCanTake7)}.get(divisionID, None)

    def _GetInvCacheContainer(self):
        return sm.GetService('invCache').GetInventoryFromId(self.itemID)

    def IsBookmarkDroppingAllowed(self):
        return True

    def IsItemHere(self, item):
        return item.locationID == self.itemID and (item.ownerID == session.corpid or session.solarsystemid and item.ownerID == sm.GetService('michelle').GetBallpark().slimItems[self.itemID].ownerID) and (self.locationFlag is None or item.flagID == self.locationFlag) and self.CheckCanQuery()

    def CheckCanQuery(self):
        if self.roles is None:
            return True
        role = self.roles[0]
        if session.corprole & role == role:
            return True
        return False

    def CheckCanTake(self):
        if self.roles is None:
            return True
        role = self.roles[1]
        if session.corprole & role == role:
            return True
        return False

    def SetAccess(self):
        role = self.roles[1]
        if session.corprole & role == role:
            self.viewOnly = False
        else:
            self.viewOnly = True

    @telemetry.ZONE_METHOD
    def GetItems(self):
        if self.CheckCanQuery():
            return BaseInvContainer.GetItems(self)
        else:
            return []


class StationCorpHangar(BaseCorpContainer):
    __guid__ = 'invCtrl.StationCorpHangar'
    hasCapacity = False

    def __init__(self, itemID = None, divisionID = 0):
        if itemID is None:
            itemID = sm.GetService('corp').GetOffice().itemID
        BaseCorpContainer.__init__(self, itemID, divisionID)

    def GetItems(self):
        office = sm.GetService('corp').GetOffice()
        if office is None or office and office.itemID != self.itemID:
            return []
        else:
            return BaseCorpContainer.GetItems(self)

    def GetCapacity(self):
        if sm.GetService('corp').GetOffice() is None:
            return ZERO_CAPACITY
        else:
            return BaseCorpContainer.GetCapacity(self)

    def GetMenu(self):
        return []


class POSCorpHangar(BaseCorpContainer):
    __guid__ = 'invCtrl.POSCorpHangar'
    scope = 'inflight'
    hasCapacity = True

    def GetCapacity(self):
        return self._GetInvCacheContainer().GetCapacity()

    def OnItemsViewed(self):
        settings.user.ui.Set('InvPOSCorpHangar_%s' % self.itemID, self.divisionID)

    def IsBookmarkDroppingAllowed(self):
        return True

    def IsInRange(self):
        bp = sm.GetService('michelle').GetBallpark()
        if bp is None:
            return True
        ball = bp.GetBall(self.itemID)
        if not ball:
            return False
        item = sm.GetService('michelle').GetItem(self.itemID)
        if item is None:
            return False
        operationalDistance = sm.GetService('godma').GetTypeAttribute(item.typeID, const.attributeMaxOperationalDistance)
        if operationalDistance is None:
            operationalDistance = const.maxCargoContainerTransferDistance
        if ball.surfaceDist > operationalDistance:
            return False
        return True

    def IsItemHereVolume(self, item):
        return item.locationID == self.itemID and (item.ownerID == session.corpid or session.solarsystemid and item.ownerID == sm.GetService('michelle').GetBallpark().slimItems[self.itemID].ownerID) and self.CheckCanQuery()


class StationCorpMember(BaseInvContainer):
    __guid__ = 'invCtrl.StationCorpMember'
    scope = 'station'
    oneWay = True
    viewOnly = True
    locationFlag = const.flagHangar
    iconName = 'ui_8_64_12'

    def __init__(self, itemID = None, ownerID = None):
        self.itemID = itemID
        self.ownerID = ownerID
        self.invID = (self.__class__.__name__, itemID, ownerID)

    def GetName(self):
        return localization.GetByLabel('UI/Station/Hangar/HangarNameWithOwner', charID=self.ownerID)

    def _GetInvCacheContainer(self):
        return sm.GetService('invCache').GetInventory(const.containerHangar, self.itemID)

    def _GetContainerArgs(self):
        return (const.containerHangar, self.itemID)

    def IsItemHere(self, item):
        return item.flagID == const.flagHangar and item.locationID == session.stationid and item.ownerID == self.ownerID


class StationCorpDeliveries(BaseInvContainer):
    __guid__ = 'invCtrl.StationCorpDeliveries'
    scope = 'station'
    oneWay = True
    locationFlag = const.flagCorpMarket
    iconName = 'ui_1337_64_6'

    def __init__(self, *args, **kwargs):
        BaseInvContainer.__init__(self, *args, **kwargs)
        self.name = localization.GetByLabel('UI/Neocom/DeliveriesHangarBtn')

    def _GetInvCacheContainer(self):
        return sm.GetService('invCache').GetInventory(const.containerCorpMarket, session.corpid)

    def _GetContainerArgs(self):
        return (const.containerCorpMarket, session.corpid)

    def IsItemHere(self, item):
        return item.flagID == const.flagCorpMarket and item.locationID == session.stationid and item.ownerID == session.corpid


class StationItems(BaseInvContainer):
    __guid__ = 'invCtrl.StationItems'
    locationFlag = const.flagHangar
    scope = 'station'
    iconName = 'ui_43_64_13'

    def __init__(self, *args, **kwargs):
        BaseInvContainer.__init__(self, *args, **kwargs)
        self.name = localization.GetByLabel('UI/Inventory/ItemHangar')

    @telemetry.ZONE_METHOD
    def IsItemHere(self, item):
        return item.locationID == session.stationid2 and item.ownerID == session.charid and item.flagID == const.flagHangar and item.categoryID != const.categoryShip

    def _GetInvCacheContainer(self):
        return sm.GetService('invCache').GetInventory(const.containerHangar)

    def _GetContainerArgs(self):
        return (const.containerHangar,)

    def IsBookmarkDroppingAllowed(self):
        return True

    def IsPrimed(self):
        return True


class StationShips(BaseInvContainer):
    __guid__ = 'invCtrl.StationShips'
    iconName = 'ui_1337_64_13'
    scope = 'station'
    locationFlag = const.flagHangar

    def __init__(self, *args, **kwargs):
        BaseInvContainer.__init__(self, *args, **kwargs)
        self.name = localization.GetByLabel('UI/Inventory/ShipHangar')

    @telemetry.ZONE_METHOD
    def IsItemHere(self, item):
        return item.locationID == session.stationid2 and item.ownerID == session.charid and item.flagID == const.flagHangar and item.categoryID == const.categoryShip

    def GetActiveShip(self):
        activeShipID = util.GetActiveShip()
        for item in self._GetItems():
            if item.itemID == activeShipID:
                return item

    def _GetInvCacheContainer(self):
        return sm.GetService('invCache').GetInventory(const.containerHangar)

    def _GetContainerArgs(self):
        return (const.containerHangar,)

    def IsPrimed(self):
        return True


class StationOwnerView(BaseInvContainer):
    __guid__ = 'invCtrl.StationOwnerView'
    scope = 'station'
    oneWay = True
    viewOnly = True

    def __init__(self, itemID = None, ownerID = None):
        self.itemID = itemID
        self.ownerID = ownerID
        self.invID = (self.__class__.__name__, itemID, ownerID)

    def GetName(self):
        return localization.GetByLabel('UI/Station/Hangar/HangarNameWithOwner', charID=self.ownerID)

    def IsItemHere(self, item):
        return item.locationID == self.id and item.ownerID == self.ownerID


class CustomsOffice(BaseInvContainer):
    __guid__ = 'invCtrl.CustomsOffice'


class BaseCelestialContainer(BaseInvContainer):
    __guid__ = 'invCtrl.BaseCelestialContainer'
    hasCapacity = True

    def __init__(self, *args, **kwargs):
        BaseInvContainer.__init__(self, *args, **kwargs)
        self._isLootable = None

    def IsBookmarkDroppingAllowed(self):
        if self.locationFlag == const.flagShipHangar:
            return False
        else:
            return True

    def IsItemHere(self, item):
        if self.locationFlag is not None:
            return item.locationID == self.itemID and item.flagID == self.locationFlag
        else:
            return item.locationID == self.itemID

    def IsInRange(self):
        bp = sm.GetService('michelle').GetBallpark()
        if bp is None:
            return True
        ball = bp.GetBall(self.itemID)
        if not ball:
            return False
        item = sm.GetService('michelle').GetItem(self.itemID)
        if item is None:
            return False
        if ball.surfaceDist > self.GetOperationalDistance(item.typeID):
            return False
        return True

    def GetOperationalDistance(self, typeID):
        distance = sm.GetService('godma').GetTypeAttribute(typeID, const.attributeMaxOperationalDistance)
        if distance is None:
            distance = const.maxCargoContainerTransferDistance
        return distance

    def GetIconName(self):
        try:
            typeID = self.GetTypeID()
        except UserError:
            return self.iconName

        if typeID:
            icon = cfg.invtypes.Get(typeID).Icon()
            if icon and icon.iconFile:
                return icon.iconFile
        return self.iconName

    def GetTypeID(self):
        if self.typeID is not None:
            return self.typeID
        bp = sm.GetService('michelle').GetBallpark()
        if bp and self.itemID in bp.slimItems:
            slimItem = bp.slimItems[self.itemID]
            self.typeID = slimItem.typeID
        else:
            self.typeID = BaseInvContainer.GetTypeID(self)
        return self.typeID

    def GetName(self):
        if self.name:
            return self.name
        bp = sm.GetService('michelle').GetBallpark()
        if bp:
            slimItem = bp.slimItems.get(self.itemID, None)
            if slimItem:
                return uix.GetSlimItemName(slimItem)
        return ''

    def _DBLessLimitationsCheck(self, errorName, item):
        if errorName in ('NotEnoughCargoSpace', 'NotEnoughCargoSpaceOverload'):
            eve.Message('ItemMoveGoesThroughFullCargoHold', {'itemType': item.typeID})
            return True
        return False

    def GetMenu(self):
        return sm.GetService('menu').GetMenuFormItemIDTypeID(self.itemID, self.GetTypeID())

    def GetSpecialActions(self):
        if self.IsLootable():
            return [(localization.GetByLabel('UI/Inventory/LootAll'), self.LootAll, 'invLootAllBtn')]
        return []

    def LootAll(self, *args):
        items = self.GetItems()
        shipCargo = ShipCargo()
        if len(items) > 0:
            if sm.GetService('crimewatchSvc').CheckCanTakeItems(self.itemID):
                if sm.GetService('consider').ConfirmTakeIllicitGoods(items):
                    shipCargo.AddItems(items)
                    sm.GetService('audio').SendUIEvent('ui_notify_mission_rewards_play')
            else:
                sm.GetService('crimewatchSvc').SafetyActivated(const.shipSafetyLevelPartial)
        if shipCargo.HasEnoughSpaceForItems(items):
            sm.ScatterEvent('OnWreckLootAll', self.GetInvID(), items)

    def IsLootable(self):
        if self._isLootable is None:
            bp = sm.GetService('michelle').GetBallpark()
            item = bp.GetInvItem(self.itemID) if bp else None
            if item and item.groupID in LOOT_GROUPS:
                self._isLootable = True
            else:
                self._isLootable = False
        return self._isLootable


class POSRefinery(BaseCelestialContainer):
    __guid__ = 'invCtrl.POSRefinery'
    locationFlag = const.flagCargo
    iconName = 'ui_24_64_1'


class POSStructureCharges(BaseCelestialContainer):
    __guid__ = 'invCtrl.POSStructureCharges'
    locationFlag = const.flagHiSlot0

    def GetIconName(self):
        typeObj = cfg.invtypes.Get(self.GetTypeID())
        if typeObj.groupID == const.groupMobileHybridSentry:
            return 'ui_13_64_5'
        elif typeObj.groupID == const.groupMobileMissileSentry:
            return 'ui_12_64_16'
        elif typeObj.groupID == const.groupMobileProjectileSentry:
            return 'ui_12_64_9'
        else:
            return BaseCelestialContainer.GetIconName(self)


class POSStructureChargeCrystal(POSStructureCharges):
    __guid__ = 'invCtrl.POSStructureChargeCrystal'

    def GetName(self):
        return localization.GetByLabel('UI/Inflight/POS/AccessPOSActiveCrystalError')

    def GetIconName(self):
        return 'ui_8_64_2'


class POSStructureChargesStorage(BaseCelestialContainer):
    __guid__ = 'invCtrl.POSStructureChargesStorage'
    locationFlag = const.flagNone


class POSStrontiumBay(BaseCelestialContainer):
    __guid__ = 'invCtrl.POSStrontiumBay'
    locationFlag = const.flagSecondaryStorage
    iconName = 'ui_51_64_10'

    def __init__(self, *args, **kwargs):
        BaseCelestialContainer.__init__(self, *args, **kwargs)
        self.name = localization.GetByLabel('UI/Inventory/StrontiumBay')


class POSFuelBay(BaseCelestialContainer):
    __guid__ = 'invCtrl.POSFuelBay'
    locationFlag = const.flagNone
    iconName = 'ui_98_64_9'

    def __init__(self, *args, **kwargs):
        BaseCelestialContainer.__init__(self, *args, **kwargs)
        self.name = localization.GetByLabel('UI/Ship/FuelBay')


class POSJumpBridge(BaseCelestialContainer):
    __guid__ = 'invCtrl.POSJumpBridge'
    locationFlag = const.flagNone
    iconName = 'ui_56_64_3'


class POSShipMaintenanceArray(BaseCelestialContainer):
    __guid__ = 'invCtrl.POSShipMaintenanceArray'
    locationFlag = const.flagNone
    iconName = 'ui_9_64_16'


class POSMobileReactor(BaseCelestialContainer):
    __guid__ = 'invCtrl.POSMobileReactor'
    locationFlag = const.flagNone
    iconName = 'ui_27_64_11'

    def PromptUserForQuantity(self, item, itemQuantity, sourceLocation):
        if sourceLocation == self.itemID:
            return None
        return BaseCelestialContainer.PromptUserForQuantity(self, item, itemQuantity)


class POSSilo(BaseCelestialContainer):
    __guid__ = 'invCtrl.POSSilo'
    locationFlag = const.flagNone
    iconName = 'ui_26_64_12'

    def PromptUserForQuantity(self, item, itemQuantity, sourceLocation):
        if sourceLocation == self.itemID:
            return None
        return BaseCelestialContainer.PromptUserForQuantity(self, item, itemQuantity)


class POSConstructionPlatform(BaseCelestialContainer):
    __guid__ = 'invCtrl.POSConstructionPlatform'
    hasCapacity = False


class ItemFloatingCargo(BaseCelestialContainer):
    __guid__ = 'invCtrl.ItemFloatingCargo'
    iconName = 'ui_38_20_12'

    def GetIconName(self):
        return self.iconName

    def GetItems(self):
        sm.GetService('wreck').MarkViewed(self.itemID, True)
        return BaseCelestialContainer.GetItems(self)


class ShipMaintenanceBay(BaseCelestialContainer):
    __guid__ = 'invCtrl.ShipMaintenanceBay'
    locationFlag = const.flagShipHangar
    iconName = 'ui_9_64_16'

    def GetName(self):
        bayName = inventoryFlagsCommon.GetNameForFlag(self.locationFlag)
        if session.solarsystemid and self.itemID != util.GetActiveShip():
            return localization.GetByLabel('UI/Inventory/BayAndLocationName', bayName=cfg.invtypes.Get(self.GetTypeID()).name, locationName=bayName)
        return bayName

    def GetOperationalDistance(self, *args):
        return const.maxCargoContainerTransferDistance


class ShipFleetHangar(BaseCelestialContainer):
    __guid__ = 'invCtrl.ShipFleetHangar'
    locationFlag = const.flagFleetHangar
    iconName = 'ui_94_64_9'

    def GetName(self):
        bayName = inventoryFlagsCommon.GetNameForFlag(self.locationFlag)
        if session.solarsystemid and self.itemID != util.GetActiveShip():
            return localization.GetByLabel('UI/Inventory/BayAndLocationName', bayName=cfg.invtypes.Get(self.GetTypeID()).name, locationName=bayName)
        return bayName

    def GetOperationalDistance(self, *args):
        return const.maxCargoContainerTransferDistance


class StationContainer(BaseCelestialContainer):
    __guid__ = 'invCtrl.StationContainer'
    hasCapacity = True

    def GetMenu(self):
        return sm.GetService('menu').InvItemMenu(self.GetInventoryItem())

    def GetName(self):
        name = cfg.evelocations.Get(self.itemID).name
        if not name:
            name = cfg.invtypes.Get(self.GetTypeID()).name
        return name

    def IsInRange(self):
        return True

    def CheckAndConfirmOneWayMove(self):
        if self.oneWay:
            return self.PromptOneWayMove()
        if session.solarsystemid:
            invItem = self.GetInventoryItem()
            bp = sm.GetService('michelle').GetBallpark()
            if bp:
                ball = bp.GetBallById(invItem.locationID)
                if ball and cfg.invtypes.Get(ball.typeID).groupID in (const.groupCorporateHangarArray, const.groupAssemblyArray, const.groupMobileLaboratory):
                    return self.PromptOneWayMove()
                if invItem.flagID == const.flagFleetHangar and invItem.ownerID != session.charid:
                    return self.PromptOneWayMove()
        return True


class ItemWreck(BaseCelestialContainer):
    __guid__ = 'invCtrl.ItemWreck'
    hasCapacity = False

    def GetIconName(self):
        slimItem = sm.GetService('michelle').GetBallpark().slimItems[self.itemID]
        if slimItem.isEmpty:
            return 'ui_38_20_29'
        else:
            return 'ui_38_20_28'

    def IsBookmarkDroppingAllowed(self):
        return False

    @telemetry.ZONE_METHOD
    def GetItems(self):
        sm.GetService('wreck').MarkViewed(self.itemID, True, True)
        return BaseCelestialContainer.GetItems(self)


class PlayerTrade(BaseInvContainer):
    __guid__ = 'invCtrl.PlayerTrade'
    scope = 'station'
    viewOnly = True
    hasCapacity = False
    isLockable = False
    filtersEnabled = False

    def __init__(self, itemID = None, ownerID = None, tradeSession = None):
        self.itemID = itemID
        self.ownerID = ownerID
        self.tradeSession = tradeSession
        self.invID = (self.__class__.__name__, itemID, ownerID)

    def _GetItems(self):
        return [ item for item in self.tradeSession.List().items ]

    def IsItemHere(self, item):
        return item.ownerID == self.ownerID and self.itemID == item.locationID

    def AddItems(self, items):
        activeShipID = util.GetActiveShip()
        for item in items:
            if item.itemID == activeShipID:
                raise UserError('PeopleAboardShip')

        BaseInvContainer.AddItems(self, items)

    def _GetInvCacheContainer(self):
        self.tradeSession.GetItem = self.tradeSession.GetSelfInvItem
        return self.tradeSession


def GetInvCtrlFromInvID(invID):
    if invID is None:
        return
    import invCtrl
    cls = getattr(invCtrl, invID[0], None)
    if cls:
        args = invID[1:]
        return cls(*args)


exports = {'invCtrl.LOOT_GROUPS': LOOT_GROUPS,
 'invCtrl.GetInvCtrlFromInvID': GetInvCtrlFromInvID}