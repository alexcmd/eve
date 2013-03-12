#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/station/fitting/slot.py
import sys
import uix
import uiutil
import mathUtil
import math
import uthread
import blue
import util
import lg
import service
import base
import uicls
import uiconst
import localization
MAXMODULEHINTWIDTH = 300

class FittingSlot(uicls.FittingSlotLayout):
    __guid__ = 'xtriui.FittingSlot'
    __notifyevents__ = ['OnRefreshModuleBanks']
    isDragObject = True

    def ApplyAttributes(self, attributes):
        uicls.FittingSlotLayout.ApplyAttributes(self, attributes)
        self.isInvItem = 1
        self.isChargeable = 0
        self.quantity = 1
        self.shell = None
        self.linkDragging = 0
        self.id = None
        self.charge = None
        self.scaleFactor = 1.0
        self.utilButtons = []
        self.backupHint = ''

    def IsItemHere(self, item):
        return item.flagID == self.flag and item.locationID == eve.session.shipid

    def Startup(self, flag, powerType, shell, scaleFactor = 1.0):
        self.flag = flag
        self.locationFlag = flag
        self.powerType = powerType
        self.invCache = sm.GetService('invCache')
        self._emptyHint = self.PrimeToEmptySlotHint()
        self.invReady = 1
        self.sr.groupMark.parent.left = int(self.sr.groupMark.parent.left * scaleFactor)
        self.sr.groupMark.parent.top = int(self.sr.groupMark.parent.top * scaleFactor)
        self.sr.groupMark.GetMenu = self.GetGroupMenu
        sm.RegisterNotify(self)
        self.SetFitting(None, shell)

    def OnRefreshModuleBanks(self):
        self.SetGroup()

    def OnDogmaAttributeChanged(self, shipID, itemID, attributeID, value):
        try:
            if self.module is not None and self.module.itemID == itemID and attributeID == const.attributeIsOnline:
                self.UpdateOnlineDisplay()
            elif attributeID == const.attributeQuantity:
                if not isinstance(itemID, tuple):
                    return
                shipID, flagID, typeID = itemID
                if shipID != self.shell.shipID or flagID != self.flag:
                    return
                if not value:
                    self.SetFitting(self.module)
                else:
                    chargeKey = self.shell.GetSubLocation(shipID, flagID)
                    if chargeKey is None:
                        self.LogError('Slot::Got OnDogmaAttributeChange for non zero value but no chargeKey', shipID, itemID, value)
                    charge = self.shell.dogmaItems[chargeKey]
                    self.SetFitting(charge)
        except ReferenceError:
            sys.exc_clear()

    def SetGroup(self):
        shipID = util.GetActiveShip()
        try:
            if self.module is not None and not self.shell.SlotExists(shipID, self.module.flagID):
                masterID = self.shell.IsInWeaponBank(self.module.locationID, self.id)
                if masterID:
                    self.shell.DestroyWeaponBank(self.module.locationID, masterID)
        except ReferenceError:
            pass

        allGroupsDict = settings.user.ui.Get('linkedWeapons_groupsDict', {})
        groupDict = allGroupsDict.get(shipID, {})
        ret = self.GetBankGroup(groupDict)
        if ret is None:
            self.sr.groupMark.parent.state = uiconst.UI_HIDDEN
            return
        groupNumber = ret.groupNumber
        self.sr.groupMark.parent.state = uiconst.UI_PICKCHILDREN
        self.sr.groupMark.parent.SetRotation(-self.GetRotation())
        if groupNumber < 0:
            availGroups = [1,
             2,
             3,
             4,
             5,
             6,
             7,
             8]
            for masterID, groupNum in groupDict.iteritems():
                if groupNum in availGroups:
                    availGroups.remove(groupNum)

            groupNumber = availGroups[0] if availGroups else ''
        self.sr.groupMark.LoadIcon('ui_73_16_%s' % (176 + groupNumber))
        self.sr.groupMark.hint = localization.GetByLabel('UI/Fitting/GroupNumber', groupNumber=groupNumber)
        groupDict[ret.masterID] = groupNumber
        allGroupsDict[shipID] = groupDict
        settings.user.ui.Set('linkedWeapons_groupsDict', allGroupsDict)

    def IsOnlineable(self):
        shipID = self.GetShipID()
        if self.module is None or not self.shell.SlotExists(shipID, self.module.flagID):
            return False
        try:
            return const.effectOnline in self.shell.dogmaStaticMgr.effectsByType[self.module.typeID]
        except ReferenceError:
            pass

    def GetBankGroup(self, groupDict):
        module = getattr(self, 'module', None)
        try:
            if not module:
                return
        except ReferenceError:
            return

        isInWeaponBank = self.shell.IsInWeaponBank(self.module.locationID, self.module.itemID)
        if not isInWeaponBank:
            return
        masterID = isInWeaponBank
        if masterID in groupDict:
            groupNumber = groupDict.get(masterID)
        else:
            groupNumber = -1
        ret = util.KeyVal()
        ret.masterID = masterID
        ret.groupNumber = groupNumber
        return ret

    def PrepareUtilButtons(self):
        for btn in self.utilButtons:
            btn.Close()

        self.utilButtons = []
        if not self.module:
            return
        toggleLabel = localization.GetByLabel('UI/Fitting/PutOffline') if bool(self.module.IsOnline) is True else localization.GetByLabel('UI/Fitting/PutOnline')
        myrad, cos, sin, cX, cY = self.radCosSin
        btns = []
        if self.charge:
            btns += [(localization.GetByLabel('UI/Fitting/RemoveCharge'),
              'ui_38_16_200',
              self.Unfit,
              1,
              0), (localization.GetByLabel('UI/Fitting/ShowChargeInfo'),
              'ui_38_16_208',
              self.ShowChargeInfo,
              1,
              0), ('',
              cfg.invtypes.Get(self.typeID).IconFile(),
              None,
              1,
              0)]
        isRig = False
        for effect in cfg.dgmtypeeffects.get(self.typeID, []):
            if effect.effectID == const.effectRigSlot:
                isRig = True
                break

        isSubSystem = cfg.invtypes.Get(self.typeID).categoryID == const.categorySubSystem
        isOnlinable = self.IsOnlineable()
        if isRig:
            btns += [(localization.GetByLabel('UI/Fitting/Destroy'),
              'ui_38_16_200',
              self.Unfit,
              1,
              0), (localization.GetByLabel('UI/Commands/ShowInfo'),
              'ui_38_16_208',
              self.ShowInfo,
              1,
              0)]
        elif isSubSystem:
            btns += [(localization.GetByLabel('UI/Commands/ShowInfo'),
              'ui_38_16_208',
              self.ShowInfo,
              1,
              0)]
        else:
            btns += [(localization.GetByLabel('UI/Fitting/UnfitModule'),
              'ui_38_16_200',
              self.UnfitModule,
              1,
              0), (localization.GetByLabel('UI/Commands/ShowInfo'),
              'ui_38_16_208',
              self.ShowInfo,
              1,
              0), (toggleLabel,
              'ui_38_16_207',
              self.ChangeOnline,
              isOnlinable,
              1)]
        rad = myrad - 34
        i = 0
        for hint, icon, func, active, onlinebtn in btns:
            left = int((rad - i * 16) * cos) + cX - 16 / 2
            top = int((rad - i * 16) * sin) + cY - 16 / 2
            icon = uicls.Icon(icon=icon, parent=self.parent, pos=(left,
             top,
             16,
             16), idx=0, pickRadius=-1, ignoreSize=True)
            icon.OnMouseEnter = self.ShowUtilButtons
            icon.hint = hint
            icon.color.a = 0.0
            icon.isActive = active
            if active:
                icon.OnClick = func
            else:
                shipID = self.GetShipID()
                if self.module is None or self.shell.SlotExists(shipID, self.module.flagID):
                    icon.hint = localization.GetByLabel('UI/Fitting/Disabled', moduleName=hint)
                else:
                    icon.hint = localization.GetByLabel('UI/Fitting/CantOnlineIllegalSlot')
            if onlinebtn == 1:
                self.sr.onlineButton = icon
            self.utilButtons.append(icon)
            i += 1

    def PrimeToEmptySlotHint(self):
        if self.flag in const.hiSlotFlags:
            return localization.GetByLabel('UI/Fitting/EmptyHighPowerSlot')
        if self.flag in const.medSlotFlags:
            return localization.GetByLabel('UI/Fitting/EmptyMediumPowerSlot')
        if self.flag in const.loSlotFlags:
            return localization.GetByLabel('UI/Fitting/EmptyLowPowerSlot')
        if self.flag in const.subSystemSlotFlags:
            return localization.GetByLabel('UI/Fitting/EmptySubsystemSlot')
        if self.flag in const.rigSlotFlags:
            return localization.GetByLabel('UI/Fitting/EmptyRigSlot')
        return localization.GetByLabel('UI/Fitting/EmptySlot')

    def SetFitting(self, invItem, shell = None, putOnline = 0):
        if self.destroyed:
            return
        lg.Info('fitting', 'SetFitting', self.flag, invItem and cfg.invtypes.Get(invItem.typeID).Group().name)
        if invItem is None:
            self.DisableDrag()
        else:
            self.EnableDrag()
        self.shell = shell or self.shell
        if invItem and self.IsCharge(invItem.typeID):
            self.charge = invItem
            chargeQty = self.shell.GetQuantity(invItem.itemID)
            if self.module is None:
                portion = 1.0
            else:
                cap = self.shell.GetCapacity(self.module.locationID, const.attributeCapacity, self.flag)
                if cap.capacity == 0:
                    portion = 1.0
                else:
                    portion = cap.used / cap.capacity
            step = max(0, min(4, int(portion * 5.0)))
            self.sr.chargeIndicator.rectTop = 10 * step
            self.sr.chargeIndicator.state = uiconst.UI_NORMAL
            self.sr.chargeIndicator.hint = '%s %d%%' % (cfg.invtypes.Get(self.charge.typeID).name, portion * 100)
        elif invItem is None:
            self.id = None
            self.isChargeable = 0
            self.typeID = None
            self.module = None
            self.charge = None
            self.fitted = 0
            self.isChargeable = 0
            self.HideUtilButtons(1)
            self.sr.chargeIndicator.state = uiconst.UI_HIDDEN
        else:
            self.id = invItem.itemID
            self.typeID = invItem.typeID
            self.module = invItem
            self.fitted = 1
            self.charge = None
            if invItem.groupID in cfg.__chargecompatiblegroups__:
                self.isChargeable = 1
                self.sr.chargeIndicator.rectTop = 0
                self.sr.chargeIndicator.state = uiconst.UI_NORMAL
                self.sr.chargeIndicator.hint = localization.GetByLabel('UI/Fitting/NoCharge')
            else:
                self.isChargeable = 0
                self.sr.chargeIndicator.state = uiconst.UI_HIDDEN
        if self.typeID:
            modulehint = cfg.invtypes.Get(self.typeID).name
            if self.charge:
                modulehint += '<br>%s' % localization.GetByLabel('UI/Fitting/ChargeQuantity', charge=self.charge.typeID, chargeQuantity=chargeQty)
            shipID = self.GetShipID()
            if not self.shell.SlotExists(shipID, self.module.flagID):
                modulehint = localization.GetByLabel('UI/Fitting/SlotDoesNotExist')
        else:
            modulehint = self._emptyHint
        self.backupHint = modulehint
        self.opacity = 1.0
        self.state = uiconst.UI_NORMAL
        self.PrepareUtilButtons()
        if putOnline:
            uthread.new(self.DelayedOnlineAttempt, eve.session.shipid, invItem.itemID)
        icon = self.sr.flagIcon
        icon.SetAlign(uiconst.CENTER)
        iconSize = int(48 * self.scaleFactor)
        icon.SetSize(iconSize, iconSize)
        icon.SetPosition(0, 0)
        if self.charge or self.module:
            icon.LoadIconByTypeID((self.charge or self.module).typeID, ignoreSize=True)
            icon.parent.SetRotation(-self.GetRotation())
        else:
            rev = 0
            slotIcon = {const.flagSubSystemSlot0: 'ui_81_64_9',
             const.flagSubSystemSlot1: 'ui_81_64_10',
             const.flagSubSystemSlot2: 'ui_81_64_11',
             const.flagSubSystemSlot3: 'ui_81_64_12',
             const.flagSubSystemSlot4: 'ui_81_64_13'}.get(self.flag, None)
            if slotIcon is None:
                slotIcon = {const.effectLoPower: 'ui_81_64_5',
                 const.effectMedPower: 'ui_81_64_6',
                 const.effectHiPower: 'ui_81_64_7',
                 const.effectRigSlot: 'ui_81_64_8'}.get(self.powerType, None)
            else:
                rev = 1
            if slotIcon is not None:
                icon.LoadIcon(slotIcon, ignoreSize=True)
            if rev:
                icon.parent.SetRotation(mathUtil.DegToRad(180.0))
            else:
                icon.parent.SetRotation(0.0)
        icon.state = uiconst.UI_PICKCHILDREN
        self.SetGroup()
        self.UpdateOnlineDisplay()
        self.Hilite(0)

    def ColorUnderlay(self, color = None):
        a = self.sr.underlay.color.a
        r, g, b = color or (1.0, 1.0, 1.0)
        self.sr.underlay.color.SetRGB(r, g, b, a)
        self.UpdateOnlineDisplay()

    def UpdateOnlineDisplay(self):
        if getattr(self, 'module', None) is not None and self.IsOnlineable():
            isActive = const.effectOnline in self.shell.dogmaStaticMgr.effectsByType[self.module.typeID]
            if self.module.IsOnline():
                self.sr.flagIcon.SetRGBA(1.0, 1.0, 1.0, 1.0)
                if util.GetAttrs(self, 'sr', 'onlineButton') and self.sr.onlineButton.hint == localization.GetByLabel('UI/Fitting/PutOnline'):
                    self.sr.onlineButton.hint = localization.GetByLabel('UI/Fitting/PutOffline')
                    uicore.UpdateHint(self.sr.onlineButton)
            else:
                self.sr.flagIcon.SetRGBA(1.0, 1.0, 1.0, 0.25)
                if util.GetAttrs(self, 'sr', 'onlineButton') and self.sr.onlineButton.hint == localization.GetByLabel('UI/Fitting/PutOffline'):
                    self.sr.onlineButton.hint = localization.GetByLabel('UI/Fitting/PutOnline')
                    uicore.UpdateHint(self.sr.onlineButton)
        elif self.sr.flagIcon:
            shipID = self.GetShipID()
            if self.module is None or self.shell.SlotExists(shipID, self.module.flagID):
                self.sr.flagIcon.SetRGBA(1.0, 1.0, 1.0, 1.0)
            else:
                self.sr.flagIcon.SetRGBA(0.7, 0.0, 0.0, 0.5)

    def DelayedOnlineAttempt(self, shipID, moduleID):
        blue.pyos.synchro.SleepWallclock(500)
        if shipID != eve.session.shipid:
            return
        ship = sm.GetService('godma').GetItem(shipID)
        if ship is not None:
            for module in ship.modules:
                if module.itemID == moduleID:
                    try:
                        online = getattr(module, 'online', None)
                        if online and not online.isActive:
                            self.OnlineClick()
                    except UserError as e:
                        if e.msg == 'ModuleTooDamagedToBeOnlined':
                            eve.Message(e.msg, e.dict)
                        elif not ('effectname' in e.dict and e.dict['effectname'] == 'online') or e.msg == 'ModuleTooDamagedToBeOnlined':
                            eve.Message(e.msg, e.dict)
                        sys.exc_clear()

                    return

    def AddItem(self, item):
        for each in sm.GetService('godma').GetItem(eve.session.shipid).modules:
            if each.itemID == item.itemID:
                self.SetFitting(each, putOnline=0)
                return
        else:
            self.SetFitting(item)

    def RemoveItem(self, item):
        if self.charge and self.charge.itemID == item.itemID:
            self.charge = None
            self.SetFitting(self.module)
        elif self.module and self.module.itemID == item.itemID:
            self.SetFitting(None)

    def IsCharge(self, typeID):
        return cfg.invtypes.Get(typeID).categoryID == const.categoryCharge

    def Add(self, item, sourceLocation = None):
        if not getattr(item, 'typeID', None):
            return
        if not sm.GetService('menu').RigFittingCheck(item):
            return
        requiredSkills = sm.GetService('info').GetRequiredSkills(item.typeID)
        for skillID, level in requiredSkills:
            if getattr(sm.GetService('skills').HasSkill(skillID), 'skillLevel', 0) < level:
                sm.GetService('tutorial').OpenTutorialSequence_Check(uix.skillfittingTutorial)
                break

        if self.IsCharge(item.typeID) and self.isChargeable:
            self.shell.inventory.Add(item.itemID, item.locationID, qty=1, flag=self.locationFlag)
        validFitting = False
        for effect in cfg.dgmtypeeffects.get(item.typeID, []):
            if effect.effectID in (const.effectHiPower,
             const.effectMedPower,
             const.effectLoPower,
             const.effectSubSystem,
             const.effectRigSlot):
                validFitting = True
                if effect.effectID == self.powerType:
                    ship = self.shell.GetShip()
                    if ship:
                        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
                        isFitted = item.locationID == self.shell.shipID and item.flagID != const.flagCargo
                        if isFitted and shift:
                            if getattr(self, 'module', None):
                                if self.module.typeID == item.typeID:
                                    self.shell.LinkWeapons(self.module.locationID, self.module.itemID, item.itemID)
                                    return
                                else:
                                    eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Fitting/GroupingIncompatible')})
                                    return
                        self.shell.TryFit(item, self.locationFlag)
                    return
                eve.Message('ItemDoesntFitPower', {'item': cfg.invtypes.Get(item.typeID).name,
                 'slotpower': cfg.dgmeffects.Get(self.powerType).displayName,
                 'itempower': cfg.dgmeffects.Get(effect.effectID).displayName})

        if not validFitting:
            raise UserError('ItemNotHardware', {'itemname': item.typeID})

    def SetState(self, *args):
        self.UpdateOnlineDisplay()

    def OnlineClick(self, *args):
        effect = None
        for module in self.shell.modules:
            if module.itemID == self.id:
                effect = module.online

        if effect:
            effect.Toggle()

    def GetMenu(self):
        if self.typeID and self.id:
            m = []
            if eve.session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
                m += [(str(self.id), self.CopyItemIDToClipboard, (self.id,)), None]
            m += [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo)]
            if self.shell.dogmaStaticMgr.TypeHasEffect(self.module.typeID, const.effectRigSlot):
                m += [(uiutil.MenuLabel('UI/Fitting/Destroy'), self.Unfit)]
            else:
                if session.stationid2 is not None:
                    m += [(uiutil.MenuLabel('UI/Fitting/Unfit'), self.Unfit)]
                if self.IsOnlineable():
                    if self.module.IsOnline():
                        m.append((uiutil.MenuLabel('UI/Fitting/PutOffline'), self.ChangeOnline))
                    else:
                        m.append((uiutil.MenuLabel('UI/Fitting/PutOnline'), self.ChangeOnline))
            m += self.GetGroupMenu()
            return m

    def GetGroupMenu(self, *args):
        masterID = self.shell.IsInWeaponBank(self.module.locationID, self.id)
        if masterID:
            return [(uiutil.MenuLabel('UI/Fitting/ClearGroup'), self.UnlinkModule, (masterID,))]
        return []

    def OnClick(self, *args):
        uicore.registry.SetFocus(self)
        if self.IsOnlineable():
            self.ChangeOnline()

    def ChangeOnline(self):
        if self.module.IsOnline():
            if self.module.dogmaLocation.IsInWeaponBank(self.module.locationID, self.module.itemID):
                ret = eve.Message('CustomQuestion', {'header': localization.GetByLabel('UI/Common/Confirm'),
                 'question': localization.GetByLabel('UI/Fitting/QueryGroupOffline')}, uiconst.YESNO)
                if ret != uiconst.ID_YES:
                    return
            self.module.dogmaLocation.OfflineModule(self.module.itemID)
        else:
            self.module.dogmaLocation.OnlineModule(self.module.itemID)
        self.UpdateOnlineDisplay()

    def CopyItemIDToClipboard(self, itemID):
        blue.pyos.SetClipboardData(str(itemID))

    def ShowChargeInfo(self, *args):
        if self.charge:
            sm.GetService('info').ShowInfo(self.charge.typeID, self.charge.itemID)

    def ShowInfo(self, *args):
        sm.GetService('info').ShowInfo(self.typeID, self.id)

    def GetShipID(self):
        if self.module is not None:
            return self.module.locationID
        elif self.charge is not None:
            return self.charge.locationID
        else:
            return

    def UnfitModule(self, *args):
        if self.module is None:
            return
        shipID = self.GetShipID()
        if shipID is None:
            return
        masterID = self.shell.IsInWeaponBank(shipID, self.id)
        if masterID:
            ret = eve.Message('CustomQuestion', {'header': localization.GetByLabel('UI/Common/Confirm'),
             'question': localization.GetByLabel('UI/Fitting/ClearGroupModule')}, uiconst.YESNO)
            if ret != uiconst.ID_YES:
                return
            self.module.dogmaLocation.UngroupModule(shipID, masterID)
        if self.charge is not None:
            self.UnfitCharge()
        if session.stationid2:
            self.invCache.GetInventory(const.containerHangar).Add(self.id, shipID)
        else:
            shipInv = self.invCache.GetInventoryFromId(shipID, locationID=session.stationid2)
            shipInv.Add(self.id, shipID, qty=None, flag=const.flagCargo)

    def UnfitCharge(self):
        shipID = self.GetShipID()
        if shipID is None:
            return
        shipInv = self.invCache.GetInventoryFromId(shipID, locationID=session.stationid2)
        if isinstance(self.charge.itemID, tuple):
            chargeIDs = self.shell.GetSubLocationsInBank(shipID, self.charge.itemID)
            if chargeIDs:
                if session.stationid2:
                    self.invCache.GetInventory(const.containerHangar).MultiAdd(chargeIDs, shipID, flag=const.flagHangar, fromManyFlags=True)
                else:
                    self.invCache.GetInventoryFromId(eve.session.shipid).MultiAdd(chargeIDs, shipID, flag=const.flagCargo)
            elif session.stationid2:
                shipInv.RemoveChargeToHangar(self.charge.itemID)
            else:
                shipInv.RemoveChargeToCargo(self.charge.itemID)
        else:
            crystalIDs = self.shell.GetCrystalsInBank(shipID, self.charge.itemID)
            if crystalIDs:
                if session.stationid2:
                    self.invCache.GetInventory(const.containerHangar).MultiAdd(crystalIDs, shipID, flag=const.flagHangar, fromManyFlags=True)
                else:
                    shipInv.MultiAdd(crystalIDs, shipID, flag=const.flagCargo)
            elif session.stationid2:
                self.invCache.GetInventory(const.containerHangar).Add(self.charge.itemID, shipID)
            else:
                shipInv.Add(self.charge.itemID, shipID, qty=None, flag=const.flagCargo)

    def Unfit(self, *args):
        shipID = self.GetShipID()
        if shipID is None:
            return
        shipInv = self.invCache.GetInventoryFromId(shipID, locationID=session.stationid2)
        if self.powerType == const.effectRigSlot:
            ret = eve.Message('RigUnFittingInfo', {}, uiconst.OKCANCEL)
            if ret != uiconst.ID_OK:
                return
            shipInv.DestroyFitting(self.id)
        elif self.charge:
            self.UnfitCharge()
        else:
            self.UnfitModule()

    def UnlinkModule(self, masterID):
        self.shell.DestroyWeaponBank(self.module.locationID, masterID)

    def _OnEndDrag(self, *args):
        self.left = self.top = -2

    def OnEndDrag(self, *args):
        if self.module is not None:
            sm.ScatterEvent('OnResetSlotLinkingMode', self.module.typeID)

    def OnMouseEnter(self, *args):
        if getattr(self, 'module', None) is not None:
            self.ShowUtilButtons()
            if settings.user.ui.Get('showModuleTooltips', 1):
                self.moduleHintTimer = base.AutoTimer(200, self.ShowHint)
            elif self.backupHint:
                self.hint = self.backupHint
        else:
            self.Hilite(1)
            eve.Message('ListEntryEnter')

    def OnMouseExit(self, *args):
        if not getattr(self, 'module', None):
            self.Hilite(0)
        if getattr(uicore.layer.hint, 'moduleButtonHint', None) is not None:
            uicore.layer.hint.moduleButtonHint.FadeOpacity(0.0)
        self.moduleHintTimer = None
        self.updateTimer = None
        self.hint = ''

    def ShowHint(self, *args):
        self.moduleHintTimer = None
        if len(uicore.layer.menu.children) > 0:
            return
        self.updateTimer = base.AutoTimer(1000, self.UpdateInfo_TimedCall)
        if getattr(uicore.layer.hint, 'moduleButtonHint', None) is None or uicore.layer.hint.moduleButtonHint.destroyed:
            moduleButtonHint = uicls.ModuleButtonHint(parent=uicore.layer.hint, name='moduleButtonHint', align=uiconst.TOPLEFT, pos=(0,
             0,
             MAXMODULEHINTWIDTH,
             200))
            moduleButtonHint.opacity = 0.0
            uicore.layer.hint.moduleButtonHint = moduleButtonHint
        self.UpdateInfo_TimedCall()
        self.PositionHint()
        uicore.layer.hint.moduleButtonHint.FadeOpacity(1.0)

    def UpdateInfo_TimedCall(self, *args):
        if self.typeID:
            itemID = self.id
            if self.charge:
                chargeItemID = self.charge.itemID
            else:
                chargeItemID = None
            if getattr(uicore.layer.hint, 'moduleButtonHint', None) is None or uicore.layer.hint.moduleButtonHint.destroyed:
                moduleButtonHint = uicls.ModuleButtonHint(parent=uicore.layer.hint, name='moduleButtonHint', align=uiconst.TOPLEFT, pos=(0,
                 0,
                 MAXMODULEHINTWIDTH,
                 200))
                moduleButtonHint.opacity = 0.0
                uicore.layer.hint.moduleButtonHint = moduleButtonHint
            uicore.layer.hint.moduleButtonHint.UpdateAllInfo(itemID, chargeItemID, positionTuple=None, fromWhere='fitting')

    def PositionHint(self, *args):
        moduleHint = uicore.layer.hint.moduleButtonHint
        if moduleHint.parent is None or self.parent is None:
            moduleHint.Close()
            return
        myRotation = self.rotation + 2 * math.pi
        myRotation = -myRotation
        sl, st, sw, sh = self.parent.GetAbsolute()
        cX = sl + sw / 2.0
        cY = st + sh / 2.0
        w, h = moduleHint.GetAbsoluteSize()
        rad, cos, sin, oldcX, oldcY = self.radCosSin
        hintLeft = int(round((rad + 30) * cos + cX))
        hintTop = int(round((rad + 30) * sin + cY))
        if myRotation < 0 or myRotation >= 1.5 * math.pi:
            myTop = hintTop - moduleHint.height
            myLeft = hintLeft - moduleHint.width
            if myTop < 0:
                myTop = 0
                myLeft -= 20
            if myLeft < 0:
                myLeft = 0
                myTop = self.absoluteBottom
        elif 0 <= myRotation < 0.5 * math.pi:
            myTop = hintTop - moduleHint.height
            myLeft = hintLeft
            if myTop < 0:
                myTop = 0
                myLeft += 20
            if myLeft > uicore.desktop.width - moduleHint.width:
                myLeft = uicore.desktop.width - moduleHint.width
                myTop = self.absoluteBottom
        elif 0.5 * math.pi <= myRotation < 1.0 * math.pi:
            myTop = hintTop
            myLeft = hintLeft
            if myTop + moduleHint.height > uicore.desktop.height:
                myTop = uicore.desktop.height - moduleHint.height
                myLeft += 20
            if myLeft > uicore.desktop.width - moduleHint.width:
                myLeft = uicore.desktop.width - moduleHint.width
                myTop = self.absoluteTop - moduleHint.height
        else:
            myTop = hintTop
            myLeft = hintLeft - moduleHint.width
            if myTop + moduleHint.height > uicore.desktop.height:
                myTop = uicore.desktop.height - moduleHint.height
                myLeft -= 20
            if myLeft < 0:
                myLeft = 0
                myTop = self.absoluteTop - moduleHint.height
        moduleHint.top = myTop
        moduleHint.left = myLeft

    def ShowUtilButtons(self, *args):
        fittingbase = self.FindParentByName('fittingbase')
        fittingbase.ClearSlotsWithMenu()
        fittingbase.AddToSlotsWithMenu(self)
        for button in self.utilButtons:
            if button.isActive:
                button.color.a = 1.0
            else:
                button.color.a = 0.25

        self.utilButtonsTimer = base.AutoTimer(500, self.HideUtilButtons)

    def HideUtilButtons(self, force = 0):
        mo = uicore.uilib.mouseOver
        if not force and (mo in self.utilButtons or mo == self or uiutil.IsUnder(mo, self)):
            return
        for button in self.utilButtons:
            button.color.a = 0.0

        self.utilButtonsTimer = None

    def Hilite(self, state):
        if state:
            self.sr.underlay.color.a = 1.0
        else:
            self.sr.underlay.color.a = 0.3

    def GetDragData(self, *args):
        l = []
        if not self.IsChargeEmpty():
            l.extend(self.GetChargeDragNodes())
        if l:
            return l
        if getattr(self, 'module', None) is None:
            return l
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        if shift:
            isGroupable = self.module.groupID in const.dgmGroupableGroupIDs
            if not isGroupable:
                return []
            if getattr(self, 'module', None):
                sm.ScatterEvent('OnStartSlotLinkingMode', self.module.typeID)
        return self.shell.GetDragData(self.module.itemID)

    def OnDropData(self, dragObj, nodes):
        shipID = self.GetShipID()
        if self.module is not None and not self.shell.SlotExists(shipID, self.module.flagID):
            return
        chargeTypeID = None
        chargeItems = []
        for node in nodes:
            if node.__guid__ not in ('listentry.InvItem', 'xtriui.InvItem'):
                continue
            item = node.rec
            if not getattr(item, 'typeID', None):
                lg.Info('fittingUI', 'Dropped a non-item here', item)
                return
            if self.isChargeable and self.IsCharge(item.typeID):
                if chargeTypeID is None:
                    chargeTypeID = item.typeID
                if chargeTypeID == item.typeID:
                    chargeItems.append(item)
            elif self.shell.IsInWeaponBank(item.locationID, item.itemID):
                ret = eve.Message('CustomQuestion', {'header': localization.GetByLabel('UI/Common/Confirm'),
                 'question': localization.GetByLabel('UI/Fitting/ClearGroupModule')}, uiconst.YESNO)
                if ret == uiconst.ID_YES:
                    eve.Message('DragDropSlot')
                    uthread.new(self.Add, item)
            elif item.categoryID == const.categorySubSystem and getattr(self, 'module', None) is not None:
                uthread.new(self.Add, item)
            else:
                eve.Message('DragDropSlot')
                uthread.new(self.Add, item)

        if len(chargeItems):
            chargeTypeID = chargeItems[0].typeID
            self.shell.DropLoadChargeToModule(self.module.itemID, chargeTypeID, chargeItems)

    def IsChargeEmpty(self):
        return self.charge is None

    def GetChargeType(self):
        if self.IsChargeEmpty():
            return None
        return self.charge.typeID

    def GetChargeDragNodes(self, *args):
        if not self.charge:
            return []
        return self.shell.GetDragData(self.charge.itemID)

    def _OnClose(self, *args):
        self.updateTimer = None
        moduleButtonHint = getattr(uicore.layer.hint, 'moduleButtonHint', None)
        if moduleButtonHint and not moduleButtonHint.destroyed:
            if moduleButtonHint.fromWhere == 'fitting':
                uicore.layer.hint.moduleButtonHint.FadeOpacity(0.0)


exports = {'xtriui.FittingSlot': FittingSlot}