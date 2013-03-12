#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/crimewatch/crimewatchTimers.py
import uicls
import uiconst
import uiutil
import collections
import blue
import uthread
import math
import trinity
import localization
import util
import state
import copy
from math import pi
from crimewatchConst import Colors
ALPHA_EMPTY = 0.2
BLINK_BEFORE_DONE_TIME = const.SEC * 5
HINT_FRAME_COLOR = (1.0,
 1.0,
 1.0,
 0.25)
HINT_BACKGROUND_COLOR = (0,
 0,
 0,
 0.85)
MAX_ENGAGED_VISIBLE = 10
TimerData = collections.namedtuple('TimerData', 'icon smallIcon color tooltip maxTimeout resetAudioEvent endingAudioEvent timerFunc')

def FmtTime(timeLeft):
    if timeLeft > 0:
        seconds = timeLeft / const.SEC
        minutes = seconds / 60
        seconds = seconds % 60
    else:
        minutes = 0
        seconds = 0
    return '%02d:%02d' % (max(0, minutes), max(0, seconds))


class TimerType():
    __guid__ = 'crimewatchTimers.TimerType'
    Weapons = 0
    Npc = 1
    Pvp = 2
    Suspect = 3
    Criminal = 4
    Engagement = 5


CRIMEWATCH_TIMER_DATA = [TimerData('res:/UI/Texture/Crimewatch/Crimewatch_Locked.png', 'res:/UI/Texture/Crimewatch/Crimewatch_Locked_Small.png', Colors.Red.GetRGBA(), 'UI/Crimewatch/Timers/WeaponsTimerTooltip', const.weaponsTimerTimeout, 'wise:/crimewatch_weapons_timer_play', 'wise:/crimewatch_weapons_timer_end_play', blue.os.GetSimTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_Combat.png', 'res:/UI/Texture/Crimewatch/Crimewatch_Combat_Small.png', Colors.Yellow.GetRGBA(), 'UI/Crimewatch/Timers/PveTimerTooltip', const.npcTimerTimeout, 'wise:/crimewatch_log_off_timer_new_play', 'wise:/crimewatch_log_off_timer_end_play', blue.os.GetSimTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_Combat.png', 'res:/UI/Texture/Crimewatch/Crimewatch_Combat_Small.png', Colors.Red.GetRGBA(), 'UI/Crimewatch/Timers/PvpTimerTooltiip', const.pvpTimerTimeout, 'wise:/crimewatch_log_off_timer_new_play', 'wise:/crimewatch_log_off_timer_end_play', blue.os.GetSimTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal.png', 'res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal_Small.png', Colors.Suspect.GetRGBA(), 'UI/Crimewatch/Timers/SuspectTimerTooltip', const.criminalTimerTimeout, 'wise:/crimewatch_criminal_timer_play', 'wise:/crimewatch_criminal_timer_end_play', blue.os.GetSimTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal.png', 'res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal_Small.png', Colors.Criminal.GetRGBA(), 'UI/Crimewatch/Timers/CriminalTimerTooltip', const.criminalTimerTimeout, 'wise:/crimewatch_criminal_timer_play', 'wise:/crimewatch_criminal_timer_end_play', blue.os.GetSimTime),
 TimerData('res:/UI/Texture/Crimewatch/Crimewatch_LimitedEngagement.png', None, Colors.Engagement.GetRGBA(), 'UI/Crimewatch/Timers/LimitedEngagementTimerTooltip', const.crimewatchEngagementDuration, 'wise:/crimewatch_engagement_timer_play', 'wise:/crimewatch_engagement_timer_end_play', blue.os.GetWallclockTime)]

class TimerHint(uicls.Container):
    __guid__ = 'crimewatchTimers.TimerHint'
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_bgColor = HINT_BACKGROUND_COLOR
    default_width = 300
    default_height = 48
    TIME_WIDTH = 58
    TEXT_WIDTH = 242

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.parentTimer = attributes.get('parentTimer')
        self.timerData = attributes.get('timerData')
        self.GetTime = self.timerData.timerFunc
        uicls.Frame(pgParent=self, state=uiconst.UI_DISABLED, color=HINT_FRAME_COLOR)
        leftCont = uicls.Container(parent=self, align=uiconst.TOLEFT, width=self.TIME_WIDTH)
        rightCont = uicls.Container(parent=self, align=uiconst.TOALL)
        self.time = uicls.Label(parent=leftCont, name='counter', text=str(int(self.timerData.maxTimeout / const.SEC)), fontsize=20, bold=False, align=uiconst.CENTERLEFT, color=self.timerData.color, left=2 * const.defaultPadding)
        self.text = uicls.EveLabelSmall(left=const.defaultPadding, parent=rightCont, name='timer description', text=localization.GetByLabel(self.timerData.tooltip), align=uiconst.CENTERLEFT, width=self.TEXT_WIDTH - 2 * const.defaultPadding)
        self.height = self.text.actualTextHeight + 2 * const.defaultPadding
        self.activeBlink = None
        self.doUpdates = True
        uthread.new(self.UpdateTimer)
        self.opacity = 0.0
        uicore.animations.FadeIn(self, duration=0.5)

    def _OnClose(self):
        self.doUpdates = False
        self.parentTimer.timerHint = None

    def UpdateTimer(self):
        startTime = self.GetTime()
        while self.doUpdates:
            timeNow = self.GetTime()
            if self.parentTimer.expiryTime is not None:
                timeLeft = max(0, self.parentTimer.expiryTime - timeNow)
                self.time.text = FmtTime(timeLeft)
                if timeLeft == 0:
                    self.doUpdates = False
                if self.activeBlink is not None:
                    self.activeBlink.Stop()
                    self.time.opacity = 1.0
                    self.activeBlink = None
            else:
                self.time.text = FmtTime(self.timerData.maxTimeout)
                if self.activeBlink is None:
                    self.activeBlink = uicore.animations.BlinkOut(self.time, duration=1.0, loops=uiconst.ANIM_REPEAT)
            if startTime + const.SEC < timeNow:
                if not (uicore.uilib.mouseOver is self or uiutil.IsUnder(uicore.uilib.mouseOver, self.parentTimer)):
                    self.doUpdates = False
            if self.doUpdates:
                blue.pyos.synchro.SleepWallclock(200)

        uicore.animations.FadeOut(self, sleep=True)
        self.Close()


class EngagementEntry(uicls.Container):
    __guid__ = 'crimewatchTimers.EngagementEntry'
    default_align = uiconst.TOTOP
    default_height = 32
    default_padBottom = 1
    default_state = uiconst.UI_NORMAL
    isDragObject = True
    __notifyevents__ = ['OnCrimewatchEngagementUpdated']

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.charID = attributes.get('charID')
        self.timeout = attributes.get('timeout')
        self.isDragObject = True
        self.itemID = self.charID
        self.info = cfg.eveowners.Get(self.charID)
        self.activeBlink = None
        self.highlight = uicls.Fill(bgParent=self, color=(1, 1, 1, 0.1), state=uiconst.UI_HIDDEN)
        leftCont = uicls.Container(parent=self, align=uiconst.TOLEFT, width=54)
        self.time = uicls.Label(parent=leftCont, name='counter', text='', fontsize=16, bold=False, align=uiconst.CENTERLEFT, color=Colors.Engagement.GetRGBA(), left=2 * const.defaultPadding)
        self.portrait = uicls.Sprite(parent=self, pos=(50, 0, 32, 32), state=uiconst.UI_DISABLED)
        uicls.EveLabelSmall(parent=self, name='name', text=self.info.ownerName, align=uiconst.TOPLEFT, top=1, left=96)
        self.corpText = uicls.EveLabelSmall(parent=self, name='corporation', text='', align=uiconst.TOPLEFT, top=17, left=96)
        self.stateFlag = uicls.StateFlag(parent=self, align=uiconst.TOPRIGHT, pos=(13, 4, 9, 9))
        self.LoadData()
        sm.RegisterNotify(self)

    def LoadData(self):
        self.SetTimer()
        sm.GetService('photo').GetPortrait(self.charID, 32, self.portrait)
        uthread.new(self.LazyLoadData)

    def OnMouseEnter(self, *args):
        self.highlight.display = True

    def OnMouseExit(self, *args):
        self.highlight.display = False

    def SetTimer(self):
        if self.timeout == const.crimewatchEngagementTimeoutOngoing:
            self.time.text = FmtTime(const.crimewatchEngagementDuration)
            if self.activeBlink is None:
                self.activeBlink = uicore.animations.BlinkOut(self.time, duration=1.0, loops=uiconst.ANIM_REPEAT)
        else:
            self.time.text = FmtTime(self.timeout - blue.os.GetWallclockTime())
            if self.activeBlink is not None:
                self.activeBlink.Stop()
                self.activeBlink = None
                self.time.opacity = 1.0

    def LazyLoadData(self):
        slimItem = sm.GetService('crimewatchSvc').GetSlimItemDataForCharID(self.charID)
        if slimItem is not None:
            self.corpText.text = cfg.eveowners.Get(slimItem.corpID).ownerName
            flagCode = sm.GetService('state').CheckFilteredFlagState(slimItem, (state.flagLimitedEngagement,))
            self.stateFlag.LoadFromFlag(flagCode, showHint=True)
            self.slimItem = copy.copy(slimItem)

    def OnClick(self):
        sm.GetService('info').ShowInfo(typeID=self.info.typeID, itemID=self.charID)

    def GetDragData(self, *args):
        if self and not self.destroyed:
            fakeNode = util.KeyVal()
            fakeNode.charID = self.charID
            fakeNode.typeID = self.info.typeID
            fakeNode.info = self.info
            fakeNode.itemID = self.itemID
            fakeNode.__guid__ = 'listentry.User'
            return [fakeNode]
        else:
            return []

    def GetMenu(self):
        if self.slimItem:
            if self.slimItem.itemID:
                return sm.GetService('menu').CelestialMenu(self.slimItem.itemID)
            else:
                return sm.GetService('menu').GetMenuFormItemIDTypeID(self.itemID, self.info.typeID)

    def OnCrimewatchEngagementUpdated(self, otherCharId, timeout):
        if otherCharId == self.charID:
            if timeout is None:
                uicore.animations.FadeOut(self, duration=0.5, sleep=True)
                self.Close()
                sm.ScatterEvent('OnEngagementTimerHintResize')
            else:
                self.timeout = timeout


class EngagementTimerHint(uicls.ContainerAutoSize):
    __guid__ = 'crimewatchTimers.EngagementTimerHint'
    __notifyevents__ = ['OnEngagementTimerHintResize', 'OnCrimewatchEngagementUpdated']
    default_name = 'EngagementTimerHint'
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_bgColor = HINT_BACKGROUND_COLOR
    default_width = 240

    def ApplyAttributes(self, attributes):
        uicls.ContainerAutoSize.ApplyAttributes(self, attributes)
        self.parentTimer = attributes.get('parentTimer')
        self.timerData = attributes.get('timerData')
        self.GetTime = self.timerData.timerFunc
        self.doUpdates = True
        uicls.Frame(bgParent=self, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.25))
        self.mainText = uicls.EveLabelMedium(parent=self, align=uiconst.TOTOP, text='', padding=(8, 8, 8, 8), state=uiconst.UI_DISABLED)
        self.engagementsContainer = uicls.ScrollContainer(parent=self, align=uiconst.TOTOP)
        self.LoadData()
        uthread.new(self.UpdateTimer)
        sm.RegisterNotify(self)

    def OnEngagementTimerHintResize(self):
        self.UpdateScrollHeight()

    def SortKey(self, entry):
        if entry[0] == const.crimewatchEngagementTimeoutOngoing:
            return blue.os.GetWallclockTime()

    def LoadData(self):
        engagements = sm.GetService('crimewatchSvc').GetMyEngagements()
        cfg.eveowners.Prime(engagements.keys())
        engagementList = [ (timeout, charID) for charID, timeout in engagements.iteritems() ]
        engagementList.sort(key=self.SortKey)
        for timeout, charID in engagementList:
            self.AddEntry(charID, timeout)

        self.mainText.text = localization.GetByLabel('UI/Crimewatch/Timers/EngagementTooltipHintHeader', count=len(engagementList))
        self.UpdateScrollHeight()

    def AddEntry(self, charID, timeout):
        EngagementEntry(parent=self.engagementsContainer, charID=charID, timeout=timeout)

    def UpdateScrollHeight(self):
        self.engagementsContainer.height = sum((x.height + x.padBottom for x in self.engagementsContainer.mainCont.children[:MAX_ENGAGED_VISIBLE]))

    def UpdateTimer(self):
        startTime = self.GetTime()
        count = 0
        while self.doUpdates:
            timeNow = self.GetTime()
            for child in self.engagementsContainer.mainCont.children[:]:
                child.SetTimer()

            if startTime + const.SEC < timeNow:
                if not (uicore.uilib.mouseOver is self or uiutil.IsUnder(uicore.uilib.mouseOver, self) or uiutil.IsUnder(uicore.uilib.mouseOver, self.parentTimer)):
                    if count > 2:
                        self.doUpdates = False
                    else:
                        count += 1
                else:
                    count = 0
            if self.doUpdates:
                blue.pyos.synchro.SleepWallclock(200)

        uicore.animations.FadeOut(self, sleep=True)
        self.Close()

    def _OnClose(self):
        self.doUpdates = False
        self.parentTimer.timerHint = None

    def OnCrimewatchEngagementUpdated(self, otherCharId, timeout):
        for child in self.engagementsContainer.mainCont.children[:]:
            if otherCharId == child.charID:
                break
        else:
            self.AddEntry(otherCharId, timeout)
            self.UpdateScrollHeight()


class Timer(uicls.Container):
    __guid__ = 'crimewatchTimers.Timer'
    default_width = 46
    default_align = uiconst.TOLEFT
    default_hintClass = TimerHint

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.hintClass = attributes.get('hintClass', self.default_hintClass)
        self.state = uiconst.UI_PICKCHILDREN
        self.timerHint = None
        self.showHint = False
        self.expiryTime = None
        self.iconBlink = None
        self.rewind = False
        self.ratio = 0.0
        self.counterText = None
        self.animationThread = None
        self.timerData = CRIMEWATCH_TIMER_DATA[attributes.Get('timerType')]
        self.GetTime = self.timerData.timerFunc
        self.activeAnimationCurves = None
        self.content = uicls.Transform(parent=self, name='content', align=uiconst.TOPLEFT, pos=(0, 0, 32, 32), state=uiconst.UI_NORMAL)
        self.circleSprite = uicls.Sprite(name='icon', parent=self.content, pos=(0, 0, 32, 32), texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerCircle.png', color=self.timerData.color, state=uiconst.UI_DISABLED, align=uiconst.CENTER, opacity=ALPHA_EMPTY)
        self.content.OnMouseEnter = self.OnMouseEnter
        self.iconTransform = uicls.Transform(parent=self.content, name='iconTransform', align=uiconst.CENTER, width=16, height=16, state=uiconst.UI_DISABLED)
        self.icon = uicls.Sprite(name='icon', parent=self.iconTransform, pos=(0, 0, 16, 16), texturePath=self.timerData.icon, color=self.timerData.color, state=uiconst.UI_DISABLED, align=uiconst.CENTER)
        self.halfCircleSprite = uicls.Sprite(name='half_circle', parent=self.content, width=32, height=32, texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerHalfCircle.png', color=self.timerData.color, state=uiconst.UI_DISABLED)
        self.clipContainer = uicls.Container(name='clipper', parent=self.content, width=16, align=uiconst.TOLEFT, clipChildren=True, state=uiconst.UI_DISABLED)
        self.cycleContainer = uicls.Transform(name='cycle_container', parent=self.clipContainer, width=32, height=32)
        self.cycleSprite = uicls.Sprite(name='cycle_half_circle', parent=self.cycleContainer, width=32, height=32, rotation=pi, texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerHalfCircle.png', color=self.timerData.color, state=uiconst.UI_DISABLED)
        self.pointerContainer = uicls.Transform(name='pointer_container', parent=self.content, width=32, height=32, idx=0)
        self.pointerClipper = uicls.Container(parent=self.pointerContainer, pos=(9, -10, 15, 13), clipChildren=True, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        self.pointerSprite = uicls.Sprite(name='cycle_pointer', parent=self.pointerClipper, pos=(0, 0, 15, 19), texturePath='res:/UI/Texture/Crimewatch/Crimewatch_TimerPoint_WithShadow.png', color=self.timerData.color, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        self.iconTransform.scalingCenter = (0.5, 0.5)
        uicore.animations.Tr2DScaleTo(self.iconTransform, startScale=(0.8, 0.8), endScale=(1.0, 1.0), duration=0.75, curveType=uiconst.ANIM_OVERSHOT)

    def SetTimerType(self, timerType):
        self.timerData = CRIMEWATCH_TIMER_DATA[timerType]
        r, g, b, a = self.timerData.color
        self.icon.color.SetRGB(r, g, b, a)
        self.circleSprite.color.SetRGB(r, g, b, ALPHA_EMPTY)
        self.halfCircleSprite.SetRGB(r, g, b, a)
        self.cycleSprite.color.SetRGB(r, g, b, a)
        self.pointerSprite.color.SetRGB(r, g, b, a)

    def SetRatio(self, ratio):
        self.ratio = min(1.0, max(0.0, ratio))
        if self.ratio > 0.5:
            self.clipContainer.SetAlign(uiconst.TORIGHT)
            self.cycleContainer.left = -16
            self.halfCircleSprite.display = True
        else:
            self.clipContainer.SetAlign(uiconst.TOLEFT)
            self.cycleContainer.left = 0
            self.halfCircleSprite.display = False
        rotation = min(pi * 2, 2 * pi * self.ratio)
        self.pointerContainer.rotation = rotation
        self.cycleContainer.rotation = rotation

    def SetExpiryTime(self, expiryTime, doAlert):
        self.Reset(expiryTime, doAlert)
        self.expiryTime = expiryTime
        if expiryTime is None:
            self.PlayActiveAnimation()
        else:
            self.animationThread = uthread.new(self.Animate_Thread)

    def Reset(self, resetTo, doAlert):
        if self.animationThread is not None:
            self.animationThread.kill()
        uthread.new(self.Rewind_Thread, resetTo, doAlert)

    def Rewind_Thread(self, resetTo, doAlert):
        if self.rewind:
            return
        if doAlert and self.timerData.resetAudioEvent is not None:
            sm.GetService('audio').SendUIEvent(self.timerData.resetAudioEvent)
        self.rewind = True
        ratio = self.ratio
        startTime = self.GetTime()
        distance = 1 - ratio
        cycleSpeed = float(distance * 500)
        while not self.destroyed and self.ratio < (self.GetRatio(resetTo - self.GetTime()) if resetTo is not None else 1.0):
            elapsedTime = blue.os.TimeDiffInMs(startTime, self.GetTime())
            toAdd = elapsedTime / cycleSpeed
            self.SetRatio(ratio + toAdd)
            blue.pyos.synchro.SleepWallclock(25)

        self.rewind = False

    def FlipFlop(self, sprite, duration = 1.0, startValue = 0.0, endValue = 1.0, loops = 5):
        curve = trinity.Tr2ScalarCurve()
        curve.length = duration
        curve.interpolation = trinity.TR2CURVE_LINEAR
        curve.startValue = startValue
        curve.AddKey(0.01 * duration, endValue)
        curve.AddKey(0.5 * duration, endValue)
        curve.AddKey(0.51 * duration, startValue)
        curve.endValue = startValue
        return uicore.animations._Play(curve, sprite, 'opacity', loops, None, False)

    def GetRatio(self, timeLeft):
        ratio = timeLeft / float(self.timerData.maxTimeout)
        ratio = min(1.0, max(0.0, ratio))
        return ratio

    def Animate_Thread(self):
        self.StopActiveAnimation()
        while not self.destroyed and self.expiryTime is not None:
            if not self.rewind:
                if self.ratio <= 0.0:
                    break
                timeLeft = self.expiryTime - self.GetTime()
                ratio = self.GetRatio(timeLeft)
                self.SetRatio(ratio)
                if timeLeft < BLINK_BEFORE_DONE_TIME:
                    self.PlayIconBlink()
                else:
                    self.StopIconBlink()
            blue.pyos.synchro.SleepWallclock(50)

    def PlayIconBlink(self):
        if self.iconBlink is None:
            self.iconBlink = self.FlipFlop(self.icon, startValue=1.0, endValue=0.0)
            if self.timerData.endingAudioEvent:
                sm.GetService('audio').SendUIEvent(self.timerData.endingAudioEvent)

    def StopIconBlink(self):
        if self.iconBlink is not None:
            self.iconBlink.Stop()
            self.iconBlink = None
            self.icon.opacity = 1.0

    def EndAnimation(self):
        self.SetRatio(0.0)
        uicore.animations.MoveOutBottom(self.pointerSprite, amount=9, duration=0.3, sleep=False)
        self.content.scalingCenter = (0.5, 0.5)
        uicore.animations.Tr2DScaleTo(self.content, startScale=(1.0, 1.0), endScale=(0.8, 0.8), duration=0.4, sleep=True)

    def OnMouseEnter(self, *args):
        uthread.new(self.ShowHide)

    def ShowHide(self):
        blue.pyos.synchro.SleepWallclock(250)
        if uicore.uilib.mouseOver is self.content:
            self.showHint = True
            if self.timerHint is None:
                left, top, width, height = self.content.GetAbsolute()
                self.timerHint = self.hintClass(parent=uicore.layer.abovemain, left=left + 16, top=top + 16, timerData=self.timerData, parentTimer=self)

    def ShiftLeft(self):
        uicore.animations.MoveInFromRight(self, self.width, duration=0.5)

    def SetCounter(self, count):
        if count is None or count <= 1:
            if self.counterText is not None:
                self.counterText.Close()
                self.counterText = None
        else:
            if self.counterText is None:
                self.counterText = uicls.EveHeaderLarge(parent=self.content, name='counter', left=34, top=-2, bold=True, color=self.timerData.color)
            text = str(count) if count < 10 else '9+'
            self.counterText.text = text

    def PlayActiveAnimation(self):
        self.activeAnimationCurves = ((self.halfCircleSprite, self.FlipFlop(self.halfCircleSprite, startValue=1.0, endValue=0.75, duration=1.0, loops=uiconst.ANIM_REPEAT)), (self.cycleSprite, self.FlipFlop(self.cycleSprite, startValue=1.0, endValue=0.75, duration=1.0, loops=uiconst.ANIM_REPEAT)), (self.pointerSprite, self.FlipFlop(self.pointerSprite, startValue=1.0, endValue=0.75, duration=1.0, loops=uiconst.ANIM_REPEAT)))

    def StopActiveAnimation(self):
        if self.activeAnimationCurves is not None:
            for sprite, animCurve in self.activeAnimationCurves:
                animCurve.Stop()
                sprite.opacity = 1.0

            self.activeAnimationCurves = None


class TimerContainer(uicls.Container):
    __guid__ = 'crimewatchTimers.TimerContainer'
    __notifyevents__ = ['OnWeaponsTimerUpdate',
     'OnPvpTimerUpdate',
     'OnCriminalTimerUpdate',
     'OnNpcTimerUpdate',
     'OnCombatTimersUpdated',
     'OnCrimewatchEngagementUpdated']
    default_name = 'TimerContainer'
    default_height = 32
    default_width = 96 + 16
    default_padBottom = 6
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.weaponsTimer = None
        self.npcTimer = None
        self.pvpTimer = None
        self.criminalTimer = None
        self.engagementTimer = None
        self.crimewatchSvc = sm.GetService('crimewatchSvc')
        uthread.new(self.OnCombatTimersUpdated)

    def OnCombatTimersUpdated(self):
        self.OnWeaponsTimerUpdate(doAlert=False, *self.crimewatchSvc.GetWeaponsTimer())
        self.OnNpcTimerUpdate(doAlert=False, *self.crimewatchSvc.GetNpcTimer())
        self.OnPvpTimerUpdate(doAlert=False, *self.crimewatchSvc.GetPvpTimer())
        self.OnCriminalTimerUpdate(doAlert=False, *self.crimewatchSvc.GetCriminalTimer())
        self.OnCrimewatchEngagementUpdated(None, None, doAlert=False)

    def OnWeaponsTimerUpdate(self, state, expiryTime, doAlert = True):
        if state in (const.weaponsTimerStateActive, const.weaponsTimerStateInherited):
            timer = self.GetTimer(TimerType.Weapons)
            timer.SetExpiryTime(None, doAlert)
        elif expiryTime is not None:
            timer = self.GetTimer(TimerType.Weapons)
            timer.SetExpiryTime(expiryTime, doAlert)
        else:
            self.DeleteTimer(TimerType.Weapons)

    def OnNpcTimerUpdate(self, state, expiryTime, doAlert = True):
        if state in (const.npcTimerStateActive, const.npcTimerStateInherited):
            timer = self.GetTimer(TimerType.Npc)
            timer.SetExpiryTime(None, doAlert)
        elif expiryTime is not None:
            timer = self.GetTimer(TimerType.Npc)
            timer.SetExpiryTime(expiryTime, doAlert)
        else:
            self.DeleteTimer(TimerType.Npc)

    def OnPvpTimerUpdate(self, state, expiryTime, doAlert = True):
        if state in (const.pvpTimerStateActive, const.pvpTimerStateInherited):
            timer = self.GetTimer(TimerType.Pvp)
            timer.SetExpiryTime(None, doAlert)
        elif expiryTime is not None:
            timer = self.GetTimer(TimerType.Pvp)
            timer.SetExpiryTime(expiryTime, doAlert)
        else:
            self.DeleteTimer(TimerType.Pvp)

    def OnCriminalTimerUpdate(self, state, expiryTime, doAlert = True):
        if state in (const.criminalTimerStateActiveSuspect, const.criminalTimerStateInheritedSuspect):
            timer = self.GetTimer(TimerType.Suspect)
            timer.SetExpiryTime(None, doAlert)
        elif state == const.criminalTimerStateTimerSuspect and expiryTime is not None:
            timer = self.GetTimer(TimerType.Suspect)
            timer.SetExpiryTime(expiryTime, doAlert)
        elif state in (const.criminalTimerStateActiveCriminal, const.criminalTimerStateInheritedCriminal):
            timer = self.GetTimer(TimerType.Criminal)
            timer.SetExpiryTime(None, doAlert)
        elif state == const.criminalTimerStateTimerCriminal and expiryTime is not None:
            timer = self.GetTimer(TimerType.Criminal)
            timer.SetExpiryTime(expiryTime, doAlert)
        else:
            self.DeleteTimer(TimerType.Suspect)

    def OnCrimewatchEngagementUpdated(self, otherCharId, timeout, doAlert = True):
        engagements = self.crimewatchSvc.GetMyEngagements()
        if len(engagements) == 0:
            self.DeleteTimer(TimerType.Engagement)
        else:
            timer = self.GetTimer(TimerType.Engagement)
            onGoingEngagement = any((_timeout == const.crimewatchEngagementTimeoutOngoing for _timeout in engagements.itervalues()))
            if onGoingEngagement:
                timeout = None
            else:
                timeout = max((_timeout for _timeout in engagements.itervalues()))
            timer.SetExpiryTime(timeout, doAlert)
            timer.SetCounter(len(engagements))

    def DeleteTimer(self, timerType):
        idx = None
        if timerType == TimerType.Weapons:
            if self.weaponsTimer is not None:
                idx = self.children.index(self.weaponsTimer)
                self.weaponsTimer.EndAnimation()
                self.weaponsTimer.Close()
                self.weaponsTimer = None
        elif timerType == TimerType.Npc:
            if self.npcTimer is not None:
                idx = self.children.index(self.npcTimer)
                self.npcTimer.EndAnimation()
                self.npcTimer.Close()
                self.npcTimer = None
        elif timerType == TimerType.Pvp:
            if self.pvpTimer is not None:
                idx = self.children.index(self.pvpTimer)
                self.pvpTimer.EndAnimation()
                self.pvpTimer.Close()
                self.pvpTimer = None
        elif timerType in (TimerType.Suspect, TimerType.Criminal):
            if self.criminalTimer is not None:
                idx = self.children.index(self.criminalTimer)
                self.criminalTimer.EndAnimation()
                self.criminalTimer.Close()
                self.criminalTimer = None
        elif timerType == TimerType.Engagement:
            if self.engagementTimer is not None:
                idx = self.children.index(self.engagementTimer)
                self.engagementTimer.EndAnimation()
                self.engagementTimer.Close()
                self.engagementTimer = None
        if idx is not None:
            for timer in self.children[idx:idx + 1]:
                timer.ShiftLeft()

    def GetTimer(self, timerType):
        if timerType == TimerType.Weapons:
            if self.weaponsTimer is None:
                self.weaponsTimer = Timer(parent=self, name='WeaponsTimer', timerType=TimerType.Weapons)
            timer = self.weaponsTimer
        elif timerType == TimerType.Npc:
            if self.npcTimer is None:
                self.npcTimer = Timer(parent=self, name='NpcTimer', timerType=TimerType.Npc)
            timer = self.npcTimer
        elif timerType == TimerType.Pvp:
            if self.pvpTimer is None:
                self.pvpTimer = Timer(parent=self, name='PvpTimer', timerType=TimerType.Pvp)
            timer = self.pvpTimer
        elif timerType == TimerType.Suspect:
            if self.criminalTimer is None:
                self.criminalTimer = Timer(parent=self, name='CriminalTimer', timerType=TimerType.Suspect)
            timer = self.criminalTimer
        elif timerType == TimerType.Criminal:
            if self.criminalTimer is None:
                self.criminalTimer = Timer(parent=self, name='CriminalTimer', timerType=TimerType.Criminal)
            else:
                self.criminalTimer.SetTimerType(TimerType.Criminal)
            timer = self.criminalTimer
        elif timerType == TimerType.Engagement:
            if self.engagementTimer is None:
                self.engagementTimer = Timer(parent=self, name='EngagementTimer', timerType=TimerType.Engagement, hintClass=EngagementTimerHint)
            timer = self.engagementTimer
        return timer