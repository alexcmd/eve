#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/spaceObjectUiPointer.py
import uicls
import uiconst
import blue
import trinity
import localization
import math
import geo2
import uiutil
from tutorial import TutorialColor, TutorialConstants
import base
POINTER_WIDTH = 300
ICON_SIZE = 48
FLOATING_DISTANCE = 48
ACCELERATION = 6.0
MAX_SPEED = 10.0
SLOWDOWN_DISTANCE = 100
MAX_ELAPSED_TIME = 0.1
DOCK_MARGIN = 20
CASE1 = 1 << 0
CASE2 = 1 << 1
CASE3 = 1 << 2
CASE4 = 1 << 3
CASE5 = 1 << 4
CASE6 = 1 << 5
CASE7 = 1 << 6
CASE8 = 1 << 7
CASE9 = 1 << 8
X_LEFT = CASE1 | CASE4 | CASE6
X_MIDDLE = CASE2 | CASE9 | CASE7
X_RIGHT = CASE3 | CASE5 | CASE8
Y_TOP = CASE1 | CASE2 | CASE3
Y_MIDDLE = CASE4 | CASE9 | CASE5
Y_BOTTOM = CASE6 | CASE7 | CASE8

class UiPointerContainer(uicls.Container):
    __guid__ = 'uipointer.UiPointerContainer'
    default_height = 300
    default_width = 100
    default_align = uiconst.TOPLEFT

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.blinkSprite = uicls.Sprite(bgParent=self, name='blinkSprite', texturePath='res:/UI/Texture/classes/Neocom/buttonDown.png', state=uiconst.UI_DISABLED)
        uicls.Frame(name='pointerFrame', bgParent=self, color=TutorialColor.HINT_FRAME)
        uicls.Fill(name='UIPointerImg', bgParent=self, color=TutorialColor.BACKGROUND)
        uicore.animations.SpSwoopBlink(self.blinkSprite, rotation=math.pi - 0.5, duration=3.0, loops=TutorialConstants.NUM_BLINKS)
        self.headerButtons = uicls.Container(name='headerButtons', state=uiconst.UI_PICKCHILDREN, align=uiconst.TOPRIGHT, parent=self, pos=(5, 0, 15, 15), idx=0, display=False)
        uicls.ImageButton(name='close', parent=self.headerButtons, align=uiconst.TOPRIGHT, state=uiconst.UI_NORMAL, pos=(0, 0, 16, 16), idleIcon='ui_38_16_220', mouseoverIcon='ui_38_16_220', mousedownIcon='ui_38_16_220', onclick=lambda : getattr(self, 'OnCloseContainer')(), expandonleft=True, hint=localization.GetByLabel('UI/Common/Buttons/Close'))
        self.headerButtons.Hide()

    def OnCloseContainer(self):
        pass

    def OnMouseEnter(self, *args):
        self.headerButtons.Show()
        self.closeButtonTimer = base.AutoTimer(2000, self.headerButtons.Hide)

    def OnMouseExit(self, *args):
        if not uiutil.IsUnder(uicore.uilib.GetMouseOver(), self):
            self.headerButtons.display = False


class FloatingBox(UiPointerContainer):
    __guid__ = 'uipointer.FloatingBox'
    default_height = 2 * const.defaultPadding + ICON_SIZE
    default_width = POINTER_WIDTH

    def ApplyAttributes(self, attributes):
        UiPointerContainer.ApplyAttributes(self, attributes)
        self.itemID = attributes.get('itemID')

    def OnCloseContainer(self):
        sm.GetService('uipointerSvc').SuppressSpaceObjectPointer(self.itemID)


class SpaceObjectTypeUiPointer(object):
    __guid__ = 'uipointer.SpaceObjectTypeUiPointer'

    def __init__(self, typeID, uiPointer, targetBall):
        self.itemID = targetBall.id
        self.bracket = SpaceObjectUiPointerBracket(parent=uicore.layer.bracket, name='SpaceObjectUiPointerBracket')
        self.bracket.trackBall = targetBall
        blue.pyos.synchro.Yield()
        height = 2 * const.defaultPadding + ICON_SIZE
        self.floatingBox = FloatingBox(name='SpaceObjectUiPointer.box', parent=uicore.layer.abovemain, top=(uicore.desktop.height - height) / 2, left=(uicore.desktop.width - POINTER_WIDTH) / 2, hint=localization.GetByLabel(uiPointer.hint) if uiPointer.hint else None, state=uiconst.UI_NORMAL, itemID=self.itemID)
        self.icon = uicls.Icon(typeID=typeID, parent=self.floatingBox, width=ICON_SIZE, height=ICON_SIZE, ignoreSize=True, padding=const.defaultPadding, align=uiconst.TOLEFT, OnClick=lambda : sm.GetService('info').ShowInfo(typeID=typeID))
        textContainer = uicls.Container(parent=self.floatingBox, align=uiconst.TOALL)
        self.typeLabel = uicls.EveLabelLarge(name='typeNameLabel', parent=textContainer, text='<url=showinfo:%s//%s>%s</url>' % (typeID, self.itemID, cfg.invtypes.Get(typeID).typeName), top=const.defaultPadding, align=uiconst.TOTOP, state=uiconst.UI_NORMAL)
        self.messgeLabel = uicls.EveLabelSmall(name='mesageLabel', parent=textContainer, text=localization.GetByLabel(uiPointer.message) if uiPointer.message else '', align=uiconst.TOTOP)
        self.line = uicls.VectorLine(widthFrom=1.2, widthTo=1.2, translationFrom=(0, 0), translationTo=(10, 10), parent=self.floatingBox, name='spaceObjectBracketPointer', left=self.floatingBox.width / 2, top=self.floatingBox.height / 2, color=TutorialColor.HINT_FRAME, align=uiconst.TOPLEFT)
        cs = uicore.uilib.bracketCurveSet
        self.bindings = []
        self.bindings.append(trinity.CreateBinding(cs, self.bracket.renderObject, 'displayX', None, ''))
        self.bindings.append(trinity.CreateBinding(cs, self.bracket.renderObject, 'displayY', None, ''))
        self.bindings.append(trinity.CreateBinding(cs, self.floatingBox.renderObject, 'displayX', None, ''))
        self.bindings.append(trinity.CreateBinding(cs, self.floatingBox.renderObject, 'displayY', None, ''))
        for binding in self.bindings:
            binding.copyValueCallable = self.Update

        self.lastUpdateTime = blue.os.GetSimTime()
        self.speed = 0.0

    def CalcVectorTo(self, contA, contB):
        x0, y0 = self.GetContainerPosition(contA)
        x1, y1 = self.GetContainerPosition(contB)
        return (x1 - x0, y1 - y0)

    def GetContainerPosition(self, cont):
        x = uicore.ScaleDpi(cont.left + cont.width / 2)
        y = uicore.ScaleDpi(cont.top + cont.height / 2)
        if cont is self.bracket:
            l, r = uicore.layer.sidePanels.GetSideOffset()
            x += uicore.ScaleDpi(l)
        return (x, y)

    def UpdateBoxPosition(self):
        t = blue.os.GetSimTime()
        vx, vy = self.CalcVectorTo(self.floatingBox, self.bracket)
        distToBox = self.DistanceFromPointToBox(self.GetContainerPosition(self.bracket), self.floatingBox)
        diff = distToBox - FLOATING_DISTANCE
        absDiff = abs(diff)
        ratio = 1.0
        if absDiff < 15.0:
            self.speed = 0
            return
        if absDiff < SLOWDOWN_DISTANCE:
            ratio = absDiff / SLOWDOWN_DISTANCE
        elapsedTime = min(MAX_ELAPSED_TIME, float(t - self.lastUpdateTime) / const.SEC)
        change = ACCELERATION * elapsedTime
        self.speed = min(self.speed + change, MAX_SPEED * ratio)
        x = vx / diff * self.speed
        y = vy / diff * self.speed
        box = self.floatingBox
        box.left += x
        box.top += y
        left, top, width, height = uicore.layer.bracket.GetAbsolute()
        xMin, xMax = left + DOCK_MARGIN, left + width - box.width - DOCK_MARGIN
        yMin, yMax = top + DOCK_MARGIN, height - box.height - top - DOCK_MARGIN
        if box.left < xMin:
            box.left = xMin
        elif box.left > xMax:
            box.left = xMax
        if box.top < yMin:
            box.top = yMin
        elif box.top > yMax:
            box.top = yMax
        self.lastUpdateTime = t

    def Update(self, *args):
        t = blue.os.GetSimTime()
        if t == self.lastUpdateTime:
            return
        if sm.GetService('michelle').GetBall(self.itemID) is None:
            self.Close()
            return
        self.UpdateBoxPosition()
        bracketPos = self.GetContainerPosition(self.bracket)
        boxPos = self.GetContainerPosition(self.floatingBox)
        lineTo = self.GetLineConnectionPointOnBox(bracketPos, self.floatingBox)
        cornerPos = geo2.Vec2Add(boxPos, lineTo)
        vec = geo2.Vec2Subtract(bracketPos, cornerPos)
        length = geo2.Vec2Length(vec)
        vec = geo2.Scale(vec, (length - uicore.ScaleDpi(ICON_SIZE / 2)) / length)
        self.line.translationTo = geo2.Vec2Add(vec, lineTo)
        self.line.translationFrom = lineTo

    def GetAABB(self, box):
        xMin = uicore.ScaleDpi(box.left)
        xMax = xMin + uicore.ScaleDpi(box.width)
        yMin = uicore.ScaleDpi(box.top)
        yMax = yMin + uicore.ScaleDpi(box.height)
        return (xMin,
         xMax,
         yMin,
         yMax)

    def ClassifyPointNearBox(self, point, box):
        x, y = point
        xMin, xMax, yMin, yMax = self.GetAABB(box)
        if x < xMin:
            case = X_LEFT
        elif xMax < x:
            case = X_RIGHT
        else:
            case = X_MIDDLE
        if y < yMin:
            case &= Y_TOP
        elif yMax < y:
            case &= Y_BOTTOM
        else:
            case &= Y_MIDDLE
        return case

    def DistanceFromPointToBox(self, point, box):
        case = self.ClassifyPointNearBox(point, box)
        x, y = point
        xMin, xMax, yMin, yMax = self.GetAABB(box)
        if case == CASE1:
            boxPoint = (xMin, yMin)
        elif case == CASE2:
            boxPoint = (x, yMin)
        elif case == CASE3:
            boxPoint = (xMax, yMin)
        elif case == CASE4:
            boxPoint = (xMin, y)
        elif case == CASE5:
            boxPoint = (xMax, y)
        elif case == CASE6:
            boxPoint = (xMin, yMax)
        elif case == CASE7:
            boxPoint = (x, yMax)
        elif case == CASE8:
            boxPoint = (xMax, yMax)
        elif case == CASE9:
            return 0.0
        return geo2.Vec2Length(geo2.Vec2Subtract(point, boxPoint))

    def GetLineConnectionPointOnBox(self, point, box):
        case = self.ClassifyPointNearBox(point, box)
        xMax, yMax = uicore.ScaleDpi(box.width) * 0.5, uicore.ScaleDpi(box.height) * 0.5
        xMin, yMin = -xMax, -yMax
        if case == CASE1:
            boxPoint = (xMin, yMin)
        elif case == CASE2:
            boxPoint = (0, yMin)
        elif case == CASE3:
            boxPoint = (xMax, yMin)
        elif case == CASE4:
            boxPoint = (xMin, 0)
        elif case == CASE5:
            boxPoint = (xMax, 0)
        elif case == CASE6:
            boxPoint = (xMin, yMax)
        elif case == CASE7:
            boxPoint = (0, yMax)
        elif case == CASE8:
            boxPoint = (xMax, yMax)
        elif case == CASE9:
            x = (xMin + xMax) * 0.5
            y = (yMin + yMax) * 0.5
            point2 = geo2.Vec2Subtract(point, (x, y))
            boxPoint = sorted(((xMin, yMin),
             (xMin, yMax),
             (xMax, yMin),
             (xMax, yMax)), key=lambda x: geo2.Vec2Length(geo2.Vec2Subtract(point2, x)))[0]
        return boxPoint

    def Close(self):
        sm.GetService('uipointerSvc').FlushSpaceObjectPointer(self.itemID)
        self.floatingBox.Close()
        self.bracket.Close()
        self.line.Close()
        cs = uicore.uilib.bracketCurveSet
        if cs:
            for binding in self.bindings:
                if binding in cs.bindings:
                    cs.bindings.remove(binding)

        sm.ScatterEvent('OnTutorialHighlightItem', self.itemID, False)


class SpaceObjectUiPointerBracket(uicls.Bracket):
    __guid__ = 'tutorial.SpaceObjectUiPointerBracket'
    default_texturePath = 'res:/ui/texture/classes/Tutorial/circle48strong.png'
    default_width = 16
    default_height = 16
    default_align = uiconst.NOALIGN
    default_state = uiconst.UI_DISABLED

    def ApplyAttributes(self, attributes):
        uicls.Bracket.ApplyAttributes(self, attributes)
        self.dock = True
        self.texturePath = attributes.get('texturePath', self.default_texturePath)
        uicls.Sprite(parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, texturePath=self.texturePath, color=TutorialColor.HINT_FRAME, width=48, height=48)
        self.projectBracket.marginRight = self.projectBracket.marginLeft + self.width
        self.projectBracket.marginBottom = self.projectBracket.marginTop + self.height
        self.projectBracket.parent = uicore.layer.inflight.GetRenderObject()
        self.inflight = True