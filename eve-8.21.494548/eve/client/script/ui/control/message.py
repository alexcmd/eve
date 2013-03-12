#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/control/message.py
import blue
import base
import uicls
import uiutil
import uiconst
import uthread
import math
import localization
import collections

class MessageParentClass(uicls.Container):
    __guid__ = 'uicls.MessageParentClass'
    __notifyevents__ = ['OnEndChangeDevice', 'OnSessionChanged']

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.layerOffset = uicore.layer.abovemain.absoluteLeft
        self.myLayer = uicore.layer.abovemain
        self.minTop = 0
        config = settings.char.ui.Get(self.configName, self.defaultConfig)
        if not isinstance(config, tuple) or len(config) != 4:
            config = self.defaultConfig
        self.SetAllAlignments(config)
        self.inDragMode = False
        sm.RegisterNotify(self)

    def SetAllAlignments(self, config, *args):
        align, textAlign, left, topOffset = config
        self.SetAlign(align)
        self.currentTextAlignment = textAlign
        self.left = left
        self.topOffset = topOffset

    def EnterDragMode(self, *args):
        self.dragFill = uicls.Sprite(parent=self, name='dragFill', texturePath='res:/UI/Texture/classes/Neocom/buttonDown.png', state=uiconst.UI_DISABLED, align=uiconst.TOALL, idx=2)
        func = sm.GetService('logger').MoveNotifications
        self.exitMoveModeBtn = uicls.ImageButton(name='close', parent=self, align=uiconst.TOPRIGHT, state=uiconst.UI_NORMAL, pos=(0, 0, 16, 16), idleIcon='ui_38_16_220', mouseoverIcon='ui_38_16_220', mousedownIcon='ui_38_16_220', onclick=lambda : func(False), expandonleft=True, hint=localization.GetByLabel('UI/Accessories/Log/ExitMessageMovingMode'), idx=0)
        self.state = uiconst.UI_NORMAL
        self.inDragMode = True
        uicore.animations.SpSwoopBlink(self.dragFill, rotation=math.pi - 0.5, duration=1.5, loops=10)

    def BeginDrag(self, *args):
        layerOffset = self.layerOffset
        mouseX = uicore.uilib.x - layerOffset
        self.lastx = mouseX
        fromTop = self.absoluteTop - uicore.uilib.y
        while not self.destroyed and getattr(self, 'dragging', 0):
            self.CalculateRepositioning(fromTop)
            blue.pyos.synchro.SleepWallclock(1)

    def CalculateRepositioning(self, fromTop, *args):
        mouseX = uicore.uilib.x - self.layerOffset
        xDiff = mouseX - self.lastx
        uicore.uilib.SetCursor(uiconst.UICURSOR_NONE)
        self.top = max(self.minTop, uicore.uilib.y + fromTop)
        self.topOffset = self.top + self.height
        self.DoAlignment(xDiff)
        self.lastx = mouseX

    def DoAlignment(self, xDiff = 0, *args):
        layerOffset = self.layerOffset
        fullWidth, fullHeight = self.myLayer.GetAbsoluteSize()
        fromRightBorder = fullWidth - (self.absoluteRight - layerOffset)
        alignmentMode = settings.user.ui.Get(self.settingNameAlign, 'auto')
        autoAlign = alignmentMode == 'auto'
        if autoAlign and fromRightBorder < 200 or alignmentMode == 'right':
            if self.align != uiconst.TOPRIGHT:
                self.SetAlign(uiconst.TOPRIGHT)
                self.left = fromRightBorder
            else:
                self.left = max(0, self.left - xDiff)
            self.left = min(self.left, fullWidth - 100)
            self.left = max(self.left, 0)
            self.SetTextAlignmentIfNeeded('right')
        elif autoAlign and self.absoluteLeft - layerOffset < 200 or alignmentMode == 'left':
            if self.align != uiconst.TOPLEFT:
                left = self.absoluteLeft - layerOffset
                self.SetAlign(uiconst.TOPLEFT)
                self.left = left
            else:
                self.left = max(0, self.left + xDiff)
            self.left = min(self.left, fullWidth - 100)
            self.left = max(self.left, 0)
            self.SetTextAlignmentIfNeeded('left')
        else:
            if self.align != uiconst.CENTERTOP:
                self.left = self.absoluteLeft - layerOffset + self.width / 2 - fullWidth / 2
                self.SetAlign(uiconst.CENTERTOP)
            else:
                self.left = self.left + xDiff
            self.left = max(self.left, -(fullWidth - 100) / 2)
            self.left = min(self.left, (fullWidth - 100) / 2)
            self.SetTextAlignmentIfNeeded('center')

    def OnMouseDown(self, *args):
        self.dragging = 1
        uthread.new(self.BeginDrag)

    def OnMouseUp(self, *args):
        self.dragging = 0

    def ExitDragMode(self, *args):
        self.dragging = 0
        dragFill = getattr(self, 'dragFill', None)
        if dragFill:
            dragFill.Close()
        fakeText = getattr(self, 'fakeText', None)
        if fakeText:
            fakeText.Close()
        exitMoveModeBtn = getattr(self, 'exitMoveModeBtn', None)
        if exitMoveModeBtn:
            exitMoveModeBtn.Close()
        self.SaveSettings()
        self.inDragMode = False

    def SetTextAlignmentIfNeeded(self, alignment, *args):
        pass

    def SaveSettings(self, *args):
        pass

    def OnEndChangeDevice(self, change, *args):
        self.defaultConfig = self.GetDefaultAlignmentValues()
        if settings.char.ui.Get(self.configName, None) is None:
            self.SetAllAlignments(self.defaultConfig)

    def OnSessionChanged(self, isRemote, sess, change):
        pass


class Message(MessageParentClass):
    __guid__ = 'uicls.Message'

    def ApplyAttributes(self, attributes):
        self.configName = 'generalMessages_config'
        self.settingNameAlign = 'generalnotifictions_alignment'
        self.defaultConfig = self.GetDefaultAlignmentValues()
        uicls.MessageParentClass.ApplyAttributes(self, attributes)
        self.layerOffset = 0
        self.myLayer = uicore.layer.abovemain
        self.minTop = 0
        self.scope = 'station_inflight'
        self.message = None
        self.allLabels = []
        self.pureText = ''

    def GetDefaultAlignmentValues(self, *args):
        offset = sm.GetService('window').GetCameraLeftOffset(300, align=uiconst.CENTERTOP, left=0)
        if settings.user.ui.Get('shipuialigntop', 0):
            top = uicore.desktop.height * 0.75
        else:
            top = max(uicore.desktop.height * 0.2, 175)
        defaultConfig = (uiconst.CENTERTOP,
         'center',
         offset,
         top)
        return defaultConfig

    def Prepare_Text_(self):
        notificationFontSize = settings.user.ui.Get('dmgnotifictions_fontsize', 12)
        self.message = uicls.Label(text='', parent=self, left=6, top=5, width=288, state=uiconst.UI_DISABLED, fontsize=notificationFontSize)
        self.allLabels.append(self.message)

    def Prepare_Underlay_(self):
        border = uicls.Frame(parent=self, frameConst=uiconst.FRAME_BORDER1_CORNER5, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.25))
        frame = uicls.Frame(parent=self, color=(0.0, 0.0, 0.0, 0.75), frameConst=uiconst.FRAME_FILLED_CORNER4, state=uiconst.UI_DISABLED)

    def ShowMsg(self, text):
        if self.message is None:
            self.Prepare_Text_()
            self.Prepare_Underlay_()
        if getattr(self, 'fakeText', None) is not None:
            self.fakeText.Close()
        self.message.text = '<%s>%s' % (self.currentTextAlignment, text)
        self.pureText = text
        self.SetSizeAndPosition()
        self.state = uiconst.UI_DISABLED
        uiutil.SetOrder(self, 0)
        if not self.inDragMode:
            self.timer = base.AutoTimer(5000, self.hide)

    def SetSizeAndPosition(self, *args):
        self.height = self.message.textheight + 8
        self.top = max(self.minTop, min(uicore.desktop.height - self.height, self.topOffset - self.height))
        self.width = 300

    def hide(self):
        if self is not None and not self.destroyed:
            self.state = uiconst.UI_HIDDEN

    def kill_timer(self):
        self.timer = None

    def EnterDragMode(self, *args):
        self.isVisible = self.state != uiconst.UI_HIDDEN
        self.kill_timer()
        if not self.isVisible:
            if self.message is None:
                self.Prepare_Text_()
                self.Prepare_Underlay_()
            self.message.text = ''
            fakeText = getattr(self, 'fakeText', None)
            if fakeText is None or fakeText.destroyed:
                self.fakeText = uicls.EveLabelMedium(text='', parent=self, name='faketext', left=6, top=5, width=288, state=uiconst.UI_DISABLED, idx=0)
            self.fakeText.text = '<br><%s>%s' % (self.currentTextAlignment, localization.GetByLabel('UI/Accessories/Log/ExampleText'))
            self.height = self.fakeText.textheight + 10
        uicls.MessageParentClass.EnterDragMode(self, *args)

    def ExitDragMode(self, *args):
        uicls.MessageParentClass.ExitDragMode(self, *args)
        isVisible = getattr(self, 'isVisible', False)
        if isVisible:
            self.state = uiconst.UI_DISABLED
            self.timer = base.AutoTimer(5000, self.hide)
        else:
            self.hide()

    def SetTextAlignmentIfNeeded(self, alignment, *args):
        if self.currentTextAlignment != alignment:
            self.currentTextAlignment = alignment
            fakeText = getattr(self, 'fakeText', None)
            if fakeText is not None and not fakeText.destroyed:
                self.fakeText.text = '<br><%s>%s' % (alignment, localization.GetByLabel('UI/Accessories/Log/ExampleText'))
            else:
                self.message.text = '<br><%s>%s' % (alignment, self.pureText)

    def SaveSettings(self, *args):
        settings.char.ui.Set('generalMessages_config', (self.align,
         self.currentTextAlignment,
         self.left,
         self.topOffset))

    def _OnClose(self, *args):
        self.kill_timer()

    def ChangeFontSize(self, *args):
        if self.message:
            self.message.fontsize = settings.user.ui.Get('dmgnotifictions_fontsize', 12)


class CombatMessage(MessageParentClass):
    __guid__ = 'uicls.CombatMessage'

    def ApplyAttributes(self, attributes):
        self.noDamageMsgTimer = 10 * SEC
        self.expiryTime = 5 * SEC
        numMessagePerSec = 6
        self.messageSleepTime = 1000 / numMessagePerSec
        self.messageSleepTimeInMs = self.messageSleepTime / 1000.0
        self.fadeOutTime = 5.0
        self.moveUpTime = 0.8
        self.messageList = []
        self.showingMessage = False
        self.configName = 'damageMessages_config'
        self.settingNameAlign = 'dmgnotifictions_alignment'
        self.defaultConfig = self.GetDefaultAlignmentValues()
        uicls.MessageParentClass.ApplyAttributes(self, attributes)
        self.layerOffset = uicore.layer.target.absoluteLeft
        self.myLayer = uicore.layer.target
        self.minTop = -40
        self.scope = 'station_inflight'
        self.state = uiconst.UI_DISABLED
        self.allLabels = []
        self.noDamageDict = {}
        self.messageCounter = collections.deque([], maxlen=8 * numMessagePerSec)
        uthread.new(self.ShowMsg)

    def GetDefaultAlignmentValues(self, *args):
        offset = sm.GetService('window').GetCameraLeftOffset(300, align=uiconst.CENTERTOP, left=0)
        if settings.user.ui.Get('shipuialigntop', 0):
            top = uicore.desktop.height * 0.7
        else:
            top = max(uicore.desktop.height * 0.32, 225)
        defaultConfig = (uiconst.CENTERTOP,
         uiconst.CENTERBOTTOM,
         offset,
         top)
        return defaultConfig

    def Prepare_Text_(self):
        uiAlignment = self.GetUIAlignment(self.currentTextAlignment)
        notificationFontSize = settings.user.ui.Get('dmgnotifictions_fontsize', 12)
        for i in xrange(6):
            name = 'L%s' % i
            message = uicls.Label(text='', name=name, parent=self, left=6, top=5, align=uiAlignment, state=uiconst.UI_DISABLED, fontsize=notificationFontSize, dropShadow=True)
            message.display = False
            message.msgIndex = i
            setattr(self, 'message%s' % i, message)
            self.allLabels.append(message)

    def ShowMsg(self, *args):
        if self.showingMessage:
            return
        while 1:
            if not self or self.destroyed:
                return
            try:
                if len(self.messageList) == 0:
                    self.messageCounter.append(0)
                    continue
                self.messageCounter.append(1)
                now = blue.os.GetWallclockTime()
                validTime = now - self.expiryTime
                text = ''
                numMessagesDiscarded = 0
                while len(self.messageList) > 0:
                    nextMessage = self.messageList.pop(0)
                    timeStamp, text = nextMessage
                    if timeStamp < validTime:
                        numMessagesDiscarded += 1
                        continue
                    break

                if numMessagesDiscarded:
                    sm.GetService('logger').LogWarn('Discarded ', numMessagesDiscarded, ' messages')
                if not text:
                    continue
                if len(self.allLabels) < 1:
                    self.Prepare_Text_()
                if getattr(self, 'fakeText', None) is not None:
                    self.fakeText.Close()
                label, otherVisibleLabels = self.FindFreeLabel()
                label.display = True
                label.text = text
                label.top = 0
                label.msgIndex = -1
                self.SetSizeAndPosition()
                otherVisibleLabels.sort(lambda x, y: cmp(x.top, y.top))
                if sum(self.messageCounter) > 8:
                    duration = 0.166
                    secondPoint = 0.05
                else:
                    secondPoint = 0.2
                    duration = 0.4
                for i, ovl in enumerate(otherVisibleLabels):
                    uicore.animations.MorphScalar(ovl, 'top', startVal=ovl.top, endVal=(i + 1) * 20, duration=duration)
                    ovl.msgIndex = i
                    if i == 4:
                        uicore.animations.FadeOut(ovl, duration=self.messageSleepTimeInMs)

                curvePoints = ([0, 0], [secondPoint, 1.0], [1, 0])
                uicore.animations.MorphScalar(label, 'opacity', duration=self.fadeOutTime, curveType=curvePoints)
                uiutil.SetOrder(self, 0)
            except Exception as e:
                sm.GetService('logger').LogWarn('failed at displaying message, e = ', e)
            finally:
                blue.pyos.synchro.SleepWallclock(self.messageSleepTime)

    def AddMessage(self, text, hitQuality, attackerID, *args):
        now = blue.os.GetWallclockTime()
        if hitQuality == 0 and attackerID:
            if attackerID in self.noDamageDict:
                lastNoDmgMsgTime = self.noDamageDict[attackerID]
                if lastNoDmgMsgTime > now - self.noDamageMsgTimer:
                    return
            self.noDamageDict[attackerID] = now
        else:
            self.noDamageDict.pop(attackerID, None)
        self.messageList.append((now, text))

    def FindFreeLabel(self, *args):
        myLabel = None
        self.allLabels.sort(lambda x, y: cmp(x.msgIndex, y.msgIndex), reverse=True)
        myLabel = self.allLabels[0]
        myLabel.StopAnimations()
        otherVisibleLabels = []
        for label in self.allLabels:
            if label == myLabel:
                continue
            if label.display and self.IsStillFadingOut(label):
                otherVisibleLabels.append(label)
            else:
                label.display = False
                label.msgIndex = len(self.allLabels)

        return (myLabel, otherVisibleLabels)

    def IsStillFadingOut(self, label):
        return bool(label._animationCurves and 'opacity' in label._animationCurves and label._animationCurves['opacity'].scaledTime < self.fadeOutTime - 0.1)

    def SetSizeAndPosition(self, *args):
        boxHeight = 0
        widths = [100]
        for label in self.allLabels:
            if label.display:
                boxHeight += label.textheight
                widths.append(label.textwidth)

        self.width = max(widths) + 30
        self.height = boxHeight + 10
        self.top = max(self.minTop, min(uicore.desktop.height - self.height, self.topOffset - self.height))

    def SaveSettings(self, *args):
        settings.char.ui.Set('damageMessages_config', (self.align,
         self.currentTextAlignment,
         self.left,
         self.topOffset))

    def SetTextAlignmentIfNeeded(self, alignment, *args):
        alignmentMode = settings.user.ui.Get(self.settingNameAlign, 'auto')
        if alignmentMode != 'auto' and alignmentMode in ('center', 'right', 'left'):
            alignment = alignmentMode
        if self.currentTextAlignment != alignment:
            uiAlignment = self.GetUIAlignment(alignment)
            for label in self.allLabels:
                label.SetAlign(uiAlignment)

            if getattr(self, 'fakeText', None) is not None:
                self.fakeText.text = '<%s>%s' % (alignment, self.fakeText.cleanText)
            self.currentTextAlignment = alignment

    def GetUIAlignment(self, alignment):
        if alignment == 'left':
            uiAlignment = uiconst.BOTTOMLEFT
        elif alignment == 'right':
            uiAlignment = uiconst.BOTTOMRIGHT
        else:
            uiAlignment = uiconst.CENTERBOTTOM
        return uiAlignment

    def ExitDragMode(self, *args):
        if getattr(self, 'border', None) is not None:
            self.border.Close()
        uicls.MessageParentClass.ExitDragMode(self, *args)
        self.state = uiconst.UI_DISABLED
        self.SetParent(uicore.layer.target)

    def EnterDragMode(self, *args):
        for label in self.allLabels:
            if label.display and label.opacity > 0.05:
                break
        else:
            uiAlignment = self.GetUIAlignment(self.currentTextAlignment)
            self.fakeText = uicls.Label(text='', name='faketext', parent=self, left=6, top=5, align=uiAlignment, state=uiconst.UI_DISABLED, fontsize=12, width=380)
            text = localization.GetByLabel('UI/Accessories/Log/ExampleText')
            self.fakeText.text = '<%s>%s' % (self.currentTextAlignment, text)
            self.fakeText.cleanText = text
            self.height = self.fakeText.textheight + 20
            self.width = 400

        self.border = uicls.Frame(parent=self, frameConst=uiconst.FRAME_BORDER1_CORNER5, state=uiconst.UI_DISABLED, color=(1.0, 1.0, 1.0, 0.25), top=-5)
        uicls.MessageParentClass.EnterDragMode(self, *args)
        self.dragFill.top = -5
        self.exitMoveModeBtn.top = -5
        self.SetParent(uicore.layer.abovemain)

    def ResetAlignment(self, *args):
        self.SetAllAlignments(self.defaultConfig)
        self.SetSizeAndPosition()
        self.ChangeAlignment()

    def ChangeFontSize(self, *args):
        fontsize = settings.user.ui.Get('dmgnotifictions_fontsize', 12)
        if len(self.allLabels) < 1:
            return
        for label in self.allLabels:
            label.fontsize = fontsize

    def ChangeAlignment(self, *args):
        self.DoAlignment()

    def OnSessionChanged(self, isRemote, sess, change):
        self.noDamageDict = {}