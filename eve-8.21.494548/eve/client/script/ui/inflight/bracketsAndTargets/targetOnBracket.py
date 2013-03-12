#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/inflight/bracketsAndTargets/targetOnBracket.py
import trinity
import uiconst
import uicls
import math
import localization
SHOWLABELS_NEVER = 0
SHOWLABELS_ONMOUSEENTER = 1
SHOWLABELS_ALWAYS = 2
TARGETTING_UI_UPDATE_RATE = 50
LABELMARGIN = 6

class ActiveTargetOnBracket(uicls.Container):
    __guid__ = 'uicls.ActiveTargetOnBracket'
    default_name = 'activetarget'
    default_width = 120
    default_height = 120
    default_align = uiconst.CENTER
    default_state = uiconst.UI_DISABLED

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.rotatingArrows = uicls.Sprite(parent=self, name='rotatingArrows', pos=(0, 0, 120, 120), state=uiconst.UI_PICKCHILDREN, texturePath='res:/UI/Texture/classes/Target/spinCorners.png', color=(1.0, 1.0, 1.0, 0.2), align=uiconst.CENTER)
        self.selectedTargetCircle = uicls.Sprite(parent=self, name='selectedTargetCircle', pos=(0, 0, 80, 80), state=uiconst.UI_PICKCHILDREN, texturePath='res:/UI/Texture/classes/Target/selectedTargetedItem.png', color=(1.0, 1.0, 1.0, 0.15), align=uiconst.CENTER)
        self.RotateArrows()

    def RotateArrows(self, *args):
        uicore.animations.Tr2DRotateTo(self.rotatingArrows, duration=3.5, loops=uiconst.ANIM_REPEAT, startAngle=6.283185307179586, endAngle=0.0, curveType=uiconst.ANIM_LINEAR)
        uicore.animations.FadeTo(self.rotatingArrows, startVal=0.2, endVal=0.5, duration=3.0, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_WAVE)


class TargetLine(uicls.Fill):
    default_state = uiconst.UI_DISABLED
    default_color = (1.0, 1.0, 1.0, 1.0)
    default_align = uiconst.RELATIVE


class TargetOnBracket(uicls.Container):
    __guid__ = 'uicls.TargetOnBracket'
    default_name = 'target'
    default_width = 94
    default_height = 94
    default_align = uiconst.CENTER
    default_state = uiconst.UI_DISABLED

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.targetingIndicatorsEnabled = True
        self.circle = uicls.Sprite(parent=self, name='circle', pos=(0, 0, 96, 96), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Target/outerCircle.png', color=(1.0, 1.0, 1.0, 0.1), align=uiconst.CENTER)
        self.lines = lines = uicls.Container(parent=self, name='lines', pos=(0, 0, 1, 1), align=uiconst.CENTER)
        self.lines.opacity = 0.1
        linetop = TargetLine(parent=lines, name='linetop', pos=(0, -1216, 1, 1172))
        self.lines.linetop = linetop
        lineleft = TargetLine(parent=lines, name='lineleft', pos=(-1616, -1, 1572, 1))
        self.lines.lineleft = lineleft
        lineright = TargetLine(parent=lines, name='lineright', pos=(46, -1, 1600, 1))
        self.lines.lineright = lineright
        linebottom = TargetLine(parent=lines, name='linebottom', pos=(0, 46, 1, 1200))
        self.lines.linebottom = linebottom
        self.leftTimer = uicls.Sprite(parent=self, name='leftTimer', pos=(0, 0, 76, 76), state=uiconst.UI_PICKCHILDREN, texturePath='res:/UI/Texture/classes/Target/timerLeft.png', textureSecondaryPath='res:/UI/Texture/classes/Target/timerLeft.png', color=(1.0, 1.0, 1.0, 0.4), align=uiconst.CENTER, blendMode=1, spriteEffect=trinity.TR2_SFX_MODULATE)
        self.leftTimer.display = False
        self.rightTimer = uicls.Sprite(parent=self, name='rightTimer', pos=(0, 0, 76, 76), state=uiconst.UI_PICKCHILDREN, texturePath='res:/UI/Texture/classes/Target/timerRight.png', textureSecondaryPath='res:/UI/Texture/classes/Target/timerRight.png', color=(1.0, 1.0, 1.0, 0.4), align=uiconst.CENTER, blendMode=1, spriteEffect=trinity.TR2_SFX_MODULATE)
        self.rightTimer.display = False
        self.targetingArrows = uicls.Sprite(parent=self, name='targetingArrows', pos=(0, 0, 120, 120), state=uiconst.UI_PICKCHILDREN, texturePath='res:/UI/Texture/classes/Target/spinCorners.png', color=(1.0, 1.0, 1.0, 0.6), align=uiconst.CENTER)
        self.targetingArrows.rotation = math.pi / 4
        self.targetingArrows.display = False
        t = uicls.EveLabelSmall(text='', parent=self, top=64, align=uiconst.CENTERTOP, state=uiconst.UI_DISABLED)
        self.lockingText = t

    def ShowTargetingIndicators(self, *args):
        self.targetingIndicatorsEnabled = True
        self.targetingArrows.display = True
        uicore.animations.MorphScalar(self.targetingArrows, 'width', startVal=120.0, endVal=0.0, duration=0.33, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_LINEAR)
        uicore.animations.MorphScalar(self.targetingArrows, 'height', startVal=120.0, endVal=0.0, duration=0.33, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_LINEAR)
        uicore.animations.MorphScalar(self.targetingArrows, 'opacity', startVal=0.1, endVal=1.0, duration=0.33, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_LINEAR)

    def HideTargetingIndicators(self, *args):
        self.targetingIndicatorsEnabled = False
        self.targetingArrows.display = False
        self.targetingArrows.StopAnimations()
        self.KillTimerAnimation()

    def ChangeLineOpacity(self, faded = True, *args):
        if faded:
            self.lines.opacity = 0.1
            self.circle.SetAlpha(0.2)
        else:
            self.lines.opacity = 0.2
            self.circle.SetAlpha(0.5)

    def BlinkArrowsAndText(self):
        curvePoints = ([0, 0],
         [0.49, 0.0],
         [0.5, 0.4],
         [0.99, 0.4])
        uicore.animations.MorphScalar(self.leftTimer, 'opacity', duration=0.1, curveType=curvePoints, loops=uiconst.ANIM_REPEAT)
        uicore.animations.MorphScalar(self.rightTimer, 'opacity', duration=0.1, curveType=curvePoints, loops=uiconst.ANIM_REPEAT)
        curvePoints = ([0, 0],
         [0.49, 0.0],
         [0.5, 1.0],
         [0.99, 1.0])
        self.lockingText.text = localization.GetByLabel('UI/Inflight/Brackets/TargetLocked')
        uicore.animations.MorphScalar(self.lockingText, 'opacity', duration=0.1, curveType=curvePoints, loops=uiconst.ANIM_REPEAT)

    def KillTimerAnimation(self, *args):
        leftTimer = self.leftTimer
        rightTimer = self.rightTimer
        leftTimer.StopAnimations()
        rightTimer.StopAnimations()
        self.lockingText.StopAnimations()
        leftTimer.display = False
        rightTimer.display = False
        self.lockingText.display = False
        self.lockingText.text = ''

    def IsTargetingIndicatorsEnabled(self, *args):
        return self.targetingIndicatorsEnabled