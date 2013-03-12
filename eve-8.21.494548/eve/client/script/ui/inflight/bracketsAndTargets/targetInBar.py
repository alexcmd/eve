#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/inflight/bracketsAndTargets/targetInBar.py
import blue
import uthread
import uix
import uiutil
import util
import state
import base
import random
import _weakref
import uicls
import uiconst
import xtriui
import localization
import telemetry
import math
import trinity
accuracyThreshold = 0.8
SHIELD = 0
ARMOR = 1
HULL = 2
HOVERTIME = 250

class TargetInBar(uicls.ContainerAutoSize):
    __guid__ = 'uicls.TargetInBar'
    __notifyevents__ = ['ProcessShipEffect',
     'OnStateChange',
     'OnJamStart',
     'OnJamEnd',
     'OnSlimItemChange',
     'OnDroneStateChange2',
     'OnDroneControlLost',
     'OnStateSetupChance',
     'OnSetPlayerStanding',
     'OnItemNameChange',
     'OnUIRefresh',
     'OnFleetJoin_Local',
     'OnFleetLeave_Local',
     'OnSuspectsAndCriminalsUpdate',
     'OnCrimewatchEngagementUpdated']

    def init(self):
        self.lastDistance = None
        self.sr.updateTimer = None
        self.drones = {}
        self.activeModules = {}
        self.lastDataUsedForLabel = None
        self.lastTextUsedForLabel = None
        self.lastTextUsedDistance = None
        self.lastTextUsedForShipType = None
        self.jammingModules = {}
        self.innerHealthBorder = pow(28, 2)
        self.outerHealthBorder = pow(42, 2)
        self._hoverThread = None

    def OnUIRefresh(self):
        self.Flush()
        self.init()
        bp = sm.GetService('michelle').GetBallpark()
        if bp is not None:
            slimItem = bp.GetInvItem(self.id)
        self.Startup(slimItem)

    def Startup(self, slimItem):
        sm.RegisterNotify(self)
        obs = sm.GetService('target').IsObserving()
        self.ball = _weakref.ref(sm.GetService('michelle').GetBall(slimItem.itemID))
        self.slimItem = _weakref.ref(slimItem)
        self.id = slimItem.itemID
        self.itemID = slimItem.itemID
        self.updatedamage = slimItem.categoryID != const.categoryAsteroid and slimItem.groupID != const.groupHarvestableCloud and slimItem.groupID != const.groupOrbitalTarget
        self.iconSize = iconSize = 94
        barAndImageCont = uicls.Container(parent=self, name='barAndImageCont', align=uiconst.TOTOP, height=100, state=uiconst.UI_NORMAL)
        iconPar = uicls.Container(parent=barAndImageCont, name='iconPar', width=iconSize, height=iconSize, align=uiconst.CENTERTOP, state=uiconst.UI_DISABLED)
        barAndImageCont.OnMouseDown = self.OnTargetMouseDown
        barAndImageCont.OnMouseUp = self.OnTargetMouseUp
        barAndImageCont.OnClick = self.OnTargetClick
        barAndImageCont.GetMenu = self.GetTargetMenu
        barAndImageCont.OnMouseEnter = self.OnTargetMouseEnter
        barAndImageCont.OnMouseExit = self.OnTargetMouseExit
        self.barAndImageCont = barAndImageCont
        maskSize = 50
        iconPadding = (iconSize - maskSize) / 2
        icon = uicls.Icon(parent=iconPar, left=iconPadding, top=iconPadding, width=maskSize, height=maskSize, typeID=slimItem.typeID, textureSecondaryPath='res:/UI/Texture/classes/Target/shipMask.png', color=(1.0, 1.0, 1.0, 1.0), blendMode=1, spriteEffect=trinity.TR2_SFX_MODULATE, state=uiconst.UI_DISABLED, ignoreSize=True)
        if slimItem.groupID == const.groupOrbitalTarget:
            sm.GetService('photo').GetPortrait(slimItem.ownerID, 64, icon)
        if self.updatedamage:
            self.healthBar = uicls.TargetHealthBars(parent=iconPar, itemID=self.itemID)
        self.sr.activeTarget = uicls.ActiveTargetOnBracket(parent=iconPar, itemID=self.itemID)
        self.sr.iconPar = iconPar
        self.slimForFlag = slimItem
        self.SetStandingIcon()
        self.sr.hilite = uicls.Sprite(name='hiliteSprite', parent=iconPar, left=-5, top=-5, width=100, height=100, texturePath='res:/UI/Texture/classes/Target/targetUnderlay.png', color=(1.0, 1.0, 1.0, 0.05))
        circle = uicls.Sprite(name='circle', align=uiconst.CENTER, parent=iconPar, width=iconSize + 2, height=iconSize + 2, texturePath='res:/UI/Texture/classes/Target/outerCircle.png', color=(1.0, 1.0, 1.0, 0.5), state=uiconst.UI_DISABLED)
        self.circle = circle
        self.sr.activeTarget.RotateArrows()
        if not obs:
            labelClass = uicls.EveLabelSmall
        else:
            labelClass = uicls.EveLabelMedium
        labelContainer = uicls.ContainerAutoSize(parent=self, name='labelContainer', align=uiconst.TOTOP)
        self.sr.label = labelClass(text=' ', parent=labelContainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, maxLines=1)
        self.sr.label2 = labelClass(text=' ', parent=labelContainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, maxLines=1)
        self.sr.shipLabel = labelClass(text=' ', parent=labelContainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, maxLines=1)
        self.sr.distanceLabel = labelClass(text=' ', parent=labelContainer, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, maxLines=1)
        self.SetTargetLabel()
        self.sr.assignedPar = uicls.Container(name='assignedPar', align=uiconst.TOTOP, parent=self, height=32)
        self.sr.assigned = uicls.Container(name='assigned', align=uiconst.CENTERTOP, parent=self.sr.assignedPar, height=32)
        self.sr.updateTimer = base.AutoTimer(random.randint(750, 1000), self.UpdateData)
        self.UpdateData()
        selected = sm.GetService('state').GetExclState(state.selected)
        self.Select(selected == slimItem.itemID)
        hilited = sm.GetService('state').GetExclState(state.mouseOver)
        self.Hilite(hilited == slimItem.itemID)
        activeTargetID = sm.GetService('target').GetActiveTargetID()
        self.ActiveTarget(activeTargetID == slimItem.itemID)
        drones = sm.GetService('michelle').GetDrones()
        for key in drones:
            droneState = drones[key]
            if droneState.targetID == self.id:
                self.drones[droneState.droneID] = droneState.typeID

        self.UpdateDrones()
        for moduleInfo in sm.GetService('godma').GetStateManager().GetActiveModulesOnTargetID(slimItem.itemID):
            self.AddWeapon(moduleInfo)

    def OnItemNameChange(self, *args):
        uthread.new(self.SetTargetLabel)

    def SetTargetLabel(self):
        obs = sm.GetService('target').IsObserving()
        self.label = uix.GetSlimItemName(self.slimForFlag)
        if self.slimForFlag.corpID:
            self.label = localization.GetByLabel('UI/Inflight/Target/TargetLabelWithTicker', target=uix.GetSlimItemName(self.slimForFlag), ticker=cfg.corptickernames.Get(self.slimForFlag.corpID).tickerName)
        if self.slimForFlag.corpID and self.slimForFlag.typeID and self.slimForFlag.categoryID == const.categoryShip:
            self.shipLabel = cfg.invtypes.Get(self.slimForFlag.typeID).name
        else:
            self.shipLabel = ''
        if obs:
            self.label = sm.GetService('bracket').DisplayName(self.slimForFlag, uix.GetSlimItemName(self.slimForFlag))
        self.UpdateData()

    def OnSetPlayerStanding(self, *args):
        self.SetStandingIcon()

    def OnStateSetupChance(self, *args):
        self.SetStandingIcon()

    def SetStandingIcon(self):
        stateMgr = sm.GetService('state')
        flag = stateMgr.CheckStates(self.slimForFlag, 'flag')
        self.standingIcon = uix.SetStateFlagForFlag(self.sr.iconPar, flag, top=8, left=0, showHint=False)
        if self.sr.iconPar.sr.flag:
            self.sr.iconPar.sr.flag.SetAlign(uiconst.CENTERBOTTOM)

    def OnSuspectsAndCriminalsUpdate(self, criminalizedCharIDs, decriminalizedCharIDs):
        if self.slimForFlag.charID in criminalizedCharIDs or self.slimForFlag.charID in decriminalizedCharIDs:
            self.SetStandingIcon()

    def OnCrimewatchEngagementUpdated(self, otherCharId, timeout):
        if self.slimForFlag.charID == otherCharId:
            self.SetStandingIcon()

    def OnFleetJoin_Local(self, member, *args):
        if session.charid == member.charID or self.slimForFlag.charID == member.charID:
            self.SetStandingIcon()

    def OnFleetLeave_Local(self, member, *args):
        if session.charid == member.charID or self.slimForFlag.charID == member.charID:
            self.SetStandingIcon()

    def OnSlimItemChange(self, oldSlim, newSlim):
        uthread.new(self._OnSlimItemChange, oldSlim, newSlim)

    def _OnSlimItemChange(self, oldSlim, newSlim):
        if self.itemID != oldSlim.itemID or self.destroyed:
            return
        self.itemID = newSlim.itemID
        self.slimItem = _weakref.ref(newSlim)
        if oldSlim.corpID != newSlim.corpID or oldSlim.charID != newSlim.charID:
            self.label = uix.GetSlimItemName(newSlim)
            self.UpdateData()

    def OnStateChange(self, itemID, flag, true, *args):
        if not self.destroyed:
            uthread.new(self._OnStateChange, itemID, flag, true)

    def _OnStateChange(self, itemID, flag, true):
        if self.destroyed or self.itemID != itemID:
            return
        if flag == state.mouseOver:
            self.Hilite(true)
        elif flag == state.selected:
            self.Select(true)
        elif flag == state.activeTarget:
            self.ActiveTarget(true)

    def Hilite(self, state):
        if self.sr.hilite:
            self.sr.hilite.state = [uiconst.UI_HIDDEN, uiconst.UI_DISABLED][state]

    def Select(self, state):
        pass

    def OnJamStart(self, sourceBallID, moduleID, targetBallID, jammingType, startTime, duration):
        if targetBallID != self.id:
            return
        self.jammingModules[moduleID] = (sourceBallID,
         moduleID,
         targetBallID,
         startTime,
         duration)
        self.StartTimer(moduleID, duration)

    def OnJamEnd(self, sourceBallID, moduleID, targetBallID, jammingType):
        if not self or self.destroyed:
            return
        if moduleID in self.jammingModules:
            moduleIconCont = self.GetWeapon(moduleID)
            if moduleIconCont:
                if moduleIconCont.icon:
                    moduleIconCont.StopAnimations()
                    moduleIconCont.opacity = 1.0
                    moduleIconCont.icon.SetRGB(1, 1, 1, 1.0)
                    moduleIconCont.icon.baseAlpha = 0.3
                self.RemoveTimer(moduleID)
            del self.jammingModules[moduleID]

    def StartTimer(self, moduleID, duration, *args):
        moduleIconCont = self.GetWeapon(moduleID)
        if moduleIconCont and moduleIconCont.icon:
            moduleIconCont.icon.SetRGB(1, 1, 1, 1.0)
            moduleIconCont.icon.baseAlpha = 1.0
            leftTimer, rightTimer = self.GetTimers(moduleIconCont)
            durationInSec = duration / 1000
            curvePoints = ([0, math.pi], [0.5, 0], [1, 0])
            uicore.animations.MorphScalar(rightTimer, 'rotationSecondary', duration=durationInSec, curveType=curvePoints)
            curvePoints = ([0, 0], [0.5, 0], [1, -math.pi])
            uicore.animations.MorphScalar(leftTimer, 'rotationSecondary', duration=durationInSec, curveType=curvePoints)
            blinkIn = durationInSec - 5
            timerName = 'ecmTimer_%s' % moduleID
            setattr(self, timerName, base.AutoTimer(blinkIn * 1000, self.BlinkModule, moduleID))

    def BlinkModule(self, moduleID, *args):
        timerName = 'ecmTimer_%s' % moduleID
        setattr(self, timerName, None)
        moduleIconCont = self.GetWeapon(moduleID)
        if moduleIconCont and not moduleIconCont.destroyed:
            duration = 1.0
            numLoops = 5 / duration
            uicore.animations.BlinkIn(moduleIconCont, startVal=0.0, endVal=1.0, duration=duration, loops=numLoops)

    def GetTimers(self, moduleIconCont, *args):
        right = getattr(moduleIconCont, 'rightSide', None)
        left = getattr(moduleIconCont, 'leftSide', None)
        if not right or right.destroyed:
            rightSide = uicls.Sprite(name='rightSide', parent=moduleIconCont, align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/Target/ecmCounterRight.png', textureSecondaryPath='res:/UI/Texture/classes/Target/ecmCounterGauge.png', blendMode=1, spriteEffect=trinity.TR2_SFX_MODULATE, state=uiconst.UI_DISABLED)
            rightSide.SetRGB(0.5, 0.5, 0.5, 0.5)
        else:
            rightSide = right
        if not left or left.destroyed:
            leftSide = uicls.Sprite(name='leftSide', parent=moduleIconCont, align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/Target/ecmCounterLeft.png', textureSecondaryPath='res:/UI/Texture/classes/Target/ecmCounterGauge.png', blendMode=1, spriteEffect=trinity.TR2_SFX_MODULATE, state=uiconst.UI_DISABLED)
            leftSide.SetRGB(0.5, 0.5, 0.5, 0.5)
        else:
            leftSide = left
        leftSide.baseRotation = math.pi
        leftSide.rotationSecondary = leftSide.baseRotation
        rightSide.baseRotation = 0
        rightSide.rotationSecondary = rightSide.baseRotation
        moduleIconCont.rightSide = rightSide
        moduleIconCont.leftSide = leftSide
        return (leftSide, rightSide)

    def RemoveTimer(self, moduleID, *args):
        moduleIconCont = self.GetWeapon(moduleID)
        if not moduleIconCont or moduleIconCont.destroyed:
            return
        moduleIconCont.icon.SetRGB(1, 1, 1, moduleIconCont.icon.baseAlpha)
        for sideName in ('leftSide', 'rightSide'):
            side = getattr(moduleIconCont, sideName, None)
            if side:
                side.Close()
                setattr(moduleIconCont, sideName, None)

    def _HoverThread(self):
        while True:
            blue.synchro.SleepWallclock(HOVERTIME)
            self.OnTargetMouseHover()
            uicore.CheckHint()

    def KillHoverThread(self, *args):
        if self._hoverThread:
            self._hoverThread.kill()
            self._hoverThread = None

    def OnTargetMouseHover(self, *args):
        if not self.sr.iconPar or self.sr.iconPar.destroyed or not getattr(self, 'healthBar', None):
            self.KillHoverThread()
            return
        if self.healthBar.destroyed:
            self.KillHoverThread()
            return
        l, t, w, h = self.sr.iconPar.GetAbsolute()
        cX = w / 2 + l
        cY = h / 2 + t
        x = uicore.uilib.x - cX
        y = uicore.uilib.y - cY
        if y > 55:
            self.barAndImageCont.SetHint('')
            return
        length2 = pow(x, 2) + pow(y, 2)
        if length2 < self.innerHealthBorder or length2 > self.outerHealthBorder:
            self.barAndImageCont.SetHint('')
            return
        rad = math.atan2(y, x)
        degrees = 180 * rad / math.pi
        if degrees < 0:
            degrees = 360 + degrees
        if degrees > 45 and degrees < 135:
            return
        self.SetHintText()

    def SetHintText(self):
        hintList = []
        percLeft = self.healthBar.GetDamageHint(SHIELD)
        if percLeft is not None:
            percLeft = 100 * percLeft
            hintList.append(localization.GetByLabel('UI/Inflight/Target/GaugeShieldRemaining', percentage=percLeft))
        percLeft = self.healthBar.GetDamageHint(ARMOR)
        if percLeft is not None:
            percLeft = 100 * percLeft
            hintList.append(localization.GetByLabel('UI/Inflight/Target/GaugeArmorRemaining', percentage=percLeft))
        percLeft = self.healthBar.GetDamageHint(HULL)
        if percLeft is not None:
            percLeft = 100 * percLeft
            hintList.append(localization.GetByLabel('UI/Inflight/Target/GaugeStructureRemaining', percentage=percLeft))
        hint = '<br>'.join(hintList)
        self.barAndImageCont.SetHint(hint)

    def GetShipID(self):
        return self.itemID

    def GetIcon(self, icon, typeID, size):
        if not self.destroyed:
            icon.LoadIconByTypeID(typeID)
            icon.SetSize(size, size)

    def _OnClose(self, *args):
        sm.UnregisterNotify(self)
        self.sr.updateTimer = None

    def ProcessShipEffect(self, godmaStm, effectState):
        slimItem = self.slimItem()
        if slimItem and effectState.environment[3] == slimItem.itemID:
            if effectState.start:
                if self.GetWeapon(effectState.itemID):
                    return
                moduleInfo = self.GetModuleInfo(effectState.itemID)
                if moduleInfo:
                    self.AddWeapon(moduleInfo)
                    self.activeModules[effectState.itemID] = moduleInfo
            else:
                self.RemoveWeapon(effectState.itemID)
                self.activeModules.pop(effectState.itemID, None)

    def AddWeapon(self, moduleInfo):
        if self is None or self.destroyed:
            return
        cont = uicls.Container(parent=self.sr.assigned, align=uiconst.RELATIVE, width=32, height=32, state=uiconst.UI_HIDDEN)
        icon = uicls.Icon(parent=cont, align=uiconst.TOALL, width=0, height=0, state=uiconst.UI_NORMAL, typeID=moduleInfo.typeID)
        cont.sr.moduleID = moduleInfo.itemID
        cont.icon = icon
        icon.sr.moduleID = moduleInfo.itemID
        icon.OnClick = (self.ClickWeapon, icon)
        icon.OnMouseEnter = (self.OnMouseEnterWeapon, icon)
        icon.OnMouseExit = (self.OnMouseExitWeapon, icon)
        icon.OnMouseHover = (self.OnMouseHoverWeapon, icon)
        if self.IsECMModule(moduleInfo.typeID):
            icon.baseAlpha = 0.3
        else:
            icon.baseAlpha = 1.0
        icon.SetAlpha(icon.baseAlpha)
        self.ArrangeWeapons()
        self._SetSizeAutomatically()
        uthread.new(sm.GetService('target').AdjustRowSize)

    def IsECMModule(self, typeID, *args):
        try:
            effect = sm.GetService('godma').GetStateManager().GetDefaultEffect(typeID)
            return cfg.dgmeffects.Get(effect.effectID).electronicChance
        except KeyError:
            return False

    def ClickWeapon(self, icon):
        shipui = uicore.layer.shipui
        if shipui:
            module = shipui.GetModule(icon.sr.moduleID)
            if module:
                module.Click()

    def OnMouseEnterWeapon(self, icon):
        module = uicore.layer.shipui.GetModuleFromID(icon.sr.moduleID)
        if module is not None:
            module.InitHilite()
            module.sr.hilite.display = True
        sm.GetService('bracket').ShowHairlinesForModule(icon.sr.moduleID, reverse=True)

    def OnMouseExitWeapon(self, icon):
        module = uicore.layer.shipui.GetModuleFromID(icon.sr.moduleID)
        if module is not None:
            module.RemoveHilite()
        sm.GetService('bracket').StopShowingModuleRange(icon.sr.moduleID)

    def OnMouseHoverWeapon(self, icon):
        if icon.sr.moduleID in self.jammingModules:
            sourceBallID, moduleID, targetBallID, startTime, duration = self.jammingModules[icon.sr.moduleID]
            now = blue.os.GetSimTime()
            timeSinceStart = now - startTime
            timeLeft = duration - timeSinceStart / 10000
            icon.hint = localization.GetByLabel('UI/Inflight/Target/ECMTimeLeft', secondsLeft=timeLeft / 1000)
        else:
            icon.hint = ''

    def IsEffectActivatible(self, effect):
        return effect.isDefault and effect.effectName != 'online' and effect.effectCategory in (const.dgmEffActivation, const.dgmEffTarget)

    def RemoveWeapon(self, moduleID):
        iconCont = self.GetWeapon(moduleID)
        if iconCont:
            iconCont.Close()
        self.ArrangeWeapons()
        self._SetSizeAutomatically()
        uthread.new(sm.GetService('target').AdjustRowSize)

    def ArrangeWeapons(self):
        if self and not self.destroyed and self.sr.assigned:
            numWeapons = len(self.sr.assigned.children)
            if numWeapons > 2:
                size = 24
            else:
                size = 32
            left = 0
            top = 0
            row = 0
            column = -1
            maxColumns = 4
            for cont in self.sr.assigned.children:
                if isinstance(cont, uicls.Frame):
                    continue
                column += 1
                if column >= maxColumns:
                    column = 0
                    row += 1
                cont.width = cont.height = size
                cont.left = column * size
                cont.top = row * size
                cont.state = uiconst.UI_PICKCHILDREN

            if row > 0:
                self.sr.assigned.width = maxColumns * size
            else:
                self.sr.assigned.width = size * (column + 1)
            self.sr.assigned.height = max(32, size * (row + 1))
            self.sr.assignedPar.height = self.sr.assigned.height

    def GetWeapon(self, moduleID):
        if self is None or self.destroyed:
            return
        if self.sr.assigned:
            for cont in self.sr.assigned.children:
                if isinstance(cont, uicls.Frame):
                    continue
                if cont.sr.moduleID == moduleID:
                    return cont

    def GetModuleInfo(self, moduleID):
        ship = sm.GetService('godma').GetItem(eve.session.shipid)
        if ship is None:
            return
        for module in ship.modules:
            if module.itemID == moduleID:
                return module

    def ResetModuleIcon(self, moduleID, *args):
        if moduleID in self.activeModules:
            weapon = self.GetWeapon(moduleID)
            icon = weapon.icon
            icon.SetAlpha(icon.baseAlpha)

    def OnTargetClick(self, *args):
        sm.GetService('state').SetState(self.itemID, state.selected, 1)
        sm.GetService('state').SetState(self.itemID, state.activeTarget, 1)
        sm.GetService('menu').TacticalItemClicked(self.itemID)

    def GetTargetMenu(self):
        obs = sm.GetService('target').IsObserving()
        m = []
        if obs:
            m += [(uiutil.MenuLabel('UI/Inflight/Target/ToggleTeam'), sm.GetService('target').ToggleTeam, (self.itemID,))]
            m += [(uiutil.MenuLabel('UI/Inflight/Target/MoveUp'), sm.GetService('target').MoveUp, (self.itemID,))]
            m += [(uiutil.MenuLabel('UI/Inflight/Target/MoveDown'), sm.GetService('target').MoveDown, (self.itemID,))]
        m += sm.GetService('menu').CelestialMenu(self.itemID)
        return m

    def OnTargetMouseDown(self, *args):
        if args[0] != uiconst.MOUSELEFT:
            return
        sm.GetService('target').OnMoveTarget(self)

    def OnTargetMouseUp(self, *args):
        sm.GetService('target').OnStopMoveTarget(args[0])

    def OnTargetMouseEnter(self, *args):
        sm.GetService('state').SetState(self.id, state.mouseOver, 1)
        if self._hoverThread is None:
            self._hoverThread = uthread.new(self._HoverThread)

    def OnTargetMouseExit(self, *args):
        sm.GetService('state').SetState(self.itemID, state.mouseOver, 0)
        self.KillHoverThread()

    @telemetry.ZONE_METHOD
    def UpdateData(self):
        ball = self.ball()
        if not ball:
            return
        obs = sm.GetService('target').IsObserving()
        if not obs:
            dist = ball.surfaceDist
            distanceInMeters = int(dist)
            if self.label != self.lastTextUsedForLabel:
                self.SetNameLabels(fullLabel=self.label)
                self.lastTextUsedForLabel = self.label
            if distanceInMeters != self.lastTextUsedDistance:
                self.sr.distanceLabel.text = '<center>' + util.FmtDist(dist)
                self.FadeText(self.sr.label2)
                self.lastTextUsedDistance = distanceInMeters
            if self.shipLabel != self.lastTextUsedForShipType:
                if self.shipLabel:
                    self.sr.shipLabel.display = True
                    self.sr.shipLabel.text = '<center>' + self.shipLabel
                    self.FadeText(self.sr.shipLabel)
                    self.lastTextUsedForShipType = self.shipLabel
                else:
                    self.sr.shipLabel.text = ''
                    self.sr.shipLabel.display = False
        elif self.sr.label != self.label:
            self.sr.label.text = self.label

    def SetNameLabels(self, fullLabel, *args):
        hintMarkupStart = ''
        hintMarkupEnd = ''
        localizedHintPos = fullLabel.find('<localized hint')
        if localizedHintPos >= 0:
            strippedLabel = uiutil.StripTags(fullLabel, stripOnly=['localized'])
            hintEndIndex = fullLabel.find('">')
            if hintEndIndex > 0:
                hintMarkupStart = fullLabel[localizedHintPos:hintEndIndex + 2]
                hintMarkupEnd = '</localized>'
        else:
            strippedLabel = fullLabel
        self.sr.label.text = strippedLabel
        indexAtMaxLenght = self.sr.label.GetIndexUnderPos(self.width)
        if indexAtMaxLenght[0] < len(strippedLabel):
            lastBreak = strippedLabel.rfind(' ', 0, indexAtMaxLenght[0])
            if lastBreak != -1:
                self.sr.label.text = strippedLabel[:lastBreak]
            self.sr.label2.text = '<center>' + hintMarkupStart + strippedLabel[lastBreak:].strip() + hintMarkupEnd
            self.FadeText(self.sr.label2)
            self.sr.label2.display = True
        else:
            self.sr.label2.text = ''
            self.sr.label2.display = False
        self.sr.label.text = '<center>' + hintMarkupStart + self.sr.label.text + hintMarkupEnd
        self.lastTextUsedForLabel = self.label

    def FadeText(self, textLabel, *args):
        maxFadeWidth = 10
        fadeEnd = self.width - maxFadeWidth
        textLabel.SetRightAlphaFade(fadeEnd=fadeEnd, maxFadeWidth=maxFadeWidth)

    def ActiveTarget(self, true):
        if self.destroyed:
            return
        targetSvc = sm.GetService('target')
        if true and not targetSvc.IsObserving():
            if not targetSvc.disableSpinnyReticule:
                self.sr.activeTarget.state = uiconst.UI_DISABLED
            self.sr.iconPar.opacity = 1.0
            self.circle.opacity = 0.5
        else:
            self.sr.iconPar.width = self.sr.iconPar.height = self.iconSize
            self.sr.activeTarget.state = uiconst.UI_HIDDEN
            self.sr.iconPar.opacity = 0.8
            self.circle.opacity = 0.25

    def OnDroneStateChange2(self, itemID, oldActivityState, activityState):
        michelle = sm.GetService('michelle')
        droneState = michelle.GetDroneState(itemID)
        if activityState in (const.entityCombat,
         const.entityEngage,
         const.entityMining,
         const.entitySalvaging):
            if droneState.targetID == self.id:
                self.drones[itemID] = droneState.typeID
            elif itemID in self.drones:
                del self.drones[itemID]
        elif itemID in self.drones:
            del self.drones[itemID]
        self.UpdateDrones()

    def OnDroneControlLost(self, droneID):
        if droneID in self.drones:
            del self.drones[droneID]
        self.UpdateDrones()

    def UpdateDrones(self):
        if not self.drones:
            self.RemoveWeapon('drones')
            return
        droneIconCont = self.GetWeapon('drones')
        if not droneIconCont:
            cont = uicls.Container(parent=self.sr.assigned, align=uiconst.RELATIVE, width=32, height=32, state=uiconst.UI_HIDDEN)
            icon = uicls.Sprite(parent=cont, align=uiconst.TOALL, width=0, height=0, state=uiconst.UI_NORMAL, texturePath='res:/UI/Texture/Icons/56_64_5.png')
            cont.sr.moduleID = 'drones'
            cont.icon = icon
            icon.sr.moduleID = 'drones'
            self.ArrangeWeapons()
        self.UpdateDroneHint()

    def UpdateDroneHint(self):
        dronesByTypeID = {}
        droneIcon = self.GetWeapon('drones')
        for droneID, droneTypeID in self.drones.iteritems():
            if droneTypeID not in dronesByTypeID:
                dronesByTypeID[droneTypeID] = 0
            dronesByTypeID[droneTypeID] += 1

        hintLines = []
        for droneTypeID, number in dronesByTypeID.iteritems():
            hintLines.append(localization.GetByLabel('UI/Inflight/Target/DroneHintLine', drone=droneTypeID, count=number))

        droneIcon.icon.hint = localization.GetByLabel('UI/Inflight/Target/DroneHintLabel', droneHintLines='<br>'.join(hintLines))


class TargetHealthBars(uicls.Container):
    __guid__ = 'uicls.TargetHealthBars'
    __notifyevents__ = ['OnDamageMessage', 'OnDamageMessages']
    default_name = 'targetHealthBars'
    default_width = 94
    default_height = 94
    default_align = uiconst.CENTER
    allHealthTexture = 'res:/UI/Texture/classes/Target/targetBackground.png'
    allHealthMinusShieldTexture = 'res:/UI/Texture/classes/Target/targetBackgroundNoShield.png'
    shieldTextureLeft = 'res:/UI/Texture/classes/Target/shieldLeft.png'
    shieldTextureRight = 'res:/UI/Texture/classes/Target/shieldRight.png'
    armorTextureLeft = 'res:/UI/Texture/classes/Target/armorLeft.png'
    armorTextureRight = 'res:/UI/Texture/classes/Target/armorRight.png'
    hullTextureLeft = 'res:/UI/Texture/classes/Target/hullLeft.png'
    hullTextureRight = 'res:/UI/Texture/classes/Target/hullRight.png'

    def ApplyAttributes(self, attributes):
        self.damageValuseForTooltip = {}
        uicls.Container.ApplyAttributes(self, attributes)
        self.itemID = attributes.itemID
        self.sr.damageTimer = base.AutoTimer(random.randint(750, 1000), self.UpdateDamage)
        self.width = attributes.get('size', self.default_width)
        self.height = attributes.get('size', self.default_height)
        self.shieldBar = self.AddHealthBar(name='shieldBar', texturePathLeft=self.shieldTextureLeft, texturePathRight=self.shieldTextureRight)
        self.armorBar = self.AddHealthBar(name='armorBar', texturePathLeft=self.armorTextureLeft, texturePathRight=self.armorTextureRight)
        self.hullBar = self.AddHealthBar(name='hullBar', texturePathLeft=self.hullTextureLeft, texturePathRight=self.hullTextureRight)
        self.healthBarBackground = uicls.Sprite(name='healthBarBackground', parent=self, width=self.width, height=self.height, texturePath=self.allHealthTexture, align=uiconst.CENTER, state=uiconst.UI_DISABLED)
        self.UpdateDamage()
        sm.RegisterNotify(self)

    def AddHealthBar(self, name, texturePathLeft, texturePathRight, *args):
        cont = uicls.Container(name=name, parent=self, width=self.width, height=self.height, align=uiconst.CENTER)
        leftBar = uicls.Sprite(name='%s_Left' % name, parent=cont, width=self.width, height=self.height, texturePath=texturePathLeft, textureSecondaryPath='res:/UI/Texture/classes/Target/gaugeColor.png', idx=0, blendMode=1, spriteEffect=trinity.TR2_SFX_MODULATE, state=uiconst.UI_DISABLED)
        leftBar.baseRotation = 0
        leftBar.rotationSecondary = leftBar.baseRotation
        rightBar = uicls.Sprite(name='%s_Right' % name, parent=cont, width=self.width, height=self.height, texturePath=texturePathRight, textureSecondaryPath='res:/UI/Texture/classes/Target/gaugeColor.png', idx=0, blendMode=1, spriteEffect=trinity.TR2_SFX_MODULATE, state=uiconst.UI_DISABLED)
        rightBar.baseRotation = -3 / 4.0 * math.pi
        rightBar.rotationSecondary = rightBar.baseRotation
        cont.leftBar = leftBar
        cont.rightBar = rightBar
        return cont

    def UpdateDamage(self):
        bp = sm.GetService('michelle').GetBallpark()
        if bp is None:
            self.sr.damageTimer = None
            return
        dmg = bp.GetDamageState(self.itemID)
        if dmg is not None:
            self.PrepareHint(dmg)
            self.SetDamage(dmg)

    def PrepareHint(self, state):
        self.damageValuseForTooltip[SHIELD] = state[0]
        self.damageValuseForTooltip[ARMOR] = state[1]
        self.damageValuseForTooltip[HULL] = state[2]

    def SetDamage(self, state, *args):
        visible = 0
        healthBars = [self.shieldBar, self.armorBar, self.hullBar]
        fullAnimationTime = 0.4
        for i, healthBar in enumerate(healthBars):
            if state[i] is None:
                healthBar.display = False
            else:
                healthState = state[i]
                lastState = getattr(healthBar, 'lastState', None)
                healthBar.lastState = healthState
                leftBar = healthBar.leftBar
                rightBar = healthBar.rightBar
                if lastState:
                    totalChange = healthState - lastState
                    animationTime = max(0.1, fullAnimationTime * abs(totalChange))
                else:
                    animationTime = None
                if healthState <= 0.5:
                    portionOfBar = (0.5 - healthState) / 0.5
                    rotation = leftBar.baseRotation + portionOfBar * 0.75 * math.pi
                    if lastState and lastState > 0.5:
                        below50Damage = lastState - 0.5
                        below50Percentage = float(below50Damage) / abs(totalChange)
                        if animationTime is None:
                            rightBar.rotationSecondary = 0.0
                            leftBar.rotationSecondary = rotation
                        else:
                            curvePoints = ([0, rightBar.rotationSecondary], [below50Percentage, 0.0])
                            uicore.animations.MorphScalar(rightBar, 'rotationSecondary', duration=animationTime, curveType=curvePoints)
                            curvePoints = ([0, leftBar.rotationSecondary], [below50Percentage, leftBar.rotationSecondary], [1.0, rotation])
                            uicore.animations.MorphScalar(leftBar, 'rotationSecondary', duration=animationTime, curveType=curvePoints)
                    else:
                        rightBar.rotationSecondary = 0
                        if animationTime is None:
                            leftBar.rotationSecondary = rotation
                        else:
                            uicore.animations.MorphScalar(leftBar, 'rotationSecondary', startVal=leftBar.rotationSecondary, endVal=rotation, duration=animationTime, curveType=uiconst.ANIM_LINEAR)
                else:
                    portionOfBar = (1 - healthState) / 0.5
                    rotation = rightBar.baseRotation + portionOfBar * 0.75 * math.pi
                    if lastState and lastState <= 0.5:
                        above50Damage = 0.5 - lastState
                        above50Percentage = float(above50Damage) / abs(totalChange)
                        if animationTime is None:
                            leftBar.rotationSecondary = leftBar.baseRotation - 0.02
                            rightBar.rotationSecondary = rotation
                        else:
                            curvePoints = ([0, leftBar.rotationSecondary], [above50Percentage, leftBar.baseRotation - 0.02])
                            uicore.animations.MorphScalar(leftBar, 'rotationSecondary', duration=animationTime, curveType=curvePoints)
                            curvePoints = ([0, rightBar.rotationSecondary], [above50Percentage, rightBar.rotationSecondary], [1.0, rotation])
                            uicore.animations.MorphScalar(rightBar, 'rotationSecondary', duration=animationTime, curveType=curvePoints)
                    else:
                        if animationTime is None:
                            rightBar.rotationSecondary = rotation
                        else:
                            uicore.animations.MorphScalar(rightBar, 'rotationSecondary', startVal=rightBar.rotationSecondary, endVal=rotation, duration=animationTime, curveType=uiconst.ANIM_LINEAR)
                        leftBar.rotationSecondary = leftBar.baseRotation - 0.02
                healthBar.display = True
                visible += 1

        if visible == 0:
            self.healthBarBackground.display = False
        else:
            if visible == 2:
                self.healthBarBackground.SetTexturePath(self.allHealthMinusShieldTexture)
            else:
                self.healthBarBackground.SetTexturePath(self.allHealthTexture)
            self.healthBarBackground.display = True

    def _OnClose(self, *args):
        self.sr.damageTimer = None

    def GetDamageHint(self, whichHealthBar, *args):
        return self.damageValuseForTooltip.get(whichHealthBar, 1.0)

    def OnDamageMessages(self, dmgmsgs):
        for msg in dmgmsgs:
            didBlink = self.OnDamageMessage(*msg[1:])
            if didBlink:
                break

    def OnDamageMessage(self, damageMessagesArgs):
        attackType = damageMessagesArgs.get('attackType', 'me')
        if attackType != 'me':
            return False
        damage = damageMessagesArgs.get('damage', 0)
        if damage == 0:
            return False
        target = damageMessagesArgs.get('target', None)
        if target is None:
            return False
        if isinstance(target, long):
            if target == self.itemID:
                self.DoBlink()
                return True
        if isinstance(target, basestring):
            targetID = damageMessagesArgs.get('target_ID', None)
            if targetID == self.itemID:
                self.DoBlink()
                return True
        return False

    def DoBlink(self, *args):
        uicore.animations.FadeTo(self, startVal=1.3, endVal=1.0, duration=0.75, loops=1, curveType=uiconst.ANIM_OVERSHOT)