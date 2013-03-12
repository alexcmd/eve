#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/uipointersvc.py
import blue
import uthread
import service
import util
import sys
import log
import uiconst
import uicls
import base
from collections import namedtuple
import uipointer
import math
from tutorial import TutorialColor, TutorialConstants
import localization
import uiutil
UIPOINTER_WIDTH = 220
UIPOINTER_HEIGHT = 70
UIPOINTER_ARROW_WIDTH = 7
UIPOINTER_ARROW_HEIGHT = 15
WAITING_FOR_ELEMENT_TO_COME_BACK_SEC = 1000
HINT_WORKER_DELAY_MS = 2000
HINT_DISPLAY_DELAY_MS = 250
SpaceObjectUiPointerData = namedtuple('SpaceObjectUiPointerData', 'typeID, groupID, message, hint')

class UIPointerSvc(service.Service):
    __exportedcalls__ = {}
    __guid__ = 'svc.uipointerSvc'
    __notifyevents__ = ['OnSessionChanged',
     'OnEveMenuShown',
     'DoBallRemove',
     'OnUIScalingChange']
    __servicename__ = 'UIPointers'
    __displayname__ = 'UI Pointer Service'
    __dependencies__ = ['michelle']

    def __init__(self):
        service.Service.__init__(self)
        self.running = True
        self.currentPointer = None
        self.oldObscurers = None

    def Run(self, memStream = None):
        self.elementUrl = []
        self.spaceObjectUiPointersByItemID = {}
        self.spaceObjectUiPointerByType = {}
        self.spaceObjectUiPointerByGroup = {}
        self.suppressedSpaceObjectUiPointers = set()
        self.spaceObjectUiPointerUpdater = None
        self.activePointerThread = None

    def Stop(self, memStream = None):
        self.running = False
        self.ClearPointers()

    def OnSessionChanged(self, isremote, sess, change):
        if 'shipid' in change:
            oldShipID, newShipID = change['shipid']
            if newShipID is not None:
                pointer = self.spaceObjectUiPointersByItemID.get(newShipID)
                if pointer is not None:
                    pointer.Close()

    def OnEveMenuShown(self):
        if self.currentPointer and self.currentPointer['pointToElement'].name == 'eveMenuBtn':
            self.ClearPointers()

    def OnUIScalingChange(self, change, *args):
        self.ClearPointers(killPointer=False)
        if self.spaceObjectUiPointerUpdater is not None:
            self.RestartSpacePointers(self.activeTutorialBrowser, clearPointers=True)

    def UpdatePointer(self):
        while self.currentPointer is not None:
            uiPointerElement = self.currentPointer['uiPointerElement']
            pointToElement = self.currentPointer['pointToElement']
            considerations = self.currentPointer['considerations']
            oldPointLeft = self.currentPointer['oldPointLeft']
            oldPointUp = self.currentPointer['oldPointUp']
            oldPointDown = self.currentPointer['oldPointDown']
            uiPointerText = self.currentPointer['uiPointerText']
            if pointToElement is None or pointToElement.destroyed or hasattr(pointToElement, 'InStack') and pointToElement.InStack():
                blue.pyos.synchro.SleepWallclock(WAITING_FOR_ELEMENT_TO_COME_BACK_SEC)
                rediscoveredElement = self.FindElementToPointTo()
                if self.currentPointer is None or rediscoveredElement is None or rediscoveredElement.destroyed:
                    self.HidePointer()
                    continue
                else:
                    pointToElement = rediscoveredElement
                    self.currentPointer['pointToElement'] = rediscoveredElement
            cumTop, cumLeft, pointLeft, pointUp, pointDown, isObscured, arrowPos = self.GetLocation(pointToElement, considerations)
            if uicore.layer.systemmenu.isopen or cumTop <= 0 and cumLeft <= 0 or pointToElement.state == uiconst.UI_HIDDEN:
                self.HidePointer()
            else:
                self.ShowPointer()
            if pointLeft != oldPointLeft or pointUp != oldPointUp or pointDown != oldPointDown:
                self.ClearPointers(killPointer=False)
                elementContainer = self.SpawnPointer(cumTop, cumLeft, pointLeft, pointUp, pointDown, pointToElement, uiPointerText, arrowPos)
                self.currentPointer = {'uiPointerElement': elementContainer,
                 'pointToElement': pointToElement,
                 'considerations': considerations,
                 'oldPointLeft': pointLeft,
                 'oldPointUp': pointUp,
                 'oldPointDown': pointDown,
                 'uiPointerText': uiPointerText}
            uiPointerElement.top = cumTop
            uiPointerElement.left = cumLeft
            blue.pyos.synchro.SleepWallclock(20)

    def FindDeep(self, element, idOfItemToFind):
        if hasattr(element, 'name') and element.name == idOfItemToFind:
            return element
        elif hasattr(element, 'children'):
            for child in element.children:
                results = self.FindDeep(child, idOfItemToFind)
                if results is not None:
                    return results

            return
        else:
            return

    def GetLocation(self, element, directive):
        try:
            parent = element
            while hasattr(parent, 'parent'):
                if parent is None or parent.state == uiconst.UI_HIDDEN:
                    return (-999,
                     -999,
                     False,
                     False,
                     False,
                     False)
                parent = parent.parent

            width = 0
            if directive == 'shipui' and element.parent.name == 'slotsContainer':
                if element.parent.name == 'slotsContainer':
                    slotsContainer = element.parent
                    cumTop, cumLeft = slotsContainer.absoluteTop + element.top, slotsContainer.absoluteLeft + element.left + 5
            elif directive == 'bracket':
                parent = element.parent
                cumTop, cumLeft = parent.absoluteTop + element.top, parent.absoluteLeft + element.left - 2
            elif directive == 'neocom':
                cumTop, cumLeft = element.absoluteTop, element.absoluteLeft
            elif hasattr(element, 'absoluteTop') and hasattr(element, 'absoluteLeft'):
                cumTop, cumLeft = element.absoluteTop - 2, element.absoluteLeft - 2
            else:
                cumTop, cumLeft = element.parent.absoluteTop + element.top - 2, element.parent.absoluteLeft + element.left - 2
            pointLeft = True
            height = element.height
            if height == 0:
                height = element.absoluteBottom - element.absoluteTop
            cumTop += height / 2 - UIPOINTER_HEIGHT / 2
            if cumLeft - UIPOINTER_WIDTH <= 0:
                if directive == 'neocom':
                    neocom = sm.GetService('neocom').neocom
                    if neocom is not None:
                        width = neocom.width
                    else:
                        width = element.width
                        if width == 0:
                            width = element.absoluteRight - element.absoluteLeft
                else:
                    width = element.width
                    if width == 0:
                        width = element.absoluteRight - element.absoluteLeft
                cumLeft = cumLeft + width + 2
            else:
                pointLeft = False
                cumLeft -= UIPOINTER_WIDTH - 2
            pointUp = False
            pointDown = False
            arrowPos = 0
            if cumTop < 0:
                if directive != 'neocom':
                    pointUp = True
                    cumTop += height / 2 + UIPOINTER_HEIGHT / 2
                    if hasattr(element, 'absoluteLeft') and hasattr(element, 'absoluteRight'):
                        cumLeft = element.absoluteLeft - UIPOINTER_WIDTH / 2 + (element.absoluteRight - element.absoluteLeft) / 2
                    else:
                        cumLeft = element.parent.absoluteLeft + element.left - UIPOINTER_WIDTH / 2
                    if cumLeft < 0:
                        cumLeft = 0
                    elif cumLeft + UIPOINTER_WIDTH > uicore.desktop.width:
                        cumLeft = uicore.desktop.width - UIPOINTER_WIDTH
                    if directive == 'bracket':
                        cumTop -= 8
                else:
                    additionalSpace = 8
                    arrowPos = cumTop - additionalSpace
                    cumTop = additionalSpace
            elif cumTop + UIPOINTER_HEIGHT > uicore.desktop.height:
                uiPointerElement = self.currentPointer['uiPointerElement']
                currentPointerHeight = uiPointerElement.height
                if currentPointerHeight < 1:
                    currentPointerHeight = UIPOINTER_HEIGHT
                pointDown = True
                cumTop = element.absoluteTop - currentPointerHeight
                cumLeft = element.absoluteLeft - UIPOINTER_WIDTH / 2 + (element.absoluteRight - element.absoluteLeft) / 2
                if cumLeft < 0:
                    cumLeft = 0
                elif cumLeft + UIPOINTER_WIDTH > uicore.desktop.width:
                    cumLeft = uicore.desktop.width - UIPOINTER_WIDTH
            elif pointLeft == False:
                if directive == 'bracket':
                    cumTop -= 3
            elif directive == 'bracket':
                cumLeft += UIPOINTER_ARROW_WIDTH
                cumTop -= 3
            isObscured = self.CheckIsElementObscured(cumTop, cumLeft, pointLeft, element)
            return (cumTop,
             cumLeft,
             pointLeft,
             pointUp,
             pointDown,
             isObscured,
             arrowPos)
        except:
            log.LogException()
            sys.exc_clear()
            return (-999,
             -999,
             False,
             False,
             False,
             False)

    def CheckIsElementObscured(self, top, left, pointLeft, element):
        globalLayer = uicore.layer.main
        abovemain = uicore.layer.abovemain
        candidates = self.GetObscureCandidates(globalLayer, element, False)
        candidates.extend(self.GetObscureCandidates(abovemain, element, True))
        left, top, width, height = element.GetAbsolute()
        elementPoints = []
        elementPoints.append(util.KeyVal(x=left, y=top))
        elementPoints.append(util.KeyVal(x=left, y=top + height))
        elementPoints.append(util.KeyVal(x=left + width, y=top))
        elementPoints.append(util.KeyVal(x=left + width, y=top + height))
        occluded = False
        occludors = []
        for candidate in candidates:
            absLeft, absTop, width, height = candidate.GetAbsolute()
            absRight = absLeft + width
            absBottom = absTop + height
            for point in elementPoints:
                if point.x > absLeft and point.x < absRight and point.y > absTop and point.y < absBottom:
                    occluded = True
                    occludors.append(candidate)
                    break

        self.UpdateObscurers(occludors)
        return occluded

    def GetObscureCandidates(self, layer, pointToElement, topLayer):
        parentWindow = self.GetElementsParent(pointToElement)
        parentIdx = self.GetElementIdx(parentWindow)
        if parentIdx is None:
            return []
        list = []
        for window in layer.children:
            windowIdx = self.GetElementIdx(window)
            if windowIdx is None:
                return []
            if hasattr(window, 'name') and window.name not in ('UIPointer',
             'locationInfo',
             'snapIndicator',
             'windowhilite',
             parentWindow.name) and hasattr(window, 'state') and window.state != uiconst.UI_HIDDEN and hasattr(window, 'absoluteTop') and hasattr(window, 'absoluteBottom') and hasattr(window, 'absoluteRight') and hasattr(window, 'absoluteLeft'):
                if not topLayer and windowIdx < parentIdx:
                    list.append(window)
                elif topLayer:
                    list.append(window)

        return list

    def UpdateObscurers(self, obscurers):
        oldObscurers = self.oldObscurers
        if oldObscurers == None:
            oldObscurers = []
        for window in oldObscurers:
            if window not in obscurers:
                window.opacity = 1.0

        for window in obscurers:
            window.opacity = 0.6

        self.oldObscurers = obscurers

    def GetElementIdx(self, element):
        if element.name == 'aura9':
            return 0
        parent = element.parent
        if not parent:
            return None
        elementIndex = 0
        for child in parent.children:
            if child == element:
                break
            elementIndex += 1

        return elementIndex

    def GetElementsParent(self, element):
        parentWindow = element
        while True:
            if not hasattr(parentWindow.parent, 'parent'):
                break
            elif not hasattr(parentWindow.parent.parent, 'parent'):
                break
            elif not hasattr(parentWindow.parent.parent.parent, 'parent'):
                break
            else:
                parentWindow = parentWindow.parent

        return parentWindow

    def FindElementToPointTo(self):
        if len(self.elementUrl) == 1:
            pointToElement = self.FindDeep(uicore.desktop, self.elementUrl[0])
        elif len(self.elementUrl) == 2 and self.elementUrl[0] == 'neocom':
            wndID = self.elementUrl[1]
            pointToElement = sm.GetService('neocom').GetUIObjectByID(wndID)
            if not sm.GetService('neocom').IsButtonVisible(wndID):
                sm.GetService('neocom').Blink(wndID)
        else:
            parent = uicore.desktop
            for path in self.elementUrl[:-1]:
                parent = self.FindDeep(parent, path)

            pointToElement = self.FindDeep(parent, self.elementUrl[-1])
        if hasattr(pointToElement, 'InStack') and pointToElement.InStack():
            pointToElement = pointToElement.sr.tab
        return pointToElement

    def PointTo(self, pointToID, uiPointerText):
        self.LogInfo('PointTo', pointToID, uiPointerText)
        self.ClearPointers()
        if pointToID is None or pointToID == '':
            return
        self.activePointerThread = uthread.new(self._PointTo, pointToID, uiPointerText)

    def _PointTo(self, pointToID, uiPointerText):
        blue.pyos.synchro.SleepWallclock(HINT_DISPLAY_DELAY_MS)
        self.LogInfo('_PointTo', pointToID, uiPointerText)
        self.elementUrl = pointToID.split('.')
        while True:
            pointToElement = self.FindElementToPointTo()
            if pointToElement is not None and pointToElement.state != uiconst.UI_HIDDEN:
                parent = pointToElement
                if self.elementUrl and self.elementUrl[0] == 'neocom':
                    considerations = 'neocom'
                else:
                    considerations = None
                while considerations is None and hasattr(parent, 'parent') and pointToElement.parent is not None and hasattr(parent.parent, 'name'):
                    parent = parent.parent
                    if parent.name == 'shipui':
                        considerations = 'shipui'
                    elif parent.name == 'l_bracket':
                        considerations = 'bracket'

                cumTop, cumLeft, pointLeft, pointUp, pointDown, isObscured, arrowPos = self.GetLocation(pointToElement, considerations)
                elementContainer = self.SpawnPointer(cumTop, cumLeft, pointLeft, pointUp, pointDown, pointToElement, uiPointerText, arrowPos)
                self.currentPointer = {'uiPointerElement': elementContainer,
                 'pointToElement': pointToElement,
                 'considerations': considerations,
                 'oldPointLeft': pointLeft,
                 'oldPointUp': pointUp,
                 'oldPointDown': pointDown,
                 'uiPointerText': uiPointerText}
                self.UpdatePointer()
            else:
                reason = "The element with the id/name '%s' can not be found" % pointToID
                if pointToElement is not None:
                    reason = "The element with the id/name '%s' is invisible" % pointToID
                self.LogInfo('Not displaying UI Pointer because:', reason)
            blue.pyos.synchro.SleepWallclock(HINT_WORKER_DELAY_MS)

    def ClearPointers(self, killPointer = True):
        self.LogInfo('ClearPointers')
        if self.currentPointer is not None:
            self.currentPointer['uiPointerElement'].Close()
            if self.currentPointer['uiPointerElement'] in uicore.layer.hint.children:
                uicore.layer.hint.children.remove(self.currentPointer['uiPointerElement'])
            self.currentPointer = None
            self.UpdateObscurers([])
        if killPointer:
            self.KillPointerUpdater()

    def KillPointerUpdater(self):
        if self.activePointerThread is not None:
            self.activePointerThread.kill()
            self.activePointerThread = None

    def SpawnPointer(self, cumTop, cumLeft, pointLeft, pointUp, pointDown, element, text, arrowPosition):
        layer = uicore.layer.hint
        display = True
        if uicore.layer.systemmenu.isopen or cumTop <= 0 and cumLeft <= 0 or not uiutil.IsVisible(element):
            display = False
        rectTop = 128
        if pointLeft:
            rectTop = 0
        elementContainer = uicls.UIPointerContainer(parent=layer, name='UIPointer', text=text, idx=-1, pos=(cumTop,
         cumLeft,
         UIPOINTER_WIDTH,
         UIPOINTER_HEIGHT), align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL, display=display, rectTop=rectTop, pointDirections=(pointUp, pointDown, pointLeft), arrowPositionModifier=arrowPosition)
        elementContainer.ResizeAndAddFrame()
        return elementContainer

    def HidePointer(self):
        if self.currentPointer != None and 'uiPointerElement' in self.currentPointer:
            self.currentPointer['uiPointerElement'].display = False

    def ShowPointer(self):
        if self.currentPointer != None and 'uiPointerElement' in self.currentPointer:
            self.currentPointer['uiPointerElement'].display = True

    def AddSpaceObjectTypeUiPointer(self, typeID, groupID, message, hint, tutorialBrowser):
        self.LogInfo('AddSpaceObjectTypeUiPointer', typeID, groupID, message, hint)
        if typeID is not None:
            self.spaceObjectUiPointerByType[typeID] = SpaceObjectUiPointerData(typeID, None, message, hint)
        if groupID is not None:
            self.spaceObjectUiPointerByGroup[groupID] = SpaceObjectUiPointerData(None, groupID, message, hint)
        self.RestartSpacePointers(tutorialBrowser, clearPointers=False)

    def RestartSpacePointers(self, tutorialBrowser, clearPointers = False):
        self.KillSpacePointerUpdater()
        if clearPointers:
            for itemID in self.spaceObjectUiPointersByItemID.keys():
                pointer = self.spaceObjectUiPointersByItemID.pop(itemID)
                pointer.Close()

        self.spaceObjectUiPointerUpdater = uthread.new(self.UpdateSpaceObjectUiPointers, tutorialBrowser)

    def KillSpacePointerUpdater(self):
        if self.spaceObjectUiPointerUpdater is not None:
            self.spaceObjectUiPointerUpdater.kill()
            self.spaceObjectUiPointerUpdater = None

    def UpdateSpaceObjectUiPointers(self, tutorialBrowser):
        blue.pyos.synchro.SleepWallclock(HINT_DISPLAY_DELAY_MS)
        self.activeTutorialBrowser = tutorialBrowser
        while self.spaceObjectUiPointerUpdater is not None:
            if tutorialBrowser is None or tutorialBrowser.destroyed:
                self.LogInfo('SpaceObject updater. Browser no longer exists.  Terminating updates.')
            bp = self.michelle.GetBallpark()
            if bp is None:
                return
            itemsToPointAt = []
            for slimItem in bp.slimItems.itervalues():
                data = self.spaceObjectUiPointerByType.get(slimItem.typeID)
                if data is None:
                    data = self.spaceObjectUiPointerByGroup.get(slimItem.groupID)
                if data is not None:
                    if slimItem.charID is None:
                        if slimItem.itemID not in self.spaceObjectUiPointersByItemID:
                            if slimItem.itemID not in self.suppressedSpaceObjectUiPointers:
                                itemsToPointAt.append((slimItem.itemID, slimItem.typeID, data))
                        sm.ScatterEvent('OnTutorialHighlightItem', slimItem.itemID, True)

            for itemID, typeID, data in itemsToPointAt:
                if slimItem.itemID not in self.spaceObjectUiPointersByItemID:
                    self.spaceObjectUiPointersByItemID[itemID] = uipointer.SpaceObjectTypeUiPointer(typeID, data, bp.GetBall(itemID))
                    self.LogInfo('Creating UI Pointer for item', itemID, 'of type', typeID)

            for itemID in self.spaceObjectUiPointersByItemID.keys():
                slimItem = bp.slimItems.get(itemID)
                if slimItem and slimItem.charID is not None:
                    pointer = self.spaceObjectUiPointersByItemID.pop(itemID)
                    if pointer is not None:
                        self.LogInfo('Space pointer target item', itemID, 'is now borderd or otherwise possessed by', slimItem.charID)
                        pointer.Close()

            blue.pyos.synchro.SleepWallclock(HINT_WORKER_DELAY_MS)

    def RemoveSpaceObjectUiPointers(self):
        self.KillSpacePointerUpdater()
        pointers = self.spaceObjectUiPointersByItemID.values()
        self.spaceObjectUiPointersByItemID.clear()
        self.spaceObjectUiPointerByType.clear()
        self.spaceObjectUiPointerByGroup.clear()
        self.suppressedSpaceObjectUiPointers.clear()
        for pointer in pointers:
            pointer.Close()

        self.LogInfo('Removing all space object pointers')

    def FlushSpaceObjectPointer(self, itemID):
        self.spaceObjectUiPointersByItemID.pop(itemID, None)

    def SuppressSpaceObjectPointer(self, itemID):
        self.suppressedSpaceObjectUiPointers.add(itemID)
        self.LogInfo('space object pointer for', itemID, 'was suppressed')
        pointer = self.spaceObjectUiPointersByItemID.get(itemID)
        if pointer is not None:
            pointer.Close()

    def DoBallRemove(self, ball, slimItem, terminal):
        pointer = self.spaceObjectUiPointersByItemID.get(slimItem.itemID)
        if pointer is not None:
            pointer.Close()
            self.LogInfo('An item with a space object pointer was removed. Pointer Closer', slimItem)


class UIPointerContainer(uicls.Container):
    __guid__ = 'uicls.UIPointerContainer'

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        text = attributes.get('text', '')
        self.pointDirections = attributes.get('pointDirections', (0, 0, 0))
        self.arrowPositionModifier = attributes.get('arrowPositionModifier', 0)
        pointUp, pointDown, pointLeft = self.pointDirections
        self.innerCont = uicls.Container(parent=self, align=uiconst.TOALL, name='innerCont')
        self.blinkSprite = uicls.Sprite(bgParent=self.innerCont, name='blinkSprite', texturePath='res:/UI/Texture/classes/Neocom/buttonDown.png', state=uiconst.UI_DISABLED)
        bgColor = (0.0, 0.0, 0.0, 0.8)
        backgroundFill = uicls.Fill(name='UIPointerImg', bgParent=self.innerCont, color=bgColor)
        self.arrowSprite = uicls.Sprite(name='arrow', parent=self, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, color=bgColor)
        maxTextWidth = UIPOINTER_WIDTH - 23
        self.pointerLabel = uicls.EveCaptionSmall(text=text, parent=self.innerCont, align=uiconst.CENTER, width=maxTextWidth, state=uiconst.UI_DISABLED, idx=0)
        if self.pointerLabel.textwidth < maxTextWidth:
            self.pointerLabel.left = (maxTextWidth - self.pointerLabel.textwidth) / 2
        self.headerButtons = uicls.Container(name='headerButtons', state=uiconst.UI_PICKCHILDREN, align=uiconst.TOPRIGHT, parent=self.innerCont, pos=(5, 0, 15, 15), idx=0, display=False)
        uicls.ImageButton(name='close', parent=self.headerButtons, align=uiconst.TOPRIGHT, state=uiconst.UI_NORMAL, pos=(0, 0, 16, 16), idleIcon='ui_38_16_220', mouseoverIcon='ui_38_16_220', mousedownIcon='ui_38_16_220', onclick=lambda : getattr(self, 'OnClosePointer')(), expandonleft=True, hint=localization.GetByLabel('UI/Common/Buttons/Close'))
        self.headerButtons.Hide()

    def ResizeAndAddFrame(self):
        self.height = max(self.height, self.pointerLabel.textheight + 2 * const.defaultPadding)
        upDownLeft = UIPOINTER_WIDTH / 2 - UIPOINTER_ARROW_WIDTH / 2 + self.arrowPositionModifier
        leftRightTop = UIPOINTER_HEIGHT / 2 - UIPOINTER_ARROW_HEIGHT / 2 + self.arrowPositionModifier
        arrowSprite = self.arrowSprite
        pointUp, pointDown, pointLeft = self.pointDirections
        if pointUp or pointDown:
            arrowSprite.width = UIPOINTER_ARROW_HEIGHT
            arrowSprite.height = UIPOINTER_ARROW_WIDTH
            arrowSprite.left = upDownLeft
            if pointUp:
                arrowSprite.texturePath = 'res:/UI/Texture/classes/UIPointer/pointUp.png'
                arrowSprite.top = 0
                self.innerCont.padTop = arrowSprite.height
            elif pointDown:
                arrowSprite.texturePath = 'res:/UI/Texture/classes/UIPointer/pointDown.png'
                arrowSprite.top = self.height - arrowSprite.height
                self.innerCont.padBottom = arrowSprite.height
        else:
            arrowSprite.width = UIPOINTER_ARROW_WIDTH
            arrowSprite.height = UIPOINTER_ARROW_HEIGHT
            arrowSprite.top = leftRightTop
            if pointLeft:
                arrowSprite.texturePath = 'res:/UI/Texture/classes/UIPointer/pointLeft.png'
                arrowSprite.left = 0
                self.innerCont.padLeft = arrowSprite.width
            else:
                arrowSprite.texturePath = 'res:/UI/Texture/classes/UIPointer/pointRight.png'
                arrowSprite.left = UIPOINTER_WIDTH - arrowSprite.width
                self.innerCont.padRight = arrowSprite.width
        lineWidth = 1
        vectorLine = uicls.VectorLineTrace(parent=self.innerCont, width=lineWidth)
        vectorLine.isLoop = True
        leftMost = 0
        rightMost = self.width - self.innerCont.padLeft - self.innerCont.padRight
        top = 0
        bottom = self.height - self.innerCont.padTop - self.innerCont.padBottom
        extraVertices = []
        if pointUp:
            extraVertices = [(1, (arrowSprite.left, top)), (2, (arrowSprite.left + arrowSprite.width / 2.0, top - arrowSprite.height)), (3, (arrowSprite.left + arrowSprite.width, top))]
        elif pointDown:
            extraVertices = [(3, (arrowSprite.left + arrowSprite.width, bottom)), (4, (arrowSprite.left + arrowSprite.width / 2.0, bottom + arrowSprite.height)), (5, (arrowSprite.left, bottom))]
        elif pointLeft:
            extraVertices = [(4, (leftMost, arrowSprite.top + arrowSprite.height)), (5, (leftMost - arrowSprite.width, arrowSprite.top + arrowSprite.height / 2.0)), (6, (leftMost, arrowSprite.top))]
        else:
            extraVertices = [(2, (rightMost, arrowSprite.top)), (3, (rightMost + arrowSprite.width, arrowSprite.top + arrowSprite.height / 2.0)), (4, (rightMost, arrowSprite.top + arrowSprite.height))]
        vectorLine.AddPoint((uicore.ScaleDpi(leftMost), uicore.ScaleDpi(top)), color=TutorialColor.HINT_FRAME)
        vectorLine.AddPoint((uicore.ScaleDpi(rightMost), uicore.ScaleDpi(top)), color=TutorialColor.HINT_FRAME)
        vectorLine.AddPoint((uicore.ScaleDpi(rightMost), uicore.ScaleDpi(bottom)), color=TutorialColor.HINT_FRAME)
        vectorLine.AddPoint((uicore.ScaleDpi(leftMost), uicore.ScaleDpi(bottom)), color=TutorialColor.HINT_FRAME)
        for idx, pos in extraVertices:
            posX = uicore.ScaleDpi(pos[0])
            posY = uicore.ScaleDpi(pos[1])
            vectorLine.AddPoint((posX, posY), idx=idx, color=TutorialColor.HINT_FRAME)

        uicore.animations.SpSwoopBlink(self.blinkSprite, rotation=math.pi - 0.5, duration=3.0, loops=TutorialConstants.NUM_BLINKS)

    def OnMouseEnter(self, *args):
        self.headerButtons.Show()
        self.closeButtonTimer = base.AutoTimer(2000, self.headerButtons.Hide)

    def OnMouseExit(self, *args):
        if not uiutil.IsUnder(uicore.uilib.GetMouseOver(), self):
            self.headerButtons.display = False

    def OnClosePointer(self, *args):
        sm.GetService('uipointerSvc').ClearPointers()