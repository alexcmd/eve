#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/inflight/bracketsAndTargets/bracketVarious.py
import util
import trinity
import uicls
import fontConst
import uiconst
import telemetry
SHOWLABELS_NEVER = 0
SHOWLABELS_ONMOUSEENTER = 1
SHOWLABELS_ALWAYS = 2
TARGETTING_UI_UPDATE_RATE = 50
LABELMARGIN = 6
GROUPS_WITH_LOOTRIGHTS = (const.groupWreck, const.groupCargoContainer, const.groupFreightContainer)

class BracketSubIconNew(uicls.Icon):
    __guid__ = 'uicls.BracketSubIconNew'

    def ApplyAttributes(self, attributes):
        uicls.Icon.ApplyAttributes(self, attributes)
        bracket = attributes.bracket
        cs = uicore.uilib.bracketCurveSet
        xBinding = trinity.CreateBinding(cs, bracket.renderObject, 'displayX', self.renderObject, 'displayX')
        yBinding = trinity.CreateBinding(cs, bracket.renderObject, 'displayY', self.renderObject, 'displayY')
        self.bindings = (xBinding, yBinding)
        self.OnMouseUp = bracket.OnMouseUp
        self.OnMouseDown = bracket.OnMouseDown
        self.OnMouseEnter = bracket.OnMouseEnter
        self.OnMouseExit = bracket.OnMouseExit
        self.OnMouseHover = bracket.OnMouseHover
        self.OnClick = bracket.OnClick
        self.GetMenu = bracket.GetMenu

    def Close(self, *args, **kw):
        if getattr(self, 'bindings', None):
            cs = uicore.uilib.bracketCurveSet
            for each in self.bindings:
                if cs and each in cs.bindings:
                    cs.bindings.remove(each)

        self.OnMouseUp = None
        self.OnMouseDown = None
        self.OnMouseEnter = None
        self.OnMouseExit = None
        self.OnMouseHover = None
        self.OnClick = None
        self.GetMenu = None
        uicls.Icon.Close(self, *args, **kw)


class BracketLabel(uicls.Label):
    __guid__ = 'uicls.BracketLabel'
    default_fontsize = fontConst.EVE_SMALL_FONTSIZE
    default_fontStyle = fontConst.STYLE_SMALLTEXT
    default_shadowOffset = (0, 1)
    displayText = None

    def ApplyAttributes(self, attributes):
        uicls.Label.ApplyAttributes(self, attributes)
        bracket = attributes.bracket
        cs = uicore.uilib.bracketCurveSet
        xBinding = trinity.CreateBinding(cs, bracket.renderObject, 'displayX', self.renderObject, 'displayX')
        yBinding = trinity.CreateBinding(cs, bracket.renderObject, 'displayY', self.renderObject, 'displayY')
        self.bindings = (xBinding, yBinding)
        self.OnMouseUp = bracket.OnMouseUp
        self.OnMouseDown = bracket.OnMouseDown
        self.OnMouseEnter = bracket.OnMouseEnter
        self.OnMouseExit = bracket.OnMouseExit
        self.OnMouseHover = bracket.OnMouseHover
        self.OnClick = bracket.OnClick
        self.GetMenu = bracket.GetMenu

    def Close(self, *args, **kw):
        if getattr(self, 'bindings', None):
            cs = uicore.uilib.bracketCurveSet
            for each in self.bindings:
                if cs and each in cs.bindings:
                    cs.bindings.remove(each)

        self.OnMouseUp = None
        self.OnMouseDown = None
        self.OnMouseEnter = None
        self.OnMouseExit = None
        self.OnMouseHover = None
        self.OnClick = None
        self.GetMenu = None
        uicls.Label.Close(self, *args, **kw)


@telemetry.ZONE_METHOD
def GetIconColor(slimItem, getSortValue = False):
    iconColor = const.OVERVIEW_NORMAL_COLOR
    colorSortValue = 0
    if slimItem.categoryID in (const.categoryShip, const.categoryDrone):
        if getSortValue:
            return (iconColor, colorSortValue)
        return iconColor
    if slimItem.categoryID == const.categoryEntity and slimItem.typeID:
        val = sm.GetService('clientDogmaStaticSvc').GetTypeAttribute2(slimItem.typeID, const.attributeEntityBracketColour)
        if val >= 1:
            iconColor = const.OVERVIEW_HOSTILE_COLOR
            colorSortValue = 1
    elif slimItem.groupID == const.groupStation:
        waypoints = sm.GetService('starmap').GetWaypoints()
        if waypoints and slimItem.itemID in waypoints:
            iconColor = const.OVERVIEW_AUTO_PILOT_DESTINATION_COLOR
            colorSortValue = -1
    elif slimItem.groupID == const.groupStargate and slimItem.jumps:
        destinationPath = sm.GetService('starmap').GetDestinationPath()
        if slimItem.jumps[0].locationID in destinationPath:
            iconColor = const.OVERVIEW_AUTO_PILOT_DESTINATION_COLOR
            colorSortValue = -1
    elif IsAbandonedContainer(slimItem):
        iconColor = const.OVERVIEW_ABANDONED_CONTAINER_COLOR
    elif IsForbiddenContainer(slimItem):
        iconColor = const.OVERVIEW_FORBIDDEN_CONTAINER_COLOR
        colorSortValue = -1
    if getSortValue:
        return (iconColor, colorSortValue)
    return iconColor


def IsForbiddenContainer(slimItem):
    if slimItem.groupID not in GROUPS_WITH_LOOTRIGHTS:
        return False
    bp = sm.StartService('michelle').GetBallpark()
    if bp is None:
        return False
    if bp.HaveLootRight(slimItem.itemID):
        return False
    return True


def IsAbandonedContainer(slimItem):
    if slimItem.groupID not in GROUPS_WITH_LOOTRIGHTS:
        return False
    bp = sm.StartService('michelle').GetBallpark()
    if bp is None:
        return False
    if bp.IsAbandoned(slimItem.itemID):
        return True
    return False


class TargetingHairlines:
    __guid__ = 'bracketUtils.TargetingHairlines'

    def __init__(self):
        self.trace = None
        self.line = None

    def CreateHairlines(self, moduleID, bracket, target):
        self.trace = uicls.VectorLineTrace(parent=uicore.layer.shipui, width=2.5, idx=-1, name='vectorlineTrace')
        self.trace.SetRGB(0.5, 0.7, 0.6, 0.5)
        self.line = uicls.VectorLineTrace(parent=uicore.layer.shipui, width=0.1, idx=-1, name='vectorline')
        linePoints = self.GetHairlinePoints(moduleID, bracket, target)
        if linePoints is None:
            return
        startPoint, midPoint, endPoint = linePoints
        self.line.AddPoint(startPoint)
        self.line.AddPoint(midPoint)
        self.line.AddPoint(endPoint)
        self.trace.AddPoint(startPoint)
        self.trace.AddPoint(midPoint)
        self.trace.AddPoint(endPoint)
        return (self.trace, self.line)

    def UpdateHairlinePoints(self, moduleID, bracket, target):
        linePoints = self.GetHairlinePoints(moduleID, bracket, target)
        if linePoints is None:
            return
        startPoint, midPoint, endPoint = linePoints
        if self.line.renderObject is None or self.trace.renderObject is None:
            sm.GetService('bracket').LogWarn('Hairlines were broken, new ones were made')
            self.line.Close()
            self.trace.Close()
            self.CreateHairlines(moduleID, bracket, target)
        self.line.renderObject.vertices[0].position = startPoint
        self.line.renderObject.vertices[1].position = midPoint
        self.line.renderObject.vertices[2].position = endPoint
        self.line.renderObject.isDirty = True
        self.trace.renderObject.vertices[0].position = startPoint
        self.trace.renderObject.vertices[1].position = midPoint
        self.trace.renderObject.vertices[2].position = endPoint
        self.trace.renderObject.isDirty = True
        self.ShowLines()

    def GetHairlinePoints(self, moduleID, bracket, target, *args):
        moduleButton = uicore.layer.shipui.GetModuleFromID(moduleID)
        ro = bracket.GetRenderObject()
        if not ro or moduleButton is None:
            return
        x = uicore.ScaleDpi(moduleButton.absoluteLeft + moduleButton.width / 2.0)
        y = uicore.ScaleDpi(moduleButton.absoluteTop + moduleButton.height / 2.0)
        startPoint = (x, y)
        weapon = target.GetWeapon(moduleID)
        if weapon:
            endPointObject = weapon
        else:
            endPointObject = target
        x = uicore.ScaleDpi(endPointObject.absoluteLeft + endPointObject.width / 2.0)
        y = uicore.ScaleDpi(endPointObject.absoluteTop + endPointObject.height / 2.0)
        endPoint = (x, y)
        x = ro.displayX
        y = ro.displayY
        l, r = uicore.layer.sidePanels.GetSideOffset()
        x += uicore.ScaleDpi(l)
        midPoint = (int(x + bracket.width / 2.0), int(y + bracket.height / 2.0))
        if not settings.user.ui.Get('modulesExpanded', True):
            startPoint = midPoint
        return (startPoint, midPoint, endPoint)

    def StartAnimation(self, reverse = False, *args):
        if reverse:
            start_values = (0.99, 0.0)
            end_values = (1.0, 0.01)
        else:
            start_values = (0.0, 1.0)
            end_values = (0.01, 1.01)
        uicore.animations.MorphScalar(self.trace, 'start', startVal=start_values[0], endVal=start_values[1], duration=1.0, loops=1, curveType=uiconst.ANIM_LINEAR)
        uicore.animations.MorphScalar(self.trace, 'end', startVal=end_values[0], endVal=end_values[1], duration=1.0, loops=1, curveType=uiconst.ANIM_LINEAR)

    def ShowLines(self, *args):
        self.line.display = True
        self.trace.display = True

    def HideLines(self, *args):
        self.line.display = False
        self.trace.display = False

    def StopAnimations(self, *args):
        self.trace.StopAnimations()


def FixLines(target):

    def FindLine(name):
        return getattr(target.lines, name)

    l, r, t, b = map(FindLine, ['lineleft',
     'lineright',
     'linetop',
     'linebottom'])
    l.left -= uicore.desktop.width - l.width
    l.width = r.width = uicore.desktop.width
    t.top -= uicore.desktop.height - t.height
    t.height = b.height = uicore.desktop.height


exports = util.AutoExports('bracketUtils', locals())