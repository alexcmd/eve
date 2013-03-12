#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/inflight/shipmodulebutton.py
import uthread
import uix
import mathUtil
import base
import util
import blue
import service
import re
import state
import math
import uiutil
import uicls
import menu
import uiconst
import log
import localization
import localizationUtil
import godma
import trinity
import crimewatchConst
cgre = re.compile('chargeGroup\\d{1,2}')
GLOWCOLOR = (0.24,
 0.67,
 0.16,
 0.75)
BUSYCOLOR = (1.0,
 0.13,
 0.0,
 0.73)
OVERLOADBTN_INDEX = 1
MODULEHINTDELAY = 800
MAXMODULEHINTWIDTH = 300

class ModuleButton(uicls.Container):
    __guid__ = 'xtriui.ModuleButton'
    __notifyevents__ = ['OnStateChange',
     'OnItemChange',
     'OnModuleRepaired',
     'OnAmmoInBankChanged',
     'OnFailLockTarget',
     'OnChargeBeingLoadedToModule']
    __update_on_reload__ = 1
    __cgattrs__ = []
    __loadingcharges__ = []
    __chargesizecache__ = {}
    default_name = 'ModuleButton'
    default_pickRadius = 20
    isDragObject = True
    def_effect = None
    charge = None
    target = None
    waitingForActiveTarget = 0
    changingAmmo = 0
    reloadingAmmo = False
    online = False
    stateManager = None
    dogmaLocation = None
    autorepeat = 0
    autoreload = 0
    quantity = None
    invReady = 1
    invCookie = None
    isInvItem = 1
    isBeingRepaired = 0
    blinking = 0
    blinkingDamage = 0
    effect_activating = 0
    typeName = ''
    ramp_active = False
    isMaster = 0
    animation = None
    isPendingUnlockForDeactivate = False
    moduleHintTimer = None
    shouldUpdate = False

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.icon = uicls.Icon(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED)
        sm.RegisterNotify(self)

    def _OnClose(self):
        if getattr(self, 'invCookie', None) is not None:
            sm.GetService('inv').Unregister(self.invCookie)
        if getattr(uicore.layer.hint, 'moduleButtonHint', None) and not uicore.layer.hint.moduleButtonHint.destroyed:
            uicore.layer.hint.moduleButtonHint.Close()
        uicls.Container._OnClose(self)

    def Setup(self, moduleinfo, grey = None):
        self.crimewatchSvc = sm.GetService('crimewatchSvc')
        moduleButtonHint = getattr(uicore.layer.hint, 'moduleButtonHint', None)
        if moduleButtonHint is None or moduleButtonHint.destroyed:
            moduleButtonHint = uicls.ModuleButtonHint(parent=uicore.layer.hint, name='moduleButtonHint', align=uiconst.TOPLEFT, pos=(0,
             0,
             MAXMODULEHINTWIDTH,
             200))
            moduleButtonHint.opacity = 0.0
            uicore.layer.hint.moduleButtonHint = moduleButtonHint
            moduleButtonHint.display = False
        if not len(self.__cgattrs__):
            self.__cgattrs__.extend([ a.attributeID for a in cfg.dgmattribs if cgre.match(a.attributeName) is not None ])
        invType = cfg.invtypes.Get(moduleinfo.typeID)
        group = cfg.invtypes.Get(moduleinfo.typeID).Group()
        self.id = moduleinfo.itemID
        self.sr.moduleInfo = moduleinfo
        self.locationFlag = moduleinfo.flagID
        self.stateManager = sm.StartService('godma').GetStateManager()
        self.dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        self.grey = grey
        self.isInActiveState = True
        self.isDeactivating = False
        icon = uiutil.GetChild(self.parent, 'overloadBtn')
        icon.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOnOverload')
        icon.OnClick = self.ToggleOverload
        icon.OnMouseDown = (self.OLButtonDown, icon)
        icon.OnMouseUp = (self.OLButtonUp, icon)
        icon.OnMouseExit = (self.OLMouseExit, icon)
        icon.SetOrder(OVERLOADBTN_INDEX)
        self.sr.overloadButton = icon
        if cfg.IsChargeCompatible(moduleinfo):
            self.invCookie = sm.GetService('inv').Register(self)
        self.autoreload = settings.char.autoreload.Get(self.sr.moduleInfo.itemID, 1)
        if group.categoryID == const.categoryCharge:
            self.SetCharge(moduleinfo)
        else:
            self.SetCharge(None)
        self.autoreload = settings.char.autoreload.Get(self.sr.moduleInfo.itemID, 1)
        for key in moduleinfo.effects.iterkeys():
            effect = moduleinfo.effects[key]
            if self.IsEffectActivatible(effect):
                self.def_effect = effect
                if effect.isActive:
                    if effect.isDeactivating:
                        self.SetDeactivating()
                    else:
                        self.SetActive()
            if effect.effectName == 'online':
                if effect.isActive:
                    self.ShowOnline()
                else:
                    self.ShowOffline()

        self.autoreload = settings.char.autoreload.Get(self.sr.moduleInfo.itemID, 1)
        self.isBeingRepaired = self.stateManager.IsModuleBeingRepaired(self.id)
        if self.isBeingRepaired:
            self.SetRepairing()
        repeat = settings.char.autorepeat.Get(self.sr.moduleInfo.itemID, -1)
        if group.groupID in (const.groupMiningLaser, const.groupStripMiner):
            self.SetRepeat(1000)
        elif repeat != -1:
            self.SetRepeat(repeat)
        else:
            repeatSet = 0
            for key in self.sr.moduleInfo.effects.iterkeys():
                effect = self.sr.moduleInfo.effects[key]
                if self.IsEffectRepeatable(effect):
                    self.SetRepeat(1000)
                    repeatSet = 1
                    break

            if not repeatSet:
                self.SetRepeat(0)
        self.autoreload = settings.char.autoreload.Get(self.sr.moduleInfo.itemID, 1)
        if not self.isDeactivating:
            self.isInActiveState = True
        else:
            self.isInActiveState = False
        self.slaves = self.dogmaLocation.GetSlaveModules(self.sr.moduleInfo.itemID, session.shipid)
        moduleDamage = self.GetModuleDamage()
        if moduleDamage:
            self.SetDamage(moduleDamage / moduleinfo.hp)
        else:
            self.SetDamage(0.0)
        self.EnableDrag()
        self.autoreload = settings.char.autoreload.Get(self.sr.moduleInfo.itemID, 1)
        uthread.new(self.BlinkIcon)

    def OLButtonDown(self, btn, *args):
        btn.top = 6

    def OLButtonUp(self, btn, *args):
        btn.top = 5

    def OLMouseExit(self, btn, *args):
        btn.top = 5

    def ToggleOverload(self, *args):
        if settings.user.ui.Get('lockOverload', 0):
            eve.Message('error')
            eve.Message('LockedOverloadState')
            return
        for effect in self.sr.moduleInfo.effects.itervalues():
            if effect.effectCategory == const.dgmEffOverload:
                effectID = effect.effectID
                break
        else:
            return

        overloadState = self.stateManager.GetOverloadState(self.sr.moduleInfo.itemID)
        eve.Message('click')
        itemID = self.sr.moduleInfo.itemID
        if overloadState == godma.MODULE_NOT_OVERLOADED:
            self.stateManager.Overload(itemID, effectID)
            self.sr.overloadButton.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOffOverload')
        elif overloadState == godma.MODULE_OVERLOADED:
            self.stateManager.StopOverload(itemID, effectID)
            self.sr.overloadButton.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOnOverload')
        elif overloadState == godma.MODULE_PENDING_OVERLOADING:
            self.stateManager.StopOverload(itemID, effectID)
        elif overloadState == godma.MODULE_PENDING_STOPOVERLOADING:
            self.stateManager.StopOverload(itemID, effectID)

    def UpdateOverloadState(self):
        overloadState = self.stateManager.GetOverloadState(self.sr.moduleInfo.itemID)
        if overloadState == godma.MODULE_PENDING_OVERLOADING:
            self.animation = uicore.animations.BlinkIn(self.sr.overloadButton, startVal=1.8, endVal=1.0, duration=0.5, loops=uiconst.ANIM_REPEAT)
        elif overloadState == godma.MODULE_PENDING_STOPOVERLOADING:
            self.animation = uicore.animations.BlinkIn(self.sr.overloadButton, startVal=0.2, endVal=1.0, duration=0.5, loops=uiconst.ANIM_REPEAT)
        else:
            if self.animation:
                self.animation.Stop()
            self.sr.overloadButton.SetAlpha(1.0)
        if overloadState == godma.MODULE_OVERLOADED:
            self.sr.overloadButton.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOffOverload')
        elif overloadState == godma.MODULE_NOT_OVERLOADED:
            self.sr.overloadButton.hint = localization.GetByLabel('UI/Inflight/Overload/TurnOnOverload')

    def InitQuantityLabel(self):
        if self.sr.qtylabel is None:
            quantityParent = uicls.Container(parent=self, name='quantityParent', pos=(18, 27, 24, 10), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0)
            self.sr.qtylabel = uicls.Label(text='', parent=quantityParent, fontsize=9, letterspace=1, left=3, top=0, width=30, state=uiconst.UI_DISABLED)
            underlay = uicls.Sprite(parent=quantityParent, name='underlay', pos=(0, 0, 0, 0), align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/slotQuantityUnderlay.png', color=(0.0, 0.0, 0.0, 1.0))

    def SetCharge(self, charge):
        if charge and charge.stacksize != 0:
            if self.charge is None or charge.typeID != self.charge.typeID:
                self.icon.LoadIconByTypeID(charge.typeID)
            self.charge = charge
            self.stateManager.ChangeAmmoTypeForModule(self.sr.moduleInfo.itemID, charge.typeID)
            self.id = charge.itemID
            self.UpdateChargeQuantity(charge)
        else:
            self.icon.LoadIconByTypeID(self.sr.moduleInfo.typeID)
            if self.sr.qtylabel:
                self.sr.qtylabel.parent.state = uiconst.UI_HIDDEN
            self.quantity = 0
            self.id = self.sr.moduleInfo.itemID
            self.charge = None
        self.CheckOverload()
        self.CheckOnline()
        self.CheckMasterSlave()

    def UpdateChargeQuantity(self, charge):
        if charge is self.charge:
            if cfg.invtypes.Get(charge.typeID).groupID in cfg.GetCrystalGroups():
                if self.sr.qtylabel:
                    self.sr.qtylabel.parent.state = uiconst.UI_HIDDEN
                return
            self.InitQuantityLabel()
            self.quantity = charge.stacksize
            self.sr.qtylabel.text = '%s' % util.FmtAmt(charge.stacksize)
            self.sr.qtylabel.parent.state = uiconst.UI_DISABLED

    def ShowGroupHighlight(self):
        self.dragging = True
        if self.sr.groupHighlight is None:
            groupHighlight = uicls.Container(parent=self.parent, name='groupHighlight', pos=(0, 0, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
            leftCircle = uicls.Sprite(parent=groupHighlight, name='leftCircle', pos=(0, 0, 32, 64), texturePath='res:/UI/Texture/classes/ShipUI/slotRampLeft.png')
            rightCircle = uicls.Sprite(parent=groupHighlight, name='leftCircle', pos=(32, 0, 32, 64), texturePath='res:/UI/Texture/classes/ShipUI/slotRampRight.png')
            self.sr.groupHighlight = groupHighlight
        else:
            self.sr.groupHighlight.state = uiconst.UI_DISABLED
        uthread.new(self.PulseGroupHighlight)

    def StopShowingGroupHighlight(self):
        self.dragging = False
        if self.sr.groupHighlight:
            self.sr.groupHighlight.state = uiconst.UI_HIDDEN

    def PulseGroupHighlight(self):
        pulseSize = 0.4
        opacity = 1.0
        startTime = blue.os.GetSimTime()
        while self.dragging:
            self.sr.groupHighlight.opacity = opacity
            blue.pyos.synchro.SleepWallclock(200)
            if not self or self.destroyed:
                break
            sinWave = math.cos(float(blue.os.GetSimTime() - startTime) / (0.5 * const.SEC))
            opacity = min(sinWave * pulseSize + (1 - pulseSize / 2), 1)

    def SetDamage(self, damage):
        if not damage or damage < 0.0001:
            if self.sr.damageState:
                self.sr.damageState.state = uiconst.UI_HIDDEN
            return
        imageIndex = max(1, int(damage * 8))
        if self.sr.damageState is None:
            if self.sr.ramps:
                idx = OVERLOADBTN_INDEX + 2
            else:
                idx = OVERLOADBTN_INDEX + 1
            self.sr.damageState = uicls.Sprite(parent=self.parent, name='damageState', pos=(0, 0, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL, texturePath='res:/UI/Texture/classes/ShipUI/slotDamage_%s.png' % imageIndex, idx=idx)
        else:
            self.sr.damageState.LoadTexture('res:/UI/Texture/classes/ShipUI/slotDamage_%s.png' % imageIndex)
            self.sr.damageState.state = uiconst.UI_NORMAL
        amount = self.sr.moduleInfo.damage / self.sr.moduleInfo.hp * 100
        self.sr.damageState.hint = localization.GetByLabel('UI/Inflight/Overload/hintDamagedModule', preText='', amount=amount)
        sm.GetService('ui').BlinkSpriteA(self.sr.damageState, 1.0, 2000 - 1000 * damage, 2, passColor=0)

    def GetVolume(self):
        if self.charge:
            return cfg.GetItemVolume(self.charge, 1)

    def IsItemHere(self, rec):
        ret = rec.locationID == eve.session.shipid and rec.flagID == self.locationFlag and cfg.invtypes.Get(rec.typeID).Group().Category().id == const.categoryCharge
        return ret

    def AddItem(self, rec):
        if cfg.invtypes.Get(rec.typeID).categoryID == const.categoryCharge:
            self.SetCharge(rec)

    def UpdateItem(self, rec, change):
        if cfg.invtypes.Get(rec.typeID).categoryID == const.categoryCharge:
            self.SetCharge(rec)

    def RemoveItem(self, rec):
        if cfg.invtypes.Get(rec.typeID).categoryID == const.categoryCharge:
            if self.charge and rec.itemID == self.id:
                self.SetCharge(None)

    def GetShell(self):
        return sm.GetService('invCache').GetInventoryFromId(eve.session.shipid)

    def IsCorrectChargeSize(self, item, wantChargeSize):
        if not self.__chargesizecache__.has_key(item.typeID):
            cRS = cfg.dgmtypeattribs.get(item.typeID, [])
            cAttribs = util.IndexedRows(cRS, ('attributeID',))
            if cAttribs.has_key(const.attributeChargeSize):
                gotChargeSize = cAttribs[const.attributeChargeSize].value
            else:
                gotChargeSize = 0
            self.__chargesizecache__[item.typeID] = gotChargeSize
        else:
            gotChargeSize = self.__chargesizecache__[item.typeID]
        if wantChargeSize != gotChargeSize:
            return 0
        return 1

    def UnloadToCargo(self, itemID):
        self.reloadingAmmo = True
        try:
            self.dogmaLocation.UnloadChargeToContainer(session.shipid, itemID, (session.shipid,), const.flagCargo)
        finally:
            self.reloadingAmmo = False

    def ReloadAmmo(self, itemID, quantity, preferSingletons = False):
        if not quantity:
            return
        self.reloadingAmmo = True
        lastChargeTypeID = self.stateManager.GetAmmoTypeForModule(self.sr.moduleInfo.itemID)
        try:
            self.dogmaLocation.LoadChargeToModule(self.sr.moduleInfo.itemID, lastChargeTypeID, preferSingletons=preferSingletons)
        finally:
            self.reloadingAmmo = False

    def ReloadAllAmmo(self):
        uicore.cmd.CmdReloadAmmo()

    def BlinkIcon(self, time = None):
        if self.destroyed or self.blinking:
            return
        startTime = blue.os.GetSimTime()
        if time is not None:
            timeToBlink = time * 10000
        while self.changingAmmo or self.reloadingAmmo or self.waitingForActiveTarget or time:
            if time is not None:
                if blue.os.GetSimTime() - startTime > timeToBlink:
                    break
            blue.pyos.synchro.SleepWallclock(250)
            if self.destroyed:
                return
            self.icon.SetAlpha(0.25)
            blue.pyos.synchro.SleepWallclock(250)
            if self.destroyed:
                return
            self.icon.SetAlpha(1.0)

        if self.destroyed:
            return
        self.blinking = 0
        self.CheckOverload()
        self.CheckOnline()

    def ChangeAmmo(self, itemID, quantity, ammoType):
        if not quantity:
            return
        self.changingAmmo = 1
        try:
            self.dogmaLocation.LoadChargeToModule(itemID, ammoType, qty=quantity)
        finally:
            if self and not self.destroyed:
                self.changingAmmo = 0

    def DoNothing(self, *args):
        pass

    def CopyItemIDToClipboard(self, itemID):
        blue.pyos.SetClipboardData(str(itemID))

    def GetMenu(self):
        ship = sm.GetService('godma').GetItem(eve.session.shipid)
        if ship is None:
            return []
        m = []
        if eve.session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
            if cfg.IsChargeCompatible(self.sr.moduleInfo):
                m += [('Launcher: ' + str(self.sr.moduleInfo.itemID), self.CopyItemIDToClipboard, (self.sr.moduleInfo.itemID,))]
                if self.id != self.sr.moduleInfo.itemID:
                    m += [('Charge: ' + str(self.id), self.CopyItemIDToClipboard, (self.id,)), None]
            else:
                m += [(str(self.id), self.CopyItemIDToClipboard, (self.id,)), None]
            m += sm.GetService('menu').GetGMTypeMenu(self.sr.moduleInfo.typeID, itemID=self.id, divs=True, unload=True)
        moduleType = cfg.invtypes.Get(self.sr.moduleInfo.typeID)
        groupID = moduleType.groupID
        if cfg.IsChargeCompatible(self.sr.moduleInfo):
            chargeTypeID, chargeQuantity, roomForReload = self.GetChargeReloadInfo()
            chargeID = self.charge.itemID if self.charge is not None else None
            m.extend(self.dogmaLocation.GetAmmoMenu(session.shipid, self.sr.moduleInfo.itemID, chargeID, roomForReload))
            if self.autoreload == 0:
                m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/AutoReloadOn'), self.SetAutoReload, (1,)))
            else:
                m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/AutoReloadOff'), self.SetAutoReload, (0,)))
        overloadLock = settings.user.ui.Get('lockOverload', 0)
        itemID = self.sr.moduleInfo.itemID
        slaves = self.dogmaLocation.GetSlaveModules(itemID, session.shipid)
        for key in self.sr.moduleInfo.effects.iterkeys():
            effect = self.sr.moduleInfo.effects[key]
            if self.IsEffectRepeatable(effect) and groupID not in (const.groupMiningLaser, const.groupStripMiner):
                if self.autorepeat == 0:
                    m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/AutoRepeatOn'), self.SetRepeat, (1000,)))
                else:
                    m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/AutoRepeatOff'), self.SetRepeat, (0,)))
            if effect.effectName == 'online':
                m.append(None)
                if not slaves:
                    if effect.isActive:
                        m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/PutModuleOffline'), self.ChangeOnline, (0,)))
                    else:
                        m.append((uiutil.MenuLabel('UI/Inflight/ModuleRacks/PutModuleOnline'), self.ChangeOnline, (1,)))
            if not overloadLock and effect.effectCategory == const.dgmEffOverload:
                active = effect.isActive
                if active:
                    m.append((uiutil.MenuLabel('UI/Inflight/Overload/TurnOffOverload'), self.Overload, (0, effect)))
                else:
                    m.append((uiutil.MenuLabel('UI/Inflight/Overload/TurnOnOverload'), self.Overload, (1, effect)))
                m.append((uiutil.MenuLabel('UI/Inflight/OverloadRack'), self.OverloadRack, ()))
                m.append((uiutil.MenuLabel('UI/Inflight/StopOverloadingRack'), self.StopOverloadRack, ()))

        moduleDamage = self.GetModuleDamage()
        if moduleDamage:
            if self.isBeingRepaired:
                m.append((uiutil.MenuLabel('UI/Inflight/menuCancelRepair'), self.CancelRepair, ()))
            else:
                m.append((uiutil.MenuLabel('UI/Commands/Repair'), self.RepairModule, ()))
        if slaves:
            m.append((uiutil.MenuLabel('UI/Fitting/ClearGroup'), self.UnlinkModule, ()))
        m += [(uiutil.MenuLabel('UI/Commands/ShowInfo'), sm.GetService('info').ShowInfo, (self.sr.moduleInfo.typeID,
           self.sr.moduleInfo.itemID,
           0,
           self.sr.moduleInfo))]
        return m

    def RepairModule(self):
        success = self.stateManager.RepairModule(self.sr.moduleInfo.itemID)
        if self.slaves:
            for slave in self.slaves:
                success = self.stateManager.RepairModule(slave) or success

        if success == True:
            self.isBeingRepaired = True
            self.SetRepairing()

    def CancelRepair(self):
        sm.GetService('godma').GetStateManager().StopRepairModule(self.sr.moduleInfo.itemID)

    def OnFailLockTarget(self, tid, *args):
        self.waitingForActiveTarget = 0

    def OnModuleRepaired(self, itemID):
        if itemID == self.sr.moduleInfo.itemID:
            self.RemoveRepairing()
            self.isBeingRepaired = False

    def OnAmmoInBankChanged(self, masterID):
        slaves = self.dogmaLocation.GetSlaveModules(masterID, session.shipid)
        if self.sr.moduleInfo.itemID in slaves:
            self.SetCharge(self.sr.moduleInfo)

    def OnChargeBeingLoadedToModule(self, itemIDs, chargeTypeID, time):
        if self.sr.moduleInfo.itemID not in itemIDs:
            return
        chargeGroupID = self.stateManager.GetType(chargeTypeID).groupID
        eve.Message('LauncherLoadDelay', {'ammoGroupName': (GROUPID, chargeGroupID),
         'launcherGroupName': (GROUPID, self.sr.moduleInfo.groupID),
         'time': time / 1000})
        self.BlinkIcon(time)

    def UnlinkModule(self):
        self.dogmaLocation.DestroyWeaponBank(session.shipid, self.sr.moduleInfo.itemID)

    def Overload(self, onoff, eff):
        if onoff:
            eff.Activate()
        else:
            eff.Deactivate()

    def OverloadRack(self):
        sm.GetService('godma').OverloadRack(self.sr.moduleInfo.itemID)

    def StopOverloadRack(self):
        sm.GetService('godma').StopOverloadRack(self.sr.moduleInfo.itemID)

    def GetChargeReloadInfo(self, ignoreCharge = 0):
        moduleType = cfg.invtypes.Get(self.sr.moduleInfo.typeID)
        lastChargeTypeID = self.stateManager.GetAmmoTypeForModule(self.sr.moduleInfo.itemID)
        if self.charge and not ignoreCharge:
            chargeTypeID = self.charge.typeID
            chargeQuantity = self.charge.stacksize
        elif lastChargeTypeID is not None:
            chargeTypeID = lastChargeTypeID
            chargeQuantity = 0
        else:
            chargeTypeID = None
            chargeQuantity = 0
        if chargeTypeID is not None:
            roomForReload = int(moduleType.capacity / cfg.invtypes.Get(chargeTypeID).volume - chargeQuantity + 1e-07)
        else:
            roomForReload = 0
        return (chargeTypeID, chargeQuantity, roomForReload)

    def SetAutoReload(self, on):
        settings.char.autoreload.Set(self.sr.moduleInfo.itemID, on)
        self.autoreload = on
        self.AutoReload()

    def AutoReload(self, force = 0, useItemID = None, useQuant = None):
        if self.reloadingAmmo is not False:
            return
        if not cfg.IsChargeCompatible(self.sr.moduleInfo) or not (self.autoreload or force):
            return
        chargeTypeID, chargeQuantity, roomForReload = self.GetChargeReloadInfo()
        if chargeQuantity > 0 and not force or roomForReload <= 0:
            return
        shiplayer = uicore.layer.shipui
        if not shiplayer:
            return
        self.dogmaLocation.LoadChargeToModule(self.sr.moduleInfo.itemID, chargeTypeID)
        uthread.new(self.CheckPending)

    def OnItemChange(self, item, change):
        if not self or self.destroyed or not getattr(self, 'sr', None):
            return
        if const.ixQuantity not in change:
            return
        if self.reloadingAmmo == item.itemID and not sm.GetService('invCache').IsItemLocked(self, item.itemID):
            shiplayer = uicore.layer.shipui
            reloadsByID = shiplayer.sr.reloadsByID
            self.reloadingAmmo = True
            if reloadsByID[item.itemID].balance:
                reloadsByID[item.itemID].send(None)
            else:
                del reloadsByID[item.itemID]

    def CheckPending(self):
        shiplayer = uicore.layer.shipui
        if not shiplayer:
            return
        blue.pyos.synchro.SleepSim(1000)
        if shiplayer and shiplayer:
            shiplayer.CheckPendingReloads()

    def CheckOverload(self):
        if not self or self.destroyed:
            return
        isActive = False
        hasOverloadEffect = False
        if not util.HasAttrs(self, 'sr', 'moduleInfo', 'effects'):
            return
        for key in self.sr.moduleInfo.effects.iterkeys():
            effect = self.sr.moduleInfo.effects[key]
            if effect.effectCategory == const.dgmEffOverload:
                if effect.isActive:
                    isActive = True
                hasOverloadEffect = True

        if hasOverloadEffect:
            self.sr.overloadButton.top = 5
            if self.online:
                if isActive:
                    self.sr.overloadButton.LoadTexture('res:/UI/Texture/classes/ShipUI/slotOverloadOn.png')
                else:
                    self.sr.overloadButton.LoadTexture('res:/UI/Texture/classes/ShipUI/slotOverloadOff.png')
                self.sr.overloadButton.state = uiconst.UI_NORMAL
            else:
                self.sr.overloadButton.LoadTexture('res:/UI/Texture/classes/ShipUI/slotOverloadDisabled.png')
                self.sr.overloadButton.state = uiconst.UI_DISABLED
        else:
            self.sr.overloadButton.top = 6
            self.sr.overloadButton.LoadTexture('res:/UI/Texture/classes/ShipUI/slotOverloadDisabled.png')
            self.sr.overloadButton.state = uiconst.UI_DISABLED

    def CheckMasterSlave(self):
        if not self or self.destroyed:
            return
        itemID = self.sr.moduleInfo.itemID
        slaves = self.dogmaLocation.GetSlaveModules(itemID, session.shipid)
        if slaves:
            if self.sr.stackParent is None:
                stackParent = uicls.Container(parent=self, name='stackParent', pos=(6, 27, 12, 10), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0)
                self.sr.stacklabel = uicls.Label(text=len(slaves) + 1, parent=stackParent, fontsize=9, letterspace=1, left=5, top=0, width=30, state=uiconst.UI_DISABLED, shadowOffset=(0, 0), color=(1.0, 1.0, 1.0, 1))
                underlay = uicls.Sprite(parent=stackParent, name='underlay', pos=(0, 0, 0, 0), align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/slotStackUnderlay.png', color=(0.51, 0.0, 0.0, 1.0))
                self.sr.stackParent = stackParent
            else:
                self.sr.stackParent.state = uiconst.UI_DISABLED
                self.sr.stacklabel.text = len(slaves) + 1
        elif self.sr.stackParent:
            self.sr.stackParent.state = uiconst.UI_HIDDEN

    def CheckOnline(self, sound = 0):
        if not self or self.destroyed:
            return
        if not util.HasAttrs(self, 'sr', 'moduleInfo', 'effects'):
            return
        for key in self.sr.moduleInfo.effects.keys():
            effect = self.sr.moduleInfo.effects[key]
            if effect.effectName == 'online':
                if effect.isActive:
                    self.ShowOnline()
                    if sound:
                        eve.Message('OnLogin')
                else:
                    self.ShowOffline()
                return

    def ChangeOnline(self, on = 1):
        uthread.new(self._ChangeOnline, on)

    def _ChangeOnline(self, on):
        masterID = self.dogmaLocation.IsInWeaponBank(session.shipid, self.sr.moduleInfo.itemID)
        if masterID:
            if not on:
                ret = eve.Message('CustomQuestion', {'header': 'OFFLINE',
                 'question': "When offlining this module you will destroy the weapons bank it's in. Are you sure you want to offline it? "}, uiconst.YESNO)
                if ret != uiconst.ID_YES:
                    return
        elif not on and eve.Message('PutOffline', {}, uiconst.YESNO) != uiconst.ID_YES:
            return
        for key in self.sr.moduleInfo.effects.keys():
            effect = self.sr.moduleInfo.effects[key]
            if effect.effectName == 'online':
                if on:
                    effect.Activate()
                else:
                    self.ShowOffline(1)
                    effect.Deactivate()
                return

    def ShowOverload(self, on):
        self.CheckOverload()

    def ShowOnline(self):
        self.isMaster = 0
        if self.AreModulesOffline():
            self.ShowOffline()
            return
        self.online = True
        if self.grey:
            self.icon.SetAlpha(0.1)
        else:
            self.icon.SetAlpha(1.0)
        self.CheckOverload()

    def ShowOffline(self, ping = 0):
        self.online = False
        if self.grey:
            self.icon.SetAlpha(0.1)
        else:
            self.icon.SetAlpha(0.25)
        if ping:
            eve.Message('OnLogin')
        self.CheckOverload()
        self.isInActiveState = True

    def AreModulesOffline(self):
        slaves = self.dogmaLocation.GetSlaveModules(self.sr.moduleInfo.itemID, session.shipid)
        if not slaves:
            return False
        self.isMaster = 1
        onlineEffect = self.stateManager.GetEffect(self.sr.moduleInfo.itemID, 'online')
        if onlineEffect is None or not onlineEffect.isActive:
            return True
        for slave in slaves:
            onlineEffect = self.stateManager.GetEffect(slave, 'online')
            if onlineEffect is None or not onlineEffect.isActive:
                return True

        return False

    def IsEffectRepeatable(self, effect, activatibleKnown = 0):
        if activatibleKnown or self.IsEffectActivatible(effect):
            if not effect.item.disallowRepeatingActivation:
                return effect.durationAttributeID is not None
        return 0

    def IsEffectActivatible(self, effect):
        return effect.isDefault and effect.effectName != 'online' and effect.effectCategory in (const.dgmEffActivation, const.dgmEffTarget)

    def SetRepeat(self, num):
        settings.char.autorepeat.Set(self.sr.moduleInfo.itemID, num)
        self.autorepeat = num

    def GetDefaultEffect(self):
        if not self or self.destroyed:
            return
        if self.sr is None or self.sr.moduleInfo is None or not self.stateManager.IsItemLoaded(self.sr.moduleInfo.itemID):
            return
        for key in self.sr.moduleInfo.effects.iterkeys():
            effect = self.sr.moduleInfo.effects[key]
            if self.IsEffectActivatible(effect):
                return effect

    def OnClick(self, *args):
        if not self or self.IsBeingDragged() or not self.isInActiveState:
            return
        sm.GetService('audio').SendUIEvent('wise:/msg_click_play')
        if uicore.uilib.Key(uiconst.VK_SHIFT):
            self.ToggleOverload()
            return
        ctrlRepeat = 0
        if uicore.uilib.Key(uiconst.VK_CONTROL):
            ctrlRepeat = 1000
        self.Click(ctrlRepeat)

    def Click(self, ctrlRepeat = 0):
        if self.waitingForActiveTarget:
            sm.GetService('target').CancelTargetOrder(self)
            self.waitingForActiveTarget = 0
        elif self.def_effect is None:
            log.LogWarn('No default Effect available for this moduletypeID:', self.sr.moduleInfo.typeID)
            eve.Message('CustomNotify', {'notify': localization.GetByLabel('UI/Inflight/ModuleRacks/TryingToActivatePassiveModule')})
        elif not self.online:
            if getattr(self, 'isMaster', None):
                eve.Message('ClickOffllineGroup')
            else:
                eve.Message('ClickOffllineModule')
        elif self.def_effect.isActive:
            self.DeactivateEffect(self.def_effect)
        elif not self.effect_activating:
            self.activationTimer = base.AutoTimer(500, self.ActivateEffectTimer)
            self.effect_activating = 1
            self.ActivateEffect(self.def_effect, ctrlRepeat=ctrlRepeat)

    def ActivateEffectTimer(self, *args):
        self.effect_activating = 0
        self.activationTimer = None

    def OnEndDrag(self, *args):
        uthread.new(uicore.layer.shipui.ResetSwapMode)

    def GetDragData(self, *args):
        if settings.user.ui.Get('lockModules', 0):
            return []
        if self.charge:
            fakeNode = uix.GetItemData(self.charge, 'icons')
            fakeNode.isCharge = 1
        else:
            fakeNode = uix.GetItemData(self.sr.moduleInfo, 'icons')
            fakeNode.isCharge = 0
        fakeNode.__guid__ = 'xtriui.ShipUIModule'
        fakeNode.slotFlag = self.sr.moduleInfo.flagID
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        uicore.layer.shipui.StartDragMode(self.sr.moduleInfo.itemID, self.sr.moduleInfo.typeID)
        return [fakeNode]

    def OnDropData(self, dragObj, nodes):
        log.LogInfo('Module.OnDropData', self.id)
        flag1 = self.sr.moduleInfo.flagID
        flag2 = None
        for node in nodes:
            if node.Get('__guid__', None) == 'xtriui.ShipUIModule':
                flag2 = node.slotFlag
                break

        if flag1 == flag2:
            return
        if flag2 is not None:
            uicore.layer.shipui.ChangeSlots(flag1, flag2)
            return
        multiLoadCharges = True
        chargeTypeID = None
        chargeItems = []
        for node in nodes:
            if not hasattr(node, 'rec'):
                return
            chargeItem = node.rec
            if not hasattr(chargeItem, 'categoryID'):
                return
            if chargeItem.categoryID != const.categoryCharge:
                continue
            if chargeTypeID is None:
                chargeTypeID = chargeItem.typeID
            if chargeItem.typeID == chargeTypeID:
                chargeItems.append(chargeItem)

        if len(chargeItems) > 0:
            self.dogmaLocation.DropLoadChargeToModule(self.sr.moduleInfo.itemID, chargeTypeID, chargeItems=chargeItems)

    def OnMouseHover(self, *args):
        if uicore.uilib.Key(uiconst.VK_SHIFT):
            self.OverloadHiliteOn()
        else:
            self.OverloadHiliteOff()

    def OnMouseDown(self, *args):
        uicls.Container.OnMouseDown(self, *args)
        log.LogInfo('Module.OnMouseDown', self.id)
        if getattr(self, 'downTop', None) is not None or not self.isInActiveState or self.def_effect is None:
            return
        self.downTop = self.parent.top
        self.parent.top += 2

    def OnMouseUp(self, *args):
        self.moduleHintTimer = None
        uicls.Container.OnMouseUp(self, *args)
        if not self or self.destroyed:
            return
        log.LogInfo('Module.OnMouseUp', self.id)
        if getattr(self, 'downTop', None) is not None:
            self.parent.top = self.downTop
            self.downTop = None
        if len(args) > 0 and args[0] == uiconst.MOUSERIGHT and getattr(uicore.layer.hint, 'moduleButtonHint', None):
            uicore.layer.hint.moduleButtonHint.FadeOpacity(0.0)

    def OnMouseEnter(self, *args):
        uthread.pool('ShipMobuleButton::MouseEnter', self.MouseEnter)

    def MouseEnter(self, *args):
        if self.destroyed or sm.GetService('godma').GetItem(self.sr.moduleInfo.itemID) is None:
            return
        if uicore.uilib.Key(uiconst.VK_SHIFT):
            self.OverloadHiliteOn()
        self.SetHilite()
        tacticalSvc = sm.GetService('tactical')
        bracketMgr = sm.GetService('bracket')
        maxRange, falloffDist, bombRadius = tacticalSvc.FindMaxRange(self.sr.moduleInfo, self.charge)
        if maxRange > 0:
            bracketMgr.ShowModuleRange(self.sr.moduleInfo.itemID, maxRange + falloffDist)
            bracketMgr.ShowHairlinesForModule(self.sr.moduleInfo.itemID)
        log.LogInfo('Module.OnMouseEnter', self.id)
        eve.Message('NeocomButtonEnter')
        if settings.user.ui.Get('showModuleTooltips', 1):
            self.moduleHintTimer = base.AutoTimer(MODULEHINTDELAY, self.ShowHint)
        uthread.pool('ShipMobuleButton::OnMouseEnter-->UpdateTargetingRanges', tacticalSvc.UpdateTargetingRanges, self.sr.moduleInfo, self.charge)

    def ShowHint(self, *args):
        self.moduleHintTimer = None
        if len(uicore.layer.menu.children) > 0:
            return
        self.shouldUpdate = True
        self.updateTimer = base.AutoTimer(1000, self.UpdateInfo_TimedCall)
        if getattr(uicore.layer.hint, 'moduleButtonHint', None) is None or uicore.layer.hint.moduleButtonHint.destroyed:
            moduleButtonHint = uicls.ModuleButtonHint(parent=uicore.layer.hint, name='moduleButtonHint', align=uiconst.TOPLEFT, pos=(0,
             0,
             MAXMODULEHINTWIDTH,
             200))
            moduleButtonHint.opacity = 0.0
            uicore.layer.hint.moduleButtonHint = moduleButtonHint
        wasUpdated = self.UpdateInfo()
        if wasUpdated:
            uicore.layer.hint.moduleButtonHint.PositionHint(left=self.absoluteLeft, top=self.absoluteTop, bottom=self.absoluteBottom)
            uicore.layer.hint.moduleButtonHint.FadeOpacity(1.0)

    def OnMouseExit(self, *args):
        self.shouldUpdate = False
        if getattr(uicore.layer.hint, 'moduleButtonHint', None) is not None:
            uicore.layer.hint.moduleButtonHint.FadeOpacity(0.0)
        self.RemoveHilite()
        sm.GetService('bracket').StopShowingModuleRange(self.sr.moduleInfo.itemID)
        self.OverloadHiliteOff()
        log.LogInfo('Module.OnMouseExit', self.id)
        self.moduleHintTimer = None
        self.updateTimer = None
        self.OnMouseUp(None)

    def OnMouseMove(self, *args):
        uicls.Container.OnMouseMove(self, *args)
        if getattr(self, 'shouldUpdate', False):
            uthread.pool('ShipModuleButton::MouseMove', self.UpdateInfo)

    def UpdateInfo_TimedCall(self):
        self.UpdateInfo()

    def UpdateInfo(self):
        if not self or self.destroyed:
            return False
        if not self.stateManager.IsItemLoaded(self.id):
            return False
        if not getattr(self, 'shouldUpdate', False):
            return False
        self.sr.hint = ''
        if getattr(uicore.layer.hint, 'moduleButtonHint', None) is None or uicore.layer.hint.moduleButtonHint.destroyed:
            moduleButtonHint = uicls.ModuleButtonHint(parent=uicore.layer.hint, name='moduleButtonHint', align=uiconst.TOPLEFT, pos=(0,
             0,
             MAXMODULEHINTWIDTH,
             200))
            moduleButtonHint.opacity = 0.0
            positionTuple = (self.absoluteLeft, self.absoluteTop, self.absoluteBottom)
            uicore.layer.hint.moduleButtonHint = moduleButtonHint
        else:
            positionTuple = None
        chargeItemID = None
        if self.charge:
            chargeItemID = self.charge.itemID
        uicore.layer.hint.moduleButtonHint.UpdateAllInfo(self.sr.moduleInfo.itemID, chargeItemID, positionTuple=positionTuple)
        requiredSafetyLevel = self.GetRequiredSafetyLevel()
        if self.crimewatchSvc.CheckUnsafe(requiredSafetyLevel):
            uicore.layer.hint.moduleButtonHint.SetSafetyWarning(requiredSafetyLevel)
        else:
            uicore.layer.hint.moduleButtonHint.RemoveSafetyWarning()
        return True

    def GetModuleDamage(self):
        return uicore.layer.shipui.GetModuleGroupDamage(self.sr.moduleInfo.itemID)

    def GetAccuracy(self, targetID = None):
        if self is None or self.destroyed:
            return

    def SetActive(self):
        self.InitGlow()
        self.sr.glow.state = uiconst.UI_DISABLED
        sm.GetService('ui').BlinkSpriteA(self.sr.glow, 0.75, 1000, None, passColor=0)
        self.effect_activating = 0
        self.activationTimer = None
        self.isInActiveState = True
        self.ActivateRamps()

    def SetDeactivating(self):
        self.isDeactivating = True
        if self.sr.glow:
            self.sr.glow.state = uiconst.UI_HIDDEN
        self.InitBusyState()
        self.sr.busy.state = uiconst.UI_DISABLED
        sm.GetService('ui').BlinkSpriteA(self.sr.busy, 0.75, 1000, None, passColor=0)
        self.isInActiveState = False
        self.DeActivateRamps()

    def SetIdle(self):
        self.isDeactivating = False
        if self.sr.glow:
            self.sr.glow.state = uiconst.UI_HIDDEN
            sm.GetService('ui').StopBlink(self.sr.glow)
        if self.sr.busy:
            self.sr.busy.state = uiconst.UI_HIDDEN
            sm.GetService('ui').StopBlink(self.sr.busy)
        self.isInActiveState = True
        self.IdleRamps()

    def SetRepairing(self):
        self.InitGlow()
        self.sr.glow.state = uiconst.UI_DISABLED
        self.sr.glow.SetRGB(1, 1, 1, 1)
        sm.GetService('ui').BlinkSpriteA(self.sr.glow, 0.9, 2500, None, passColor=0)
        self.isInActiveState = True

    def RemoveRepairing(self):
        if self.sr.glow:
            sm.GetService('ui').StopBlink(self.sr.glow)
            self.sr.glow.SetRGB(*GLOWCOLOR)
            self.sr.glow.state = uiconst.UI_HIDDEN

    def SetHilite(self):
        self.InitHilite()
        self.sr.hilite.display = True
        requiredSafetyLevel = self.GetRequiredSafetyLevel()
        if self.crimewatchSvc.CheckUnsafe(requiredSafetyLevel):
            self.InitSafetyGlow()
            if requiredSafetyLevel == const.shipSafetyLevelNone:
                color = crimewatchConst.Colors.Criminal
            else:
                color = crimewatchConst.Colors.Suspect
            self.sr.safetyGlow.color.SetRGBA(*color.GetRGBA())
            self.sr.safetyGlow.display = True

    def GetRequiredSafetyLevel(self):
        requiredSafetyLevel = self.crimewatchSvc.GetRequiredSafetyLevelForEffect(self.GetRelevantEffect(), targetID=None)
        return requiredSafetyLevel

    def RemoveHilite(self):
        if self.sr.hilite:
            self.sr.hilite.display = False
        if self.sr.safetyGlow:
            self.sr.safetyGlow.display = False

    def InitSafetyGlow(self):
        if self.sr.safetyGlow is None:
            self.sr.safetyGlow = uicls.Sprite(parent=self.parent, name='safetyGlow', padding=2, align=uiconst.TOALL, state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/classes/ShipUI/slotGlow.png', color=crimewatchConst.Colors.Yellow.GetRGBA())

    def InitGlow(self):
        if self.sr.glow is None:
            self.sr.glow = uicls.Sprite(parent=self.parent, name='glow', padding=2, align=uiconst.TOALL, state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/classes/ShipUI/slotGlow.png', color=GLOWCOLOR)

    def InitBusyState(self):
        if self.sr.busy is None:
            self.sr.busy = uicls.Sprite(parent=self.parent, name='busy', padding=2, align=uiconst.TOALL, state=uiconst.UI_HIDDEN, texturePath='res:/UI/Texture/classes/ShipUI/slotGlow.png', color=BUSYCOLOR)

    def InitHilite(self):
        if self.sr.hilite is None:
            if getattr(self.parent, 'mainShape', None) is not None:
                idx = max(-1, uiutil.GetIndex(self.parent.mainShape) - 1)
            else:
                idx = -1
            self.sr.hilite = uicls.Sprite(parent=self.parent, name='hilite', padding=(10, 10, 10, 10), align=uiconst.TOALL, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/slotHilite.png', blendMode=trinity.TR2_SBM_ADDX2, idx=idx)
            self.sr.hilite.display = False

    def OverloadHiliteOn(self):
        self.sr.overloadButton.SetAlpha(1.5)

    def OverloadHiliteOff(self):
        self.sr.overloadButton.SetAlpha(1.0)

    def GetEffectByName(self, effectName):
        for key in self.sr.moduleInfo.effects.iterkeys():
            effect = self.sr.moduleInfo.effects[key]
            if effect.effectName == effectName:
                return effect

    def Update(self, effectState):
        if not self or self.destroyed:
            return
        if not self.stateManager.IsItemLoaded(self.id):
            return
        if self.def_effect and effectState.effectName == self.def_effect.effectName:
            if effectState.start:
                self.SetActive()
            else:
                self.SetIdle()
        effect = self.GetEffectByName(effectState.effectName)
        if effect and effect.effectCategory == const.dgmEffOverload:
            self.ShowOverload(effect.isActive)
        if effectState.effectName == 'online':
            if effectState.active:
                self.ShowOnline()
            else:
                self.ShowOffline()
        if effect.effectCategory in [const.dgmEffTarget, const.dgmEffActivation, const.dgmEffArea] and effect.effectID != const.effectOnline:
            if not effectState.active and self.quantity == 0:
                self.AutoReload()
        self.UpdateInfo()

    def GetRelevantEffect(self):
        if self.def_effect and (self.def_effect.effectName == 'useMissiles' or self.def_effect.effectName == 'warpDisruptSphere' and self.charge is not None):
            if self.charge is None:
                return
            effect = sm.GetService('godma').GetStateManager().GetDefaultEffect(self.charge.typeID)
        else:
            effect = self.def_effect
        return effect

    def ActivateEffect(self, effect, targetID = None, ctrlRepeat = 0):
        if self.charge and self.charge.typeID in const.orbitalStrikeAmmo:
            return sm.GetService('district').ActivateModule(self.sr.moduleInfo.itemID)
        relevantEffect = self.GetRelevantEffect()
        if relevantEffect is None:
            return
        if relevantEffect and not targetID and relevantEffect.effectCategory == 2:
            targetID = sm.GetService('target').GetActiveTargetID()
            if not targetID:
                sm.GetService('target').OrderTarget(self)
                uthread.new(self.BlinkIcon)
                self.waitingForActiveTarget = 1
                return
        if self.sr.Get('moduleinfo'):
            for key in self.sr.moduleInfo.effects.iterkeys():
                checkeffect = self.sr.moduleInfo.effects[key]
                if checkeffect.effectName == 'online':
                    if not checkeffect.isActive:
                        self._ChangeOnline(1)
                    break

        if self.def_effect:
            if relevantEffect.isOffensive:
                if not sm.GetService('consider').DoAttackConfirmations(targetID, relevantEffect):
                    return
            repeats = ctrlRepeat or self.autorepeat
            if not self.IsEffectRepeatable(self.def_effect, 1):
                repeats = 0
            if not self.charge:
                self.stateManager.ChangeAmmoTypeForModule(self.sr.moduleInfo.itemID, None)
            self.def_effect.Activate(targetID, repeats)

    def DeactivateEffect(self, effect):
        self.SetDeactivating()
        try:
            effect.Deactivate()
        except UserError as e:
            if e.msg == 'EffectStillActive':
                if not self.isPendingUnlockForDeactivate:
                    self.isPendingUnlockForDeactivate = True
                    uthread.new(self.DelayButtonUnlockForDeactivate, max(0, e.dict['timeLeft']))
            raise 

    def DelayButtonUnlockForDeactivate(self, sleepTimeBlue):
        blue.pyos.synchro.SleepSim(sleepTimeBlue / const.MSEC)
        self.isInActiveState = True
        self.isPendingUnlockForDeactivate = False

    def OnStateChange(self, itemID, flag, isTrue, *args):
        if self and isTrue and flag == state.activeTarget and self.waitingForActiveTarget:
            self.waitingForActiveTarget = 0
            self.ActivateEffect(self.def_effect, itemID)
            sm.GetService('target').CancelTargetOrder(self)

    def GetModuleType(self):
        return (self.sr.moduleInfo.typeID, self.sr.moduleInfo.itemID)

    def ActivateRamps(self):
        if not self or self.destroyed:
            return
        if self.ramp_active:
            self.UpdateRamps()
            return
        self.DoActivateRamps()

    def DeActivateRamps(self):
        self.UpdateRamps()

    def IdleRamps(self):
        self.ramp_active = False
        shiplayer = uicore.layer.shipui
        if not shiplayer:
            return
        moduleID = self.sr.moduleInfo.itemID
        rampTimers = shiplayer.sr.rampTimers
        if rampTimers.has_key(moduleID):
            del rampTimers[moduleID]
        if self.sr.ramps:
            self.sr.ramps.state = uiconst.UI_HIDDEN

    def UpdateRamps(self):
        self.DoActivateRamps()

    def DoActivateRamps(self):
        if self.ramp_active:
            return
        uthread.new(self.DoActivateRampsThread)

    def InitRamps(self):
        if self.sr.ramps:
            return
        ramps = uicls.Container(parent=self.parent, name='ramps', pos=(0, 0, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_HIDDEN, opacity=0.85, idx=OVERLOADBTN_INDEX + 1)
        self.sr.ramps = ramps
        leftRampCont = uicls.Container(parent=ramps, name='leftRampCont', pos=(0, 0, 32, 64), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, clipChildren=True)
        leftRamp = uicls.Transform(parent=leftRampCont, name='leftRamp', pos=(0, 0, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        rampLeftSprite = uicls.Sprite(parent=leftRamp, name='rampLeftSprite', pos=(0, 0, 32, 64), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/slotRampLeft.png')
        leftShadowRamp = uicls.Transform(parent=leftRampCont, name='leftShadowRamp', pos=(0, 1, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_HIDDEN)
        rampSprite = uicls.Sprite(parent=leftShadowRamp, name='rampSprite', pos=(0, 0, 32, 64), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/slotRampLeft.png', color=(0.0, 0.0, 0.0, 1.0))
        rightRampCont = uicls.Container(parent=ramps, name='rightRampCont', pos=(32, 0, 32, 64), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, clipChildren=True)
        rightRamp = uicls.Transform(parent=rightRampCont, name='rightRamp', pos=(-32, 0, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        rampRightSprite = uicls.Sprite(parent=rightRamp, name='rampRightSprite', pos=(32, 0, 32, 64), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/slotRampRight.png')
        rightShadowRamp = uicls.Transform(parent=rightRampCont, name='rightShadowRamp', pos=(-32, 1, 64, 64), align=uiconst.TOPLEFT, state=uiconst.UI_HIDDEN)
        rampSprite = uicls.Sprite(parent=rightShadowRamp, name='rampSprite', pos=(32, 0, 32, 64), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/ShipUI/slotRampRight.png', color=(0.0, 0.0, 0.0, 1.0))
        self.sr.leftRamp = leftRamp
        self.sr.leftShadowRamp = leftShadowRamp
        self.sr.rightRamp = rightRamp
        self.sr.rightShadowRamp = rightShadowRamp

    def DoActivateRampsThread(self):
        if not self or self.destroyed:
            return
        (firstActivation, startTime), durationInMilliseconds = self.GetEffectTiming()
        if durationInMilliseconds <= 0:
            return
        now = blue.os.GetSimTime()
        if firstActivation:
            startTimeAdjustment = now - startTime
            if startTimeAdjustment > const.SEC:
                startTimeAdjustment = 0
            correctionTimeMS = durationInMilliseconds / 2
            adjustmentDecayPerSec = float(-startTimeAdjustment) / (correctionTimeMS / 1000)
        else:
            startTimeAdjustment = 0
            correctionTimeMS = 0
        self.ramp_active = True
        self.InitRamps()
        self.sr.ramps.state = uiconst.UI_DISABLED
        while self and not self.destroyed and self.ramp_active:
            newNow = blue.os.GetSimTime()
            deltaTime = newNow - now
            now = newNow
            if correctionTimeMS != 0:
                deltaMS = min(deltaTime / const.MSEC, correctionTimeMS)
                startTimeAdjustment += long(adjustmentDecayPerSec * (float(deltaMS) / 1000))
                correctionTimeMS -= deltaMS
            else:
                startTimeAdjustment = 0
            portionDone = blue.os.TimeDiffInMs(startTime + startTimeAdjustment, now) / durationInMilliseconds
            if portionDone > 1:
                iterations = int(portionDone)
                startTime += long(durationInMilliseconds * iterations * const.MSEC)
                _, durationInMilliseconds = self.GetEffectTiming()
                try:
                    uicore.layer.shipui.sr.rampTimers[self.sr.moduleInfo.itemID] = (False, startTime)
                except AttributeError:
                    pass

                portionDone -= iterations
                if self.InLimboState():
                    self.IdleRamps()
                    break
            rampUpVal = min(1.0, max(0.0, portionDone * 2))
            rampDownVal = min(1.0, max(0.0, portionDone * 2 - 1.0))
            self.SetRampUpValue(rampUpVal)
            self.SetRampDownValue(rampDownVal)
            blue.pyos.synchro.Yield()

    def InLimboState(self):
        for each in ['waitingForActiveTarget',
         'changingAmmo',
         'reloadingAmmo',
         'isDeactivating']:
            if getattr(self, each, False):
                return True

        return False

    def GetRampStartTime(self):
        shiplayer = uicore.layer.shipui
        if not shiplayer:
            return
        moduleID = self.sr.moduleInfo.itemID
        rampTimers = shiplayer.sr.rampTimers
        if moduleID not in rampTimers:
            now = blue.os.GetSimTime()
            default = getattr(self.def_effect, 'startTime', now) or now
            rampTimers[moduleID] = (True, default)
        return rampTimers[moduleID]

    def GetEffectTiming(self):
        rampStartTime = self.GetRampStartTime()
        durationInMilliseconds = 0.0
        attr = cfg.dgmattribs.GetIfExists(getattr(self.def_effect, 'durationAttributeID', None))
        item = self.stateManager.GetItem(self.def_effect.itemID)
        if item is None:
            return (0, 0.0)
        if attr:
            durationInMilliseconds = self.stateManager.GetAttribute(self.def_effect.itemID, attr.attributeName)
        if not durationInMilliseconds:
            durationInMilliseconds = getattr(self.def_effect, 'duration', 0.0)
        return (rampStartTime, durationInMilliseconds)

    def SetRampUpValue(self, value):
        self.sr.leftRamp.SetRotation(math.pi - math.pi * value)
        self.sr.leftShadowRamp.SetRotation(math.pi - math.pi * value)

    def SetRampDownValue(self, value):
        self.sr.rightRamp.SetRotation(math.pi - math.pi * value)
        self.sr.rightShadowRamp.SetRotation(math.pi - math.pi * value)
        if value == 1.0:
            self.sr.rightRamp.SetRotation(math.pi)
            self.sr.rightShadowRamp.SetRotation(math.pi)
            self.sr.leftRamp.SetRotation(math.pi)
            self.sr.leftShadowRamp.SetRotation(math.pi)


class ModuleButtonHint(uicls.ContainerAutoSize):
    __guid__ = 'uicls.ModuleButtonHint'
    default_state = uiconst.UI_DISABLED
    infoFunctionNames = {const.groupMiningLaser: 'AddMiningLaserInfo',
     const.groupStripMiner: 'AddMiningLaserInfo',
     const.groupFrequencyMiningLaser: 'AddMiningLaserInfo',
     const.groupEnergyVampire: 'AddEnergyVampireInfo',
     const.groupEnergyDestabilizer: 'AddEnergyDestabilizerInfo',
     const.groupArmorRepairUnit: 'AddArmorRepairersInfo',
     const.groupHullRepairUnit: 'AddHullRepairersInfo',
     const.groupShieldBooster: 'AddShieldBoosterInfo',
     const.groupTrackingComputer: 'AddTrackingComputerInfo',
     const.groupTrackingLink: 'AddTrackingComputerInfo',
     const.groupSmartBomb: 'AddSmartBombInfo',
     const.groupAfterBurner: 'AddPropulsionModuleInfo',
     const.groupStatisWeb: 'AddStasisWebInfo',
     const.groupWarpScrambler: 'AddWarpScramblerInfo',
     const.groupCapacitorBooster: 'AddCapacitorBoosterInfo',
     const.groupEnergyTransferArray: 'AddEnergyTransferArrayInfo',
     const.groupShieldTransporter: 'AddShieldTransporterInfo',
     const.groupArmorRepairProjector: 'AddArmorRepairProjectorInfo',
     const.groupRemoteHullRepairer: 'AddRemoteHullRepairInfo',
     const.groupArmorHardener: 'AddArmorHardenerInfo',
     const.groupShieldHardener: 'AddArmorHardenerInfo',
     const.groupArmorPlatingEnergized: 'AddArmorHardenerInfo',
     const.groupElectronicCounterMeasureBurst: 'AddECMInfo',
     const.groupElectronicCounterMeasures: 'AddECMInfo',
     const.groupElectronicCounterCounterMeasures: 'AddECCMInfo',
     const.groupProjectedElectronicCounterCounterMeasures: 'AddECCMInfo',
     const.groupRemoteSensorDamper: 'AddSensorDamperInfo',
     const.groupRemoteSensorBooster: 'AddSensorDamperInfo',
     const.groupSensorBooster: 'AddSensorDamperInfo',
     const.groupTargetBreaker: 'AddTargetBreakerInfo',
     const.groupTargetPainter: 'AddTargetPainterInfo',
     const.groupTrackingDisruptor: 'AddTrackingDisruptorInfo',
     const.groupCloakingDevice: 'AddCloakingDeviceInfo',
     const.groupTractorBeam: 'AddTractorBeamInfo',
     const.groupDamageControl: 'AddDamageControlInfo',
     const.groupArmorResistanceShiftHardener: 'AddArmorResistanceShiftHardenerInfo',
     const.groupSuperWeapon: 'AddSuperWeaponInfo',
     const.groupGangCoordinator: 'AddGangCoordinatorInfo'}

    def ApplyAttributes(self, attributes):
        self.stateManager = sm.StartService('godma').GetStateManager()
        self.dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
        uicls.ContainerAutoSize.ApplyAttributes(self, attributes)
        self.moduleTypeID = attributes.moduleTypeID
        self.chargeTypeID = attributes.chargeTypeID
        self.clipChildren = 1
        uicls.Frame(bgParent=self, color=(1.0, 1.0, 1.0, 0.1))
        uicls.Fill(bgParent=self, name='hintfill', color=(0, 0, 0, 0.75))
        self.smallContainerHeight = 30
        self.bigContainerHeight = 36
        self.iconeSize = 26
        self.fromWhere = ''
        self.typeCont = uicls.ModuleButtonHintContainerTypeWithShortcut(parent=self, name='typeCont', height=self.smallContainerHeight)
        self.chargeCont = uicls.ModuleButtonHintContainerType(parent=self, name='chargeCont', height=self.smallContainerHeight)
        self.rangeCont = uicls.ModuleButtonHintContainerBase(parent=self, name='rangeCont', height=self.bigContainerHeight, texturePath='res:/UI/Texture/Icons/22_32_15.png')

    def UpdateAllInfo(self, moduleItemID, chargeItemID, positionTuple = None, fromWhere = 'shipModuleButton', *args):
        self.fromWhere = fromWhere
        moduleInfoItem = self.dogmaLocation.GetDogmaItem(moduleItemID)
        if chargeItemID is None:
            chargeInfoItem = None
        else:
            chargeInfoItem = self.dogmaLocation.GetDogmaItem(chargeItemID)
        typeName = cfg.invtypes.Get(moduleInfoItem.typeID).name
        moduleDamageAmount = None
        if fromWhere == 'fitting':
            damage = self.dogmaLocation.GetAccurateAttributeValue(moduleItemID, const.attributeDamage)
        else:
            damage = uicore.layer.shipui.GetModuleGroupDamage(moduleItemID)
        if damage:
            moduleDamageAmount = int(math.ceil(damage / self.dogmaLocation.GetAttributeValue(moduleItemID, const.attributeHp) * 100))
        else:
            moduleDamageAmount = 0.0
        chargesType, chargesQty = self.GetChargeTypeAndQty(moduleInfoItem, chargeInfoItem)
        if self.moduleTypeID != moduleInfoItem.typeID or self.chargeTypeID != chargesType:
            for child in self.children[:]:
                if getattr(child, 'isExtraInfoContainer', False):
                    child.Close()

            self.moduleTypeID = moduleInfoItem.typeID
            self.typeCont.SetTypeIcon(typeID=moduleInfoItem.typeID)
        maxTextWidth = 0
        myShip = util.GetActiveShip()
        if fromWhere == 'fitting':
            numSlaves = 0
        else:
            numSlaves = self.GetNumberOfSlaves(moduleInfoItem.itemID, myShip)
        self.typeCont.SetTypeTextAndDamage(typeName, moduleDamageAmount, numSlaves, bold=True)
        self.typeCont.SetContainerHeight()
        moduleShortcut = self.GetModuleShortCut(moduleInfoItem)
        if moduleShortcut:
            self.typeCont.SetShortcutText(moduleShortcut)
            self.typeCont.shortcutCont.display = True
        else:
            self.HideContainer(self.typeCont.shortcutCont)
            self.typeCont.shortcutPadding = 0
        shortcutPadding = self.typeCont.shortcutPadding
        self.UpdateChargesCont(chargeInfoItem, chargesQty)
        maxRange, falloffDist, bombRadius = sm.GetService('tactical').FindMaxRange(moduleInfoItem, chargeInfoItem)
        self.UpdateRangeCont(moduleInfoItem.typeID, maxRange, falloffDist)
        self.AddGroupOrCategorySpecificInfo(moduleInfoItem.itemID, moduleInfoItem.typeID, chargeInfoItem, chargesQty, numSlaves)
        maxTextWidth = self.FindMaxWidths()
        self.width = min(maxTextWidth + 10, MAXMODULEHINTWIDTH)
        self.typeCont.AddFading(self.width)
        self.chargeCont.AddFading(self.width)
        if positionTuple:
            self.PositionHint(left=positionTuple[0], top=positionTuple[1], bottom=positionTuple[2])

    def SetSafetyWarning(self, safetyLevel):
        safetyCont = getattr(self, 'safetyCont', None)
        if safetyCont is None:
            self.safetyCont = uicls.ModuleButtonHintContainerSafetyLevel(parent=self, name='safetyCont', height=self.smallContainerHeight, texturePath='res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal.png')
            safetyCont = self.safetyCont
        else:
            safetyCont.SetOrder(-1)
        safetyCont.SetSafetyLevelWarning(safetyLevel)
        safetyCont.display = True

    def RemoveSafetyWarning(self):
        if getattr(self, 'safetyCont', None) is not None:
            self.safetyCont.display = False

    def GetNumberOfSlaves(self, itemID, shipID):
        slaves = self.dogmaLocation.GetSlaveModules(itemID, shipID)
        if slaves:
            numSlaves = len(slaves) + 1
        else:
            numSlaves = 0
        return numSlaves

    def GetCrystalDamage(self, chargeInfoItem):
        crystalDamageAmount = None
        if chargeInfoItem is not None:
            dogmaLocation = sm.GetService('clientDogmaIM').GetDogmaLocation()
            crystalDamageAmount = dogmaLocation.GetAccurateAttributeValue(chargeInfoItem.itemID, const.attributeDamage)
        return crystalDamageAmount

    def GetModuleShortCut(self, moduleInfoItem):
        moduleShortcut = None
        masterModuleID = self.dogmaLocation.GetMasterModuleID(util.GetActiveShip(), moduleInfoItem.itemID)
        if masterModuleID is not None:
            masterModuleInfoItem = self.dogmaLocation.GetDogmaItem(masterModuleID)
            flagID = masterModuleInfoItem.flagID
        else:
            flagID = moduleInfoItem.flagID
        slotOrder = uicore.layer.shipui.GetSlotOrder()
        if flagID not in slotOrder:
            return
        pos = slotOrder.index(flagID)
        if pos is not None:
            row = pos / 8
            hiMedLo = ('High', 'Medium', 'Low')[row]
            loc = pos % 8
            slotno = loc + 1
            shortcut = uicore.cmd.GetShortcutStringByFuncName('CmdActivate%sPowerSlot%i' % (hiMedLo, slotno))
            if shortcut:
                moduleShortcut = shortcut
        return moduleShortcut

    def GetChargeTypeAndQty(self, moduleInfoItem, chargeInfoItem):
        chargesQty = None
        chargesType = None
        if self.IsChargeCompatible(moduleInfoItem):
            if chargeInfoItem and chargeInfoItem.typeID:
                chargesQty = self.dogmaLocation.GetQuantity(chargeInfoItem.itemID)
                chargesType = chargeInfoItem.typeID
            else:
                chargesQty = 0
        return (chargesType, chargesQty)

    def IsChargeCompatible(self, moduleInfoItem, *args):
        return moduleInfoItem.groupID in cfg.__chargecompatiblegroups__

    def FindMaxWidths(self, *args):
        maxTextWidth = 0
        for child in self.children:
            maxWidthFunc = getattr(child, 'GetContainerWidth', None)
            if maxWidthFunc is None:
                continue
            maxTextWidth = max(child.GetContainerWidth(), maxTextWidth)

        return maxTextWidth

    def UpdateRangeCont(self, typeID, optimalRange, falloff):
        if optimalRange > 0:
            self.rangeCont.display = True
            rangeText = self.GetOptimalRangeText(typeID, optimalRange, falloff)
            self.rangeCont.textLabel.text = rangeText
            self.rangeCont.SetContainerHeight()
        else:
            self.HideContainer(self.rangeCont)

    def GetOptimalRangeText(self, typeID, optimalRange, falloff, *args):
        rangeText = ''
        if optimalRange > 0:
            formattedOptimalRAnge = util.FmtDist(optimalRange)
            if sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectLauncherFitted):
                rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/MaxRange', maxRange=formattedOptimalRAnge)
            elif sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectTurretFitted):
                if falloff > 1:
                    rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/OptimalRangeAndFalloff', optimalRange=formattedOptimalRAnge, falloffPlusOptimal=util.FmtDist(falloff + optimalRange))
                else:
                    rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/OptimalRange', optimalRange=formattedOptimalRAnge)
            elif cfg.invtypes.Get(typeID).Group().groupID == const.groupSmartBomb:
                rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/AreaOfEffect', range=formattedOptimalRAnge)
            elif falloff > 1:
                rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/RangeWithFalloff', optimalRange=formattedOptimalRAnge, falloffPlusOptimal=util.FmtDist(falloff + optimalRange))
            else:
                rangeText = localization.GetByLabel('UI/Inflight/ModuleRacks/Range', optimalRange=formattedOptimalRAnge)
        return rangeText

    def UpdateChargesCont(self, chargeInfoItem, chargesQty):
        if chargeInfoItem and chargesQty:
            self.chargeCont.display = True
            chargesTypeID = chargeInfoItem.typeID
            if self.chargeTypeID != chargesTypeID:
                self.chargeTypeID = chargesTypeID
                self.chargeCont.SetTypeIcon(typeID=chargesTypeID)
                uix.GetTechLevelIcon(self.chargeCont.techIcon, typeID=chargesTypeID)
            chargeText = self.GetChargeText(chargeInfoItem, chargesQty)
            self.chargeCont.textLabel.text = chargeText
            self.chargeCont.SetContainerHeight()
        else:
            self.chargeTypeID = None
            self.HideContainer(self.chargeCont)

    def GetChargeText(self, chargeInfoItem, chargesQty, *args):
        chargeText = ''
        if chargeInfoItem.groupID in cfg.GetCrystalGroups():
            crystalDamageAmount = self.GetCrystalDamage(chargeInfoItem)
            chargeText = '<b>%s</b>' % cfg.invtypes.Get(chargeInfoItem.typeID).name
            if crystalDamageAmount > 0.0:
                damagedText = localization.GetByLabel('UI/Inflight/ModuleRacks/AmmoDamaged', color='<color=red>', damage=crystalDamageAmount)
                chargeText += '<br>' + damagedText
        else:
            chargeText = localization.GetByLabel('UI/Inflight/ModuleRacks/AmmoNameWithQty', qty=chargesQty, ammoTypeID=chargeInfoItem.typeID)
        return chargeText

    def HideContainer(self, container):
        container.display = False
        container.textLabel.text = ''

    def AddSpecificInfoContainer(self, text, configName, iconID = None, texturePath = None, *args):
        myContainer = getattr(self, configName, None)
        if myContainer is None or myContainer.destroyed:
            myContainer = uicls.ModuleButtonHintContainerBase(parent=self, name=configName, align=uiconst.TOTOP, height=self.bigContainerHeight, texturePath=texturePath, iconID=iconID, isExtraInfoContainer=True)
            setattr(self, configName, myContainer)
        myContainer.textLabel.text = text
        myContainer.SetContainerHeight()

    def AddGroupOrCategorySpecificInfo(self, itemID, typeID, chargeInfoItem, chargesQty, numSlaves, *args):
        group = cfg.invtypes.Get(typeID).Group()
        if chargesQty is None:
            for contName in ('damageTypeContMany', 'damagaTypeContOne', 'dpsCont'):
                cont = getattr(self, contName, None)
                if cont is not None and not cont.destroyed:
                    cont.Close()

        else:
            self.AddDpsAndDamgeTypeInfo(itemID, typeID, group.groupID, chargeInfoItem, numSlaves)
        myInfoFunctionName = self.infoFunctionNames.get(group.groupID, None)
        if myInfoFunctionName is not None:
            myInfoFunction = getattr(self, myInfoFunctionName)
            myInfoFunction(itemID, chargeInfoItem)

    def GetAttributeValue(self, itemID, attributeID, *args):
        return self.dogmaLocation.GetAccurateAttributeValue(itemID, attributeID)

    def GetDuration(self, itemID, *args):
        duration = self.GetAttributeValue(itemID, const.attributeDuration)
        durationInSec = duration / 1000.0
        if durationInSec % 1.0 == 0:
            decimalPlaces = 0
        else:
            decimalPlaces = 1
        unit = cfg.dgmunits.Get(const.unitMilliseconds).displayName
        durationFormatted = localizationUtil.FormatNumeric(durationInSec, decimalPlaces=decimalPlaces)
        formattedDuration = localization.GetByLabel('UI/InfoWindow/ValueAndUnit', value=durationFormatted, unit=unit)
        return formattedDuration

    def GetAmountPerTimeInfo(self, itemID, attributeID, configName, labelPath, *args):
        duration = self.GetDuration(itemID)
        amount = self.GetAttributeValue(itemID, attributeID)
        text = localization.GetByLabel(labelPath, duration=duration, amount=amount)
        self.AddSpecificInfoContainer(text, configName, iconID=cfg.dgmattribs.Get(attributeID).iconID)

    def AddDpsAndDamgeTypeInfo(self, itemID, typeID, groupID, charge, numSlaves, *args):
        isBomb = groupID == const.groupMissileLauncherBomb
        isLauncher = sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectLauncherFitted)
        isTurret = sm.GetService('clientDogmaStaticSvc').TypeHasEffect(typeID, const.effectTurretFitted)
        if not isLauncher and not isTurret and not isBomb:
            return
        GAV = self.dogmaLocation.GetAccurateAttributeValue
        texturePath = None
        iconID = None
        totalDpsDamage = 0
        if (isLauncher or isBomb) and charge:
            chargeKey = charge.itemID
            totalDpsDamage = self.dogmaLocation.GetLauncherDps(chargeKey, itemID, session.charid, GAV)
            damageMultiplier = GAV(session.charid, const.attributeMissileDamageMultiplier)
            if isLauncher:
                texturePath = 'res:/UI/Texture/Icons/81_64_16.png'
            else:
                iconID = cfg.invtypes.Get(typeID).iconID
        elif isTurret:
            if charge:
                chargeKey = charge.itemID
            else:
                chargeKey = None
            totalDpsDamage = self.dogmaLocation.GetTurretDps(chargeKey, itemID, GAV)
            damageMultiplier = GAV(itemID, const.attributeDamageMultiplier)
            texturePath = 'res:/UI/Texture/Icons/26_64_1.png'
        if totalDpsDamage == 0:
            return
        if numSlaves:
            totalDpsDamage = numSlaves * totalDpsDamage
            damageMultiplier = numSlaves * damageMultiplier
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/DamagePerSecond', dps=totalDpsDamage)
        self.AddSpecificInfoContainer(text, 'dpsCont', iconID=iconID, texturePath=texturePath)
        damageTypeAttributes = [(const.attributeEmDamage, None),
         (const.attributeExplosiveDamage, None),
         (const.attributeKineticDamage, None),
         (const.attributeThermalDamage, None)]
        textDict = {'noPassiveValue': 'UI/Inflight/ModuleRacks/Tooltips/DamageHitpoints',
         'manyHeaderWithoutPassive': 'UI/Inflight/ModuleRacks/Tooltips/DamageTypesHeader',
         'oneDamageTypeWithoutPassive': 'UI/Inflight/ModuleRacks/Tooltips/OneDamageTypeText'}
        if charge:
            dmgCausingItemID = charge.itemID
        else:
            dmgCausingItemID = itemID
            if numSlaves:
                damageMultiplier = numSlaves
            else:
                damageMultiplier = 1
        self.GetDamageTypeInfo(dmgCausingItemID, damageTypeAttributes, textDict, multiplier=damageMultiplier)

    def AddMiningLaserInfo(self, itemID, chargeInfoItem, *args):
        duration = self.GetDuration(itemID)
        amount = self.GetAttributeValue(itemID, const.attributeMiningAmount)
        if chargeInfoItem is not None:
            specializationMultiplier = self.GetAttributeValue(chargeInfoItem.itemID, const.attributeSpecialisationAsteroidYieldMultiplier)
            amount = specializationMultiplier * amount
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/MiningAmountPerTime', duration=duration, amount=amount)
        self.AddSpecificInfoContainer(text, 'miningAmountCont', texturePath='res:/ui/texture/icons/23_64_5.png')

    def AddEnergyVampireInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributePowerTransferAmount, configName='leachedAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/EnergyVampireAmountPerTime')

    def AddEnergyDestabilizerInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeEnergyDestabilizationAmount, configName='destablizedAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/EnergDestabilizedPerTime')

    def AddArmorRepairersInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeArmorDamageAmount, configName='armorRepairAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/ArmorRepairedPerTime')

    def AddHullRepairersInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeStructureDamageAmount, configName='hullRepairAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/HullRepairedPerTime')

    def AddShieldBoosterInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeShieldBonus, configName='shieldBoosterAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/ShieldBonusPerTime')

    def AddTrackingComputerInfo(self, itemID, *args):
        falloff = self.GetAttributeValue(itemID, const.attributeFalloffBonus)
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/TrackingComputerFalloffBonus', falloffBonus=falloff)
        self.AddSpecificInfoContainer(text, 'trackingComputerFalloffCont', iconID=cfg.dgmattribs.Get(const.attributeFalloffBonus).iconID)
        optimalBonus = self.GetAttributeValue(itemID, const.attributeMaxRangeBonus)
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/TrackingComputerRangeBonus', optimalRangeBonus=optimalBonus)
        self.AddSpecificInfoContainer(text, 'trackingComputerOptimalRangeCont', iconID=cfg.dgmattribs.Get(const.attributeMaxRangeBonus).iconID)
        tracking = self.GetAttributeValue(itemID, const.attributeTrackingSpeedBonus)
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/TrackingComputerTrackingBonus', trackingSpeedBonus=tracking)
        self.AddSpecificInfoContainer(text, 'trackingComputerTrackingSpeedCont', iconID=cfg.dgmattribs.Get(const.attributeTrackingSpeedBonus).iconID)

    def AddSmartBombInfo(self, itemID, *args):
        attrID = None
        damage = 0
        for attributeID in (const.attributeEmDamage,
         const.attributeKineticDamage,
         const.attributeThermalDamage,
         const.attributeExplosiveDamage):
            damage = self.GetAttributeValue(itemID, attributeID)
            if damage > 0:
                attrID = attributeID
                break

        attributeInfo = cfg.dgmattribs.Get(attrID)
        damageType = attributeInfo.displayName
        iconID = attributeInfo.iconID
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/SmartBombDamage', amount=damage, damageType=damageType)
        self.AddSpecificInfoContainer(text, 'smortBombAmountCont', iconID=iconID)

    def AddPropulsionModuleInfo(self, itemID, *args):
        myShip = util.GetActiveShip()
        myMaxVelocity = self.dogmaLocation.GetAttributeValue(myShip, const.attributeMaxVelocity)
        speedFactor = self.dogmaLocation.GetAttributeValue(itemID, const.attributeSpeedFactor)
        speedBoostFactor = self.dogmaLocation.GetAttributeValue(itemID, const.attributeSpeedBoostFactor)
        mass = self.dogmaLocation.GetAttributeValue(myShip, const.attributeMass)
        massAddition = self.dogmaLocation.GetAttributeValue(itemID, const.attributeMassAddition)
        maxVelocityWithBonus = myMaxVelocity * (1 + speedBoostFactor * speedFactor * 0.01 / (massAddition + mass))
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/MaxVelocityWithAndWithoutPropulsion', maxVelocity=myMaxVelocity, maxVelocityWithBonus=maxVelocityWithBonus)
        self.AddSpecificInfoContainer(text, 'propulsionModuleAmountCont', iconID=cfg.dgmattribs.Get(const.attributeMaxVelocity).iconID)

    def AddStasisWebInfo(self, itemID, *args):
        amount = self.GetAttributeValue(itemID, const.attributeSpeedFactor)
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/VelocityReductionFromWeb', percentage=abs(amount))
        self.AddSpecificInfoContainer(text, 'stasisWebAmountCont', iconID=cfg.dgmattribs.Get(const.attributeMaxVelocity).iconID)

    def AddCapacitorBoosterInfo(self, itemID, chargeInfoItem, *args):
        duration = self.GetDuration(itemID)
        if chargeInfoItem is None:
            return
        amount = self.GetAttributeValue(chargeInfoItem.itemID, const.attributeCapacitorBonus)
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/CapacitorBoostPerTime', boostAmount=amount, duration=duration)
        self.AddSpecificInfoContainer(text, 'capacitorBoosterAmountCont', iconID=cfg.dgmattribs.Get(const.attributeCapacitorBonus).iconID)

    def AddEnergyTransferArrayInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributePowerTransferAmount, configName='energyTransferArrayAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/EnergyTransferredPerTime')

    def AddShieldTransporterInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeShieldBonus, configName='shieldTransporterAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/ShieldTransportedPerTime')

    def AddArmorRepairProjectorInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeArmorDamageAmount, configName='armorRepairProjectorAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/ArmorTransferredPerTime')

    def AddRemoteHullRepairInfo(self, itemID, *args):
        self.GetAmountPerTimeInfo(itemID=itemID, attributeID=const.attributeStructureDamageAmount, configName='remoteHullRepairAmountCont', labelPath='UI/Inflight/ModuleRacks/Tooltips/HullRemoteRepairedPerTime')

    def AddWarpScramblerInfo(self, itemID, *args):
        strength = self.GetAttributeValue(itemID, const.attributeWarpScrambleStrength)
        text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/WarpScramblerStrength', strength=strength)
        self.AddSpecificInfoContainer(text, 'warpScramblerAmountCont', iconID=cfg.dgmattribs.Get(const.attributeWarpScrambleStrength).iconID)

    def AddArmorHardenerInfo(self, itemID, *args):
        damageTypeAttributes = [(const.attributeEmDamageResistanceBonus, None),
         (const.attributeExplosiveDamageResistanceBonus, None),
         (const.attributeKineticDamageResistanceBonus, None),
         (const.attributeThermalDamageResistanceBonus, None)]
        textDict = {'noPassiveValue': 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues',
         'manyHeaderWithoutPassive': 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusesHeader',
         'oneDamageTypeWithoutPassive': 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText'}
        self.GetDamageTypeInfo(itemID, damageTypeAttributes, textDict)

    def AddECMInfo(self, itemID, *args):
        damageTypeAttributes = [const.attributeScanGravimetricStrengthBonus,
         const.attributeScanLadarStrengthBonus,
         const.attributeScanMagnetometricStrengthBonus,
         const.attributeScanRadarStrengthBonus]
        rows = []
        for attrID in damageTypeAttributes:
            strength = self.GetAttributeValue(itemID, attrID)
            if strength is not None and strength != 0:
                attributeName = cfg.dgmattribs.Get(attrID).displayName
                rows.append(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ECMStrengthBonus', strength=strength, attributeName=attributeName))

        text = '<br>'.join(rows)
        self.AddSpecificInfoContainer(text, 'ecmInfoCont', iconID=None)

    def AddECCMInfo(self, itemID, *args):
        damageTypeAttributes = [const.attributeScanGravimetricStrengthPercent,
         const.attributeScanLadarStrengthPercent,
         const.attributeScanMagnetometricStrengthPercent,
         const.attributeScanRadarStrengthPercent]
        rows = []
        for attrID in damageTypeAttributes:
            strength = self.GetAttributeValue(itemID, attrID)
            if strength is not None and strength != 0:
                attributeName = cfg.dgmattribs.Get(attrID).displayName
                rows.append(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=strength, activeName=attributeName))

        text = '<br>'.join(rows)
        self.AddSpecificInfoContainer(text, 'eccmInfoCont', iconID=cfg.invgroups.Get(const.groupElectronicCounterCounterMeasures).iconID)

    def AddSensorDamperInfo(self, itemID, *args):
        bonus = self.GetAttributeValue(itemID, const.attributeScanResolutionBonus)
        if bonus != 0:
            attributeName = cfg.dgmattribs.Get(const.attributeScanResolutionBonus).displayName
            self.AddSpecificInfoContainer(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=bonus, activeName=attributeName), 'trackingDisruptorTrackingSpeedBonusCont', iconID=cfg.dgmattribs.Get(const.attributeScanResolutionBonus).iconID)
        bonus = self.GetAttributeValue(itemID, const.attributeMaxTargetRangeBonus)
        if bonus != 0:
            attributeName = cfg.dgmattribs.Get(const.attributeMaxTargetRangeBonus).displayName
            self.AddSpecificInfoContainer(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=bonus, activeName=attributeName), 'trackingDisruptorMaxRangeBonusCont', iconID=cfg.dgmattribs.Get(const.attributeMaxTargetRangeBonus).iconID)

    def AddTargetBreakerInfo(self, itemID, *args):
        strength = self.GetAttributeValue(itemID, const.attributeScanResolutionMultiplier)
        strength = self.ConvertInversedModifierPercent(strength)
        attributeName = cfg.dgmattribs.Get(const.attributeScanResolutionBonus).displayName
        self.AddSpecificInfoContainer(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=strength, activeName=attributeName), 'targetBreakerInfoCont', iconID=cfg.dgmattribs.Get(const.attributeScanResolutionBonus).iconID)

    def AddTargetPainterInfo(self, itemID, *args):
        sigRadiusBonus = self.GetAttributeValue(itemID, const.attributeSignatureRadiusBonus)
        attributeName = cfg.dgmattribs.Get(const.attributeSignatureRadiusBonus).displayName
        self.AddSpecificInfoContainer(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=sigRadiusBonus, activeName=attributeName), 'targetPainterSigRadiusCont', iconID=cfg.dgmattribs.Get(const.attributeSignatureRadiusBonus).iconID)

    def AddTrackingDisruptorInfo(self, itemID, *args):
        falloffBonus = self.GetAttributeValue(itemID, const.attributeFalloffBonus)
        attributeName = cfg.dgmattribs.Get(const.attributeFalloffBonus).displayName
        self.AddSpecificInfoContainer(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=falloffBonus, activeName=attributeName), 'trackingDisruptorFalloffBonusCont', iconID=cfg.dgmattribs.Get(const.attributeFalloffBonus).iconID)
        trackingSpeedBonus = self.GetAttributeValue(itemID, const.attributeTrackingSpeedBonus)
        if trackingSpeedBonus != 0:
            attributeName = cfg.dgmattribs.Get(const.attributeTrackingSpeedBonus).displayName
            self.AddSpecificInfoContainer(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=trackingSpeedBonus, activeName=attributeName), 'trackingDisruptorTrackingSpeedBonusCont', iconID=cfg.dgmattribs.Get(const.attributeTrackingSpeedBonus).iconID)
        maxRangeBonus = self.GetAttributeValue(itemID, const.attributeMaxRangeBonus)
        if maxRangeBonus != 0:
            attributeName = cfg.dgmattribs.Get(const.attributeMaxRangeBonus).displayName
            self.AddSpecificInfoContainer(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=maxRangeBonus, activeName=attributeName), 'trackingDisruptorMaxRangeBonusCont', iconID=cfg.dgmattribs.Get(const.attributeMaxRangeBonus).iconID)

    def AddCloakingDeviceInfo(self, itemID, *args):
        bonus = self.GetAttributeValue(itemID, const.attributeMaxVelocityBonus)
        bonus = self.ConvertInversedModifierPercent(bonus)
        attributeName = cfg.dgmattribs.Get(const.attributeMaxVelocityBonus).displayName
        self.AddSpecificInfoContainer(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusText', activeValue=bonus, activeName=attributeName), 'trackingDisruptorFalloffBonusCont', iconID=cfg.dgmattribs.Get(const.attributeMaxVelocityBonus).iconID)

    def AddTractorBeamInfo(self, itemID, *args):
        maxTractorVel = self.GetAttributeValue(itemID, const.attributeMaxTractorVelocity)
        attributeName = cfg.dgmattribs.Get(const.attributeMaxTractorVelocity).displayName
        self.AddSpecificInfoContainer(localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/TractorBeamTractorVelocity', maxTractorVel=maxTractorVel, attributeName=attributeName), 'trackingDisruptorFalloffBonusCont', iconID=cfg.dgmattribs.Get(const.attributeMaxTractorVelocity).iconID)

    def AddDamageControlInfo(self, itemID, *args):
        damageTypeAttributes = [const.attributeShieldEmDamageResonance,
         const.attributeShieldExplosiveDamageResonance,
         const.attributeShieldKineticDamageResonance,
         const.attributeShieldThermalDamageResonance]
        self.AddDamageControlInfoRow(itemID, damageTypeAttributes, 'UI/Inflight/ModuleRacks/Tooltips/ShieldDamageResistanceHeader', 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues', 'Shield')
        damageTypeAttributes = [const.attributeArmorEmDamageResonance,
         const.attributeArmorExplosiveDamageResonance,
         const.attributeArmorKineticDamageResonance,
         const.attributeArmorThermalDamageResonance]
        self.AddDamageControlInfoRow(itemID, damageTypeAttributes, 'UI/Inflight/ModuleRacks/Tooltips/ArmorDamageResistanceHeader', 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues', 'Armor')
        damageTypeAttributes = [const.attributeHullEmDamageResonance,
         const.attributeHullExplosiveDamageResonance,
         const.attributeHullKineticDamageResonance,
         const.attributeHullThermalDamageResonance]
        self.AddDamageControlInfoRow(itemID, damageTypeAttributes, 'UI/Inflight/ModuleRacks/Tooltips/HullDamageResistanceHeader', 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues', 'Hull')

    def AddDamageControlInfoRow(self, itemID, damageTypeAttributes, headerText, rowText, containerName, *args):
        headerText = localization.GetByLabel(headerText)
        allDamageTypeInfo = []
        for damageTypeAttr in damageTypeAttributes:
            attributeValue = self.GetAttributeValue(itemID, damageTypeAttr)
            attributeValue = self.ConvertInverseAbsolutePercent(attributeValue)
            allDamageTypeInfo.append((damageTypeAttr, localization.GetByLabel(rowText, activeValue=attributeValue)))

        containerName = 'damageControlContainer' + containerName
        damageTypeContMany = getattr(self, containerName, None)
        if damageTypeContMany is None or damageTypeContMany.destroyed:
            damageTypeContMany = uicls.ModuleButtonHintContainerIcons(parent=self, name=containerName, align=uiconst.TOTOP, isExtraInfoContainer=True, headerText=headerText)
            setattr(self, containerName, damageTypeContMany)
        damageTypeContMany.SetDamageTypeInfo(allDamageTypeInfo)
        damageTypeContMany.SetContainerHeight()

    def AddArmorResistanceShiftHardenerInfo(self, itemID, *args):
        damageTypeAttributes = [const.attributeArmorEmDamageResonance,
         const.attributeArmorExplosiveDamageResonance,
         const.attributeArmorKineticDamageResonance,
         const.attributeArmorThermalDamageResonance]
        self.AddDamageControlInfoRow(itemID, damageTypeAttributes, 'UI/Inflight/ModuleRacks/Tooltips/ArmorDamageResistanceHeader', 'UI/Inflight/ModuleRacks/Tooltips/ResistanceActiveBonusValues', 'Armor')

    def AddSuperWeaponInfo(self, itemID, *args):
        damageTypeAttributes = [const.attributeEmDamage,
         const.attributeExplosiveDamage,
         const.attributeKineticDamage,
         const.attributeThermalDamage]
        for damageType in damageTypeAttributes:
            damage = self.GetAttributeValue(itemID, damageType)
            if damage == 0:
                continue
            attributeName = cfg.dgmattribs.Get(damageType).displayName
            text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/SuperWeaponDamage', activeValue=damage, activeName=attributeName)
            self.AddSpecificInfoContainer(text, 'superWeaponInfoCont' + attributeName, iconID=cfg.dgmattribs.Get(damageType).iconID)

    def AddGangCoordinatorInfo(self, itemID, *args):
        commandBonus = self.GetAttributeValue(itemID, const.attributeCommandbonus)
        if commandBonus != 0:
            displayName = cfg.dgmattribs.Get(const.attributeCommandbonus).displayName
            text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/GangCoordinatorCommandBonus', commandBonus=commandBonus, attributeName=displayName)
            self.AddSpecificInfoContainer(text, 'gangCoordInfoContCommand', iconID=cfg.dgmattribs.Get(const.attributeCommandbonus).iconID)
        maxGangModulesAttr = cfg.dgmattribs.Get(const.attributeMaxGangModules)
        if maxGangModulesAttr.attributeName in self.stateManager.GetAttributes(itemID):
            maxGangModules = self.GetAttributeValue(itemID, const.attributeMaxGangModules)
            displayName = maxGangModulesAttr.displayName
            text = localization.GetByLabel('UI/Inflight/ModuleRacks/Tooltips/GangCoordinatorMaxCommandRelays', maxGangModules=maxGangModules, attributeName=displayName)
            self.AddSpecificInfoContainer(text, 'gangCoordInfoContMaxGangModules', iconID=cfg.dgmattribs.Get(const.attributeMaxGangModules).iconID)

    def ConvertInverseAbsolutePercent(self, value):
        return (1.0 - value) * 100.0

    def ConvertInversedModifierPercent(self, value):
        return -(1.0 - value) * 100.0

    def GetDamageTypeInfo(self, itemID, damageTypeAttributes, textDict, multiplier = None, *args):
        if multiplier is None:
            multiplier = 1
        allDamageTypeInfo, effectiveDamageTypes, withPassiveValues = self.GetDamageTypeAttributeInfo(itemID, damageTypeAttributes, textDict, multiplier)
        damageTypeContMany = getattr(self, 'damageTypeContMany', None)
        damagaTypeContOne = getattr(self, 'damagaTypeContOne', None)
        if len(effectiveDamageTypes) > 1:
            if damagaTypeContOne is not None and not damagaTypeContOne.destroyed:
                damagaTypeContOne.Close()
            headerText = self.GetDamageText('manyHeader', textDict, hasPassive=withPassiveValues)
            if damageTypeContMany is None or damageTypeContMany.destroyed:
                damageTypeContMany = uicls.ModuleButtonHintContainerIcons(parent=self, name='damageTypeContMany', align=uiconst.TOTOP, isExtraInfoContainer=True, headerText=headerText)
                self.damageTypeContMany = damageTypeContMany
            damageTypeContMany.SetDamageTypeInfo(allDamageTypeInfo)
            damageTypeContMany.SetContainerHeight()
        elif len(effectiveDamageTypes) == 1:
            if damageTypeContMany is not None:
                damageTypeContMany.Close()
            activeAttributeID, activeValue, passiveAttributeID, passiveValue = effectiveDamageTypes[0]
            text = self.GetDamageText('oneDamageType', textDict, activeAttributeID, activeValue, passiveAttributeID, passiveValue, multiplier=multiplier, hasPassive=withPassiveValues)
            self.AddSpecificInfoContainer(text, 'damagaTypeContOne', iconID=cfg.dgmattribs.Get(activeAttributeID).iconID)

    def GetDamageTypeAttributeInfo(self, itemID, damageTypeAttributes, textDict, multiplier, *args):
        effectiveDamageTypes = []
        allDamageTypeInfo = []
        withPassiveValues = False
        for activeAttributeID, passiveAttributeID in damageTypeAttributes:
            activeValue = self.GetAttributeValue(itemID, activeAttributeID)
            if passiveAttributeID:
                passiveValue = self.GetAttributeValue(itemID, passiveAttributeID)
                withPassiveValues = True
            else:
                passiveValue = 0
            text = self.GetDamageText('value', textDict, activeAttributeID, activeValue, passiveAttributeID, passiveValue, multiplier=multiplier)
            if text:
                effectiveDamageTypes.append((activeAttributeID,
                 activeValue,
                 passiveAttributeID,
                 passiveValue))
            allDamageTypeInfo.append((activeAttributeID, text))

        return (allDamageTypeInfo, effectiveDamageTypes, withPassiveValues)

    def GetDamageText(self, textTypeToGet, textDict, activeAttributeID = None, activeValue = None, passiveAttributeID = None, passiveValue = None, hasPassive = True, multiplier = 1, *args):
        if textTypeToGet == 'value':
            if activeValue == 0 and passiveValue == 0:
                return ''
            elif passiveValue == 0:
                return localization.GetByLabel(textDict['noPassiveValue'], activeValue=multiplier * activeValue)
            else:
                return localization.GetByLabel(textDict['activeAndPassiveValues'], activeValue=multiplier * activeValue, passiveValue=multiplier * passiveValue)
        elif textTypeToGet == 'manyHeader':
            if hasPassive:
                return localization.GetByLabel(textDict['manyHeaderWithPassive'])
            else:
                return localization.GetByLabel(textDict['manyHeaderWithoutPassive'])
        elif textTypeToGet == 'oneDamageType':
            if hasPassive:
                return localization.GetByLabel(textDict['oneDamageTypeWithPassive'], activeName=cfg.dgmattribs.Get(activeAttributeID).displayName, passiveName=cfg.dgmattribs.Get(passiveAttributeID).displayName, activeValue=multiplier * activeValue, passiveValue=passiveValue)
            else:
                return localization.GetByLabel(textDict['oneDamageTypeWithoutPassive'], activeName=cfg.dgmattribs.Get(activeAttributeID).displayName, activeValue=multiplier * activeValue)
        return ''

    def PositionHint(self, left = None, top = None, bottom = None, *args):
        if self.parent is None:
            self.Close()
            return
        pw, ph = self.parent.GetAbsoluteSize()
        w, h = self.GetAbsoluteSize()
        x = left or uicore.uilib.x
        y = top or uicore.uilib.y
        self.left = max(0, min(x, pw - self.width))
        self.top = y - self.height - 4
        if settings.user.ui.Get('shipuialigntop', 0) and bottom is not None:
            self.top = bottom
        else:
            self.top = max(0, min(self.top, ph - self.height))

    def FadeOpacity(self, toOpacity):
        if toOpacity == getattr(self, '_settingOpacity', None):
            return
        self._newOpacity = toOpacity
        self._settingOpacity = toOpacity
        uthread.worker('ModuleButtonHint::FadeOpacity', self.FadeOpacityThread, toOpacity)

    def FadeOpacityThread(self, toOpacity):
        self._newOpacity = None
        ndt = 0.0
        start = blue.os.GetWallclockTime()
        startOpacity = self.opacity
        while ndt != 1.0:
            ndt = min(float(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime())) / float(250.0), 1.0)
            self.opacity = min(1.0, max(0.0, mathUtil.Lerp(startOpacity, toOpacity, ndt)))
            if toOpacity == 1.0:
                self.Show()
            blue.pyos.synchro.Yield()
            if self._newOpacity:
                return

        if toOpacity == 0.0:
            self.Hide()


class ModuleButtonHintContainerBase(uicls.Container):
    __guid__ = 'uicls.ModuleButtonHintContainerBase'
    default_state = uiconst.UI_DISABLED
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        self.iconSize = 26
        uicls.Container.ApplyAttributes(self, attributes)
        self.moduleTypeID = attributes.typeID
        self.iconCont = uicls.Container(parent=self, name='iconCont', align=uiconst.TOLEFT, width=self.iconSize, padLeft=const.defaultPadding)
        self.textCont = uicls.Container(parent=self, name='textCont', align=uiconst.TOALL)
        self.icon = uicls.Icon(parent=self.iconCont, name='icon', align=uiconst.CENTER, size=self.iconSize, ignoreSize=True)
        self.textLabel = uicls.EveLabelMedium(text='', parent=self.textCont, name='textLabel', align=uiconst.CENTERLEFT, left=8)
        self.isExtraInfoContainer = attributes.get('isExtraInfoContainer', False)
        if attributes.iconID:
            self.LoadIconByIconID(attributes.iconID)
        elif attributes.texturePath:
            self.SetIconPath(attributes.texturePath)
        self.smallContainerHeight = attributes.get('smallContainerHeight', 30)
        self.bigContainerHeight = attributes.get('bigContainerHeight', 36)

    def SetIconPath(self, texturePath):
        self.icon.LoadTexture(texturePath)

    def LoadIconByIconID(self, iconID):
        self.icon.LoadIcon(iconID, ignoreSize=True)

    def SetContainerHeight(self, *args):
        textHeight = self.textLabel.textheight
        if textHeight < self.smallContainerHeight - 2:
            self.height = self.smallContainerHeight
        elif textHeight < self.bigContainerHeight - 2:
            self.height = self.bigContainerHeight
        else:
            self.height = textHeight + 2

    def GetContainerWidth(self, *args):
        if self.display == True:
            myWidth = self.textLabel.textwidth + self.textLabel.left + self.iconCont.width + self.iconCont.left
            return myWidth
        return 0


class ModuleButtonHintContainerSafetyLevel(ModuleButtonHintContainerBase):
    __guid__ = 'uicls.ModuleButtonHintContainerSafetyLevel'

    def ApplyAttributes(self, attributes):
        attributes.texturePath = 'res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal.png'
        uicls.ModuleButtonHintContainerBase.ApplyAttributes(self, attributes)
        self.icon.width = self.icon.height = 16

    def SetSafetyLevelWarning(self, safetyLevel):
        if safetyLevel == const.shipSafetyLevelNone:
            self.icon.color.SetRGBA(*crimewatchConst.Colors.Criminal.GetRGBA())
            self.textLabel.text = localization.GetByLabel('UI/Crimewatch/SafetyLevel/ModuleRestrictionTooltip', color=crimewatchConst.Colors.Criminal.GetHex())
        else:
            self.icon.color.SetRGBA(*crimewatchConst.Colors.Suspect.GetRGBA())
            self.textLabel.text = localization.GetByLabel('UI/Crimewatch/SafetyLevel/ModuleRestrictionTooltip', color=crimewatchConst.Colors.Suspect.GetHex())


class ModuleButtonHintContainerType(ModuleButtonHintContainerBase):
    __guid__ = 'uicls.ModuleButtonHintContainerType'

    def ApplyAttributes(self, attributes):
        uicls.ModuleButtonHintContainerBase.ApplyAttributes(self, attributes)
        self.techIcon = uicls.Icon(parent=self.iconCont, width=16, height=16, align=uiconst.TOPLEFT, idx=0, top=4)

    def SetTypeIcon(self, typeID = None, iconSize = 26):
        self.icon.LoadIconByTypeID(typeID, size=self.iconSize, ignoreSize=True)
        uix.GetTechLevelIcon(self.techIcon, typeID=typeID)

    def SetTypeTextAndDamage(self, typeName, damage, numSlaves, bold = True):
        if numSlaves:
            typeText = localization.GetByLabel('UI/Inflight/ModuleRacks/TypeNameWithNumInGroup', numInGroup=numSlaves, typeName=typeName)
        else:
            typeText = typeName
        if bold:
            typeText = '<b>%s</b>' % typeText
        self.textLabel.text = typeText
        if damage > 0:
            damagedText = localization.GetByLabel('UI/Inflight/ModuleRacks/ModuleDamaged', color='<color=red>', percentageNum=damage)
            self.textLabel.text += '<br>' + damagedText
            if getattr(self, 'shortcutText', None) is not None:
                self.shortcutText.text += '<br>'

    def AddFading(self, parentWidth, *args):
        availableTextWidth = parentWidth - self.icon.width - self.textLabel.left
        self.textLabel.SetRightAlphaFade(fadeEnd=availableTextWidth, maxFadeWidth=20)


class ModuleButtonHintContainerTypeWithShortcut(ModuleButtonHintContainerType):
    __guid__ = 'uicls.ModuleButtonHintContainerTypeWithShortcut'

    def ApplyAttributes(self, attributes):
        uicls.ModuleButtonHintContainerType.ApplyAttributes(self, attributes)
        self.shortcutCont = uicls.Container(parent=self, name='shortcutCont', align=uiconst.TORIGHT, width=32, state=uiconst.UI_HIDDEN)
        self.shortcutText = uicls.EveLabelMedium(text='', parent=self.shortcutCont, name='shortcutText', align=uiconst.CENTERRIGHT, left=8)
        self.shortcutCont.textLabel = self.shortcutText
        self.shortcutPadding = 0

    def SetShortcutText(self, moduleShortcut):
        self.shortcutPadding = 0
        if moduleShortcut:
            self.shortcutText.text = localization.GetByLabel('UI/Inflight/ModuleRacks/HintShortcut', shotcutString=moduleShortcut)
            self.shortcutCont.display = True
            self.shortcutCont.width = self.shortcutText.textwidth + 14
            shortcutPadding = self.shortcutCont.width + 10
        else:
            self.shortcutText.text = ''
            self.shortcutCont.display = False
        self.shortcutPadding = shortcutPadding

    def GetContainerWidth(self, *args):
        myWidth = uicls.ModuleButtonHintContainerType.GetContainerWidth(self)
        myWidth += self.shortcutPadding
        return myWidth

    def AddFading(self, parentWidth, *args):
        availableTextWidth = parentWidth - self.icon.width - self.textLabel.left - self.shortcutPadding
        self.textLabel.SetRightAlphaFade(fadeEnd=availableTextWidth, maxFadeWidth=20)


class ModuleButtonHintContainerIcons(uicls.Container):
    __guid__ = 'uicls.ModuleButtonHintContainerIcons'
    default_state = uiconst.UI_DISABLED

    def ApplyAttributes(self, attributes):
        self.iconSize = 26
        uicls.Container.ApplyAttributes(self, attributes)
        self.moduleTypeID = attributes.typeID
        self.textLabel = uicls.EveLabelMedium(text='', parent=self, name='textLabel', align=uiconst.TOTOP, padTop=const.defaultPadding, padLeft=self.iconSize + 3 * const.defaultPadding, maxLines=1)
        self.allIconCont = uicls.Container(parent=self, name='allIconCont', align=uiconst.TOTOP, height=30)
        self.isExtraInfoContainer = attributes.get('isExtraInfoContainer', False)
        self.textLabel.text = attributes.headerText
        allDamageTypeInfo = attributes.allDamageTypeInfo

    def SetDamageTypeInfo(self, damageTypeInfo):
        for each in damageTypeInfo:
            attributeID, text = each
            self.SetText(attributeID, text)

    def SetText(self, attributeID, text):
        if text == '':
            cont = self.FindDamageTypeContainer(attributeID)
            if cont:
                cont.display = False
            return
        damageTypeContainer = self.GetDamageTypeContainer(attributeID)
        damageTypeContainer.textLabel.text = text
        damageTypeContainer.width = max(64, damageTypeContainer.textLabel.textwidth + self.iconSize + 10)
        damageTypeContainer.display = True

    def FindDamageTypeContainer(self, attributeID, *args):
        myContainerName = 'damageTypeCont_%s' % attributeID
        return getattr(self, myContainerName, None)

    def GetDamageTypeContainer(self, attributeID, *args):
        myContainer = self.FindDamageTypeContainer(attributeID)
        if not myContainer or myContainer.destroyed:
            myContainerName = 'damageTypeCont_%s' % attributeID
            myContainer = uicls.Container(parent=self.allIconCont, name=myContainerName, align=uiconst.TOLEFT, width=64)
            setattr(self, myContainerName, myContainer)
            attributeInfo = cfg.dgmattribs.Get(attributeID)
            iconID = attributeInfo.iconID
            icon = uicls.Icon(parent=myContainer, name='icon', align=uiconst.CENTERLEFT, size=self.iconSize, ignoreSize=True)
            icon.LoadIcon(iconID, ignoreSize=True)
            myContainer.icon = icon
            textLabel = uicls.EveLabelMedium(text='', parent=myContainer, name='textLabel', align=uiconst.CENTERLEFT, left=self.iconSize)
            myContainer.textLabel = textLabel
        return myContainer

    def SetContainerHeight(self, *args):
        self.height = self.textLabel.textheight + self.allIconCont.height + self.allIconCont.padTop + 2 * const.defaultPadding

    def GetContainerWidth(self, *args):
        textWidth = self.textLabel.textwidth + self.textLabel.padLeft
        visibleIconsWidths = [ child.width for child in self.allIconCont.children if child.display == True ]
        myWidth = max(textWidth, sum(visibleIconsWidths))
        return myWidth