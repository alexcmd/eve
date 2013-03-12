#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/infoPanels/sessionTimeIndicator.py
import uicls
import uiconst
import math
import blue
import util
import localization

class SessionTimeIndicator(uicls.Container):
    __guid__ = 'uicls.SessionTimeIndicator'

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        size = 24
        self.ramps = uicls.Container(parent=self, name='ramps', pos=(0,
         0,
         size,
         size), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        leftRampCont = uicls.Container(parent=self.ramps, name='leftRampCont', pos=(0,
         0,
         size / 2,
         size), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, clipChildren=True)
        self.leftRamp = uicls.Transform(parent=leftRampCont, name='leftRamp', pos=(0,
         0,
         size,
         size), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        uicls.Sprite(parent=self.leftRamp, name='rampSprite', pos=(0,
         0,
         size / 2,
         size), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/TiDiIndicator/left.png', color=(0, 0, 0, 0.5))
        rightRampCont = uicls.Container(parent=self.ramps, name='rightRampCont', pos=(0,
         0,
         size / 2,
         size), align=uiconst.TOPRIGHT, state=uiconst.UI_DISABLED, clipChildren=True)
        self.rightRamp = uicls.Transform(parent=rightRampCont, name='rightRamp', pos=(-size / 2,
         0,
         size,
         size), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        uicls.Sprite(parent=self.rightRamp, name='rampSprite', pos=(size / 2,
         0,
         size / 2,
         size), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/TiDiIndicator/right.png', color=(0, 0, 0, 0.5))
        self.coloredPie = uicls.Sprite(parent=self, name='tidiColoredPie', pos=(0,
         0,
         size,
         size), texturePath='res:/UI/Texture/classes/TiDiIndicator/circle.png', state=uiconst.UI_DISABLED, color=(1, 1, 1, 0.5))

    def AnimSessionChange(self):
        duration = session.nextSessionChange - blue.os.GetSimTime()
        while blue.os.GetSimTime() < session.nextSessionChange:
            timeDiff = session.nextSessionChange - blue.os.GetSimTime()
            progress = timeDiff / float(duration)
            self.SetProgress(1.0 - progress)
            timeLeft = util.FmtTimeInterval(timeDiff, breakAt='sec')
            self.hint = localization.GetByLabel('UI/Neocom/SessionChangeHint', timeLeft=timeLeft)
            self.state = uiconst.UI_NORMAL
            uicore.CheckHint()
            blue.pyos.synchro.Yield()

        self.SetProgress(1.0)
        self.state = uiconst.UI_HIDDEN

    def SetProgress(self, progress):
        progress = max(0.0, min(1.0, progress))
        leftRamp = min(1.0, max(0.0, progress * 2))
        rightRamp = min(1.0, max(0.0, progress * 2 - 1.0))
        self.leftRamp.SetRotation(math.pi + math.pi * leftRamp)
        self.rightRamp.SetRotation(math.pi + math.pi * rightRamp)