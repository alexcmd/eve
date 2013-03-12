#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/control/scrollContainer.py
import uicls
import uiconst
import uthread
import blue
import util
import math
import uiutil

class ScrollContainerCore(uicls.Container):
    __guid__ = 'uicls.ScrollContainerCore'
    default_name = 'scrollContainer'
    default_state = uiconst.UI_NORMAL
    dragHoverScrollAreaSize = 30
    dragHoverScrollSpeed = 60.0
    isTabStop = True

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.scrollbarsDisabled = False
        self.scrollToVerticalPending = None
        self.scrollToHorizontalPending = None
        self.verticalScrollBar = uicls.ScrollBar(parent=self, align=uiconst.TORIGHT)
        self.verticalScrollBar.OnScrolled = self._OnVerticalScrollBar
        self.horizontalScrollBar = uicls.ScrollBar(parent=self, align=uiconst.TOBOTTOM)
        self.horizontalScrollBar.OnScrolled = self._OnHorizontalScrollBar
        self.clipCont = uicls.Container(name='clipCont', parent=self, clipChildren=True)
        self.mainCont = uicls.ContainerAutoSize(name='mainCont', parent=self.clipCont)
        self.mainCont._OnSizeChange_NoBlock = self._OnMainContSizeChange
        self.children.insert = self._InsertChild
        self.children.append = self._AppendChild
        self.children.remove = self._RemoveChild
        self._mouseHoverCookie = uicore.uilib.RegisterForTriuiEvents(uiconst.UI_MOUSEHOVER, self.OnGlobalMouseHover)

    def Close(self, *args):
        uicore.uilib.UnregisterForTriuiEvents(self._mouseHoverCookie)
        uicls.Container.Close(self, *args)

    def _InsertChild(self, idx, obj):
        self.mainCont.children.insert(idx, obj)
        self.mainCont.align = obj.align

    def _AppendChild(self, idx, obj):
        self.mainCont.children.append(obj)
        self.mainCont.align = obj.align

    def _RemoveChild(self, obj):
        self.mainCont.children.remove(obj)

    def OnGlobalMouseHover(self, obj, *args):
        if uicore.IsDragging() and (obj == self or uiutil.IsUnder(obj, self.mainCont)):
            l, t, w, h = self.GetAbsolute()
            if self.verticalScrollBar.display and h > 0:
                fraction = self.dragHoverScrollSpeed / float(h)
                y = uicore.uilib.y - t
                if y <= self.dragHoverScrollAreaSize:
                    self.ScrollMoveVertical(-fraction)
                    self.verticalScrollBar.AnimFade()
                elif y > h - self.dragHoverScrollAreaSize:
                    self.ScrollMoveVertical(fraction)
                    self.verticalScrollBar.AnimFade()
            if self.horizontalScrollBar.display and w > 0:
                fraction = self.dragHoverScrollSpeed / float(w)
                x = uicore.uilib.x - l
                if x <= self.dragHoverScrollAreaSize:
                    self.ScrollMoveHorizontal(-fraction)
                    self.horizontalScrollBar.AnimFade()
                elif x > w - self.dragHoverScrollAreaSize:
                    self.ScrollMoveHorizontal(fraction)
                    self.horizontalScrollBar.AnimFade()
        return True

    def _OnSizeChange_NoBlock(self, width, height):
        self._UpdateHandleSizesAndPosition(width, height)

    def _OnMainContSizeChange(self, width, height):
        self._UpdateScrollbars()

    def Flush(self):
        self.mainCont.Flush()

    def DisableScrollbars(self):
        self.scrollbarsDisabled = True
        self._UpdateScrollbars()

    def EnableScrollbars(self):
        self.scrollbarsDisabled = False
        self._UpdateScrollbars()

    def _UpdateScrollbars(self):
        w, h = self.GetAbsoluteSize()
        self._UpdateHandleSizesAndPosition(w, h)

    def _UpdateHandleSizesAndPosition(self, width, height):
        if self.mainCont.height > 0 and not self.scrollbarsDisabled:
            size = float(height) / self.mainCont.height
        else:
            size = 1.0
        self.verticalScrollBar.SetScrollHandleSize(size)
        denum = self.mainCont.height - height
        if denum <= 0.0:
            pos = 0.0
        else:
            pos = float(-self.mainCont.top) / denum
        self.verticalScrollBar.ScrollTo(pos)
        self._OnVerticalScrollBar(pos)
        if self.mainCont.width != 0 and not self.scrollbarsDisabled:
            size = float(width) / self.mainCont.width
        else:
            size = 1.0
        self.horizontalScrollBar.SetScrollHandleSize(size)
        denum = self.mainCont.width - width
        if denum <= 0.0:
            pos = 0.0
        else:
            pos = float(-self.mainCont.left) / denum
        self.horizontalScrollBar.ScrollTo(pos)
        self._OnHorizontalScrollBar(pos)
        if self.horizontalScrollBar.display and self.verticalScrollBar.display:
            self.verticalScrollBar.padBottom = self.horizontalScrollBar.height
        else:
            self.verticalScrollBar.padBottom = 0

    def _OnVerticalScrollBar(self, posFraction):
        w, h = self.clipCont.GetAbsoluteSize()
        posFraction = max(0.0, min(posFraction, 1.0))
        self.mainCont.top = -posFraction * (self.mainCont.height - h)
        self.OnScrolledVertical(posFraction)

    def _OnHorizontalScrollBar(self, posFraction):
        w, h = self.clipCont.GetAbsoluteSize()
        posFraction = max(0.0, min(posFraction, 1.0))
        self.mainCont.left = -posFraction * (self.mainCont.width - w)
        self.OnScrolledHorizontal(posFraction)

    def OnScrolledHorizontal(self, posFraction):
        pass

    def OnScrolledVertical(self, posFraction):
        pass

    def ScrollToVertical(self, posFraction):
        if self._alignmentDirty:
            self.scrollToVerticalPending = posFraction
        elif self.verticalScrollBar.display:
            self.verticalScrollBar.ScrollTo(posFraction)
            self._OnVerticalScrollBar(self.verticalScrollBar.handlePos)

    def ScrollToHorizontal(self, posFraction):
        if self._alignmentDirty:
            self.scrollToHorizontalPending = posFraction
        elif self.horizontalScrollBar.display:
            self.horizontalScrollBar.ScrollTo(posFraction)
            self._OnHorizontalScrollBar(self.horizontalScrollBar.handlePos)

    def Traverse(self, mbudget):
        ret = uicls.Container.Traverse(self, mbudget)
        if self.scrollToVerticalPending:
            self.verticalScrollBar.ScrollTo(self.scrollToVerticalPending)
            self._OnVerticalScrollBar(self.verticalScrollBar.handlePos)
        self.scrollToVerticalPending = None
        if self.scrollToHorizontalPending:
            self.horizontalScrollBar.ScrollTo(self.scrollToHorizontalPending)
            self._OnHorizontalScrollBar(self.horizontalScrollBar.handlePos)
        self.scrollToHorizontalPending = None
        return ret

    def ScrollMoveVertical(self, moveFraction):
        self.verticalScrollBar.ScrollMove(moveFraction)
        self._OnVerticalScrollBar(self.verticalScrollBar.handlePos)

    def ScrollMoveHorizontal(self, moveFraction):
        self.horizontalScrollBar.ScrollMove(moveFraction)
        self._OnHorizontalScrollBar(self.horizontalScrollBar.handlePos)

    def OnMouseWheel(self, dz):
        if self.verticalScrollBar.display:
            prop = -dz / float(self.mainCont.height)
            if math.fabs(prop) < 0.1:
                prop = math.copysign(0.1, prop)
            self.ScrollMoveVertical(prop)
            self.verticalScrollBar.AnimFade()
        elif self.horizontalScrollBar.display:
            prop = -dz / float(self.mainCont.width)
            if math.fabs(prop) < 0.1:
                prop = math.copysign(0.1, prop)
            self.ScrollMoveHorizontal(prop)
            self.horizontalScrollBar.AnimFade()


class ScrollBarCore(uicls.Container):
    __guid__ = 'uicls.ScrollBarCore'
    default_name = 'scrollBar'
    default_align = uiconst.TORIGHT
    default_state = uiconst.UI_NORMAL
    default_width = 7
    default_height = 6
    VERTICAL = 1
    HORIZONTAL = 2
    default_scrollSpeed = 0.05

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.scrollSpeed = attributes.get('scrollSpeed', self.default_scrollSpeed)
        self.handleSize = 0.5
        self.handlePos = 0.0
        self.mouseDownThread = None
        self.animFadeThread = None
        self.PrepareUnderlay_()
        if self.align in (uiconst.TORIGHT, uiconst.TOLEFT):
            self.PrepareVertical_()
            self.orientation = self.VERTICAL
        elif self.align in (uiconst.TOTOP, uiconst.TOBOTTOM):
            self.PrepareHorizontal_()
            self.orientation = self.HORIZONTAL
        else:
            raise ValueError('Scrollbars must have TOBOTTOM, TOTOP, TOLEFT or TORIGHT alignments')
        self.scrollHandle.OnMouseDown = self._OnScrollHandleMouseDown
        self.scrollHandle.OnMouseUp = self._OnScrollHandleMouseUp

    def PrepareUnderlay_(self):
        self.underlay = uicls.Fill(name='underlay', bgParent=self, color=util.Color.GetGrayRGBA(0.3, 0.1), shadowOffset=(-1, 0))

    def PrepareVertical_(self):
        self.handleCont = uicls.Container(name='handleCont', parent=self, align=uiconst.TOALL)
        self.scrollHandle = uicls._ScrollHandle(name='scrollhandle', parent=self.handleCont, align=uiconst.TOTOP_PROP, state=uiconst.UI_NORMAL, height=self.handleSize)

    def PrepareHorizontal_(self):
        self.handleCont = uicls.Container(name='handleCont', parent=self, align=uiconst.TOALL)
        self.scrollHandle = uicls._ScrollHandle(name='scrollhandle', parent=self.handleCont, align=uiconst.TOLEFT_PROP, state=uiconst.UI_NORMAL, width=self.handleSize)

    def _OnScrollHandleMouseDown(self, *args):
        uicls._ScrollHandle.OnMouseDown(self.scrollHandle, *args)
        uthread.new(self._DragScrollHandleThread)

    def _OnScrollHandleMouseUp(self, *args):
        uicls._ScrollHandle.OnMouseUp(self.scrollHandle, *args)

    def _DragScrollHandleThread(self):
        left, top = self.handleCont.GetAbsolutePosition()
        handleLeft, handleTop = self.scrollHandle.GetAbsolutePosition()
        maxLeft, maxTop = self._GetHandleMaxPos()
        if self.orientation == self.HORIZONTAL:
            xOffset = uicore.uilib.x - handleLeft
            while uicore.uilib.leftbtn:
                x = uicore.uilib.x - left - xOffset
                self.ScrollTo(float(x) / maxLeft)
                self.OnScrolled(self.handlePos)
                blue.synchro.Yield()

        else:
            yOffset = uicore.uilib.y - handleTop
            while uicore.uilib.leftbtn:
                y = uicore.uilib.y - top - yOffset
                self.ScrollTo(float(y) / maxTop)
                self.OnScrolled(self.handlePos)
                blue.synchro.Yield()

    def OnMouseDown(self, *args):
        left, top, width, height = self.handleCont.GetAbsolute()
        if self.orientation == self.VERTICAL:
            posFraction = (uicore.uilib.y - top) / float(height)
            self.ScrollTo(posFraction)
            self.OnScrolled(posFraction)
        else:
            posFraction = (uicore.uilib.x - left) / float(width)
            self.ScrollTo(posFraction)
            self.OnScrolled(posFraction)

    def SetScrollHandleSize(self, sizeFraction):
        sizeFraction = max(0.0, min(sizeFraction, 1.0))
        self.display = sizeFraction != 1.0
        if self.orientation == self.HORIZONTAL:
            self.scrollHandle.width = max(0.05, sizeFraction)
        else:
            self.scrollHandle.height = max(0.05, sizeFraction)
        self.handleSize = sizeFraction
        self.ScrollTo(self.handlePos)

    def _GetHandleMaxPos(self):
        width, height = self.handleCont.GetAbsoluteSize()
        handleWidth, handleHeight = self.scrollHandle.GetAbsoluteSize()
        maxLeft = width - handleWidth
        maxTop = height - handleHeight
        return (maxLeft, maxTop)

    def ScrollTo(self, posFraction):
        posFraction = max(0.0, min(posFraction, 1.0))
        maxLeft, maxTop = self._GetHandleMaxPos()
        if self.orientation == self.HORIZONTAL:
            self.scrollHandle.left = posFraction * maxLeft
        else:
            self.scrollHandle.top = posFraction * maxTop
        self.handlePos = posFraction

    def ScrollMove(self, moveFraction):
        self.ScrollTo(self.handlePos + moveFraction * self.handleSize)

    def OnScrolled(self, posFraction):
        pass

    def AnimFade(self):
        self.fadeEndTime = blue.os.GetTime() + 0.3 * SEC
        if not self.animFadeThread:
            uicore.animations.FadeIn(self.scrollHandle.hilite, 0.5, duration=0.1)
            uthread.new(self._AnimFadeThread)

    def _AnimFadeThread(self):
        while blue.os.GetTime() < self.fadeEndTime:
            blue.synchro.Yield()

        if uicore.uilib.mouseOver != self.scrollHandle:
            uicore.animations.FadeOut(self.scrollHandle.hilite, duration=0.5)
        self.animFadeThread = None


class _ScrollHandleCore(uicls.Container):
    __guid__ = 'uicls._ScrollHandleCore'
    default_name = 'scrollHandle'
    default_width = 50
    default_height = 50

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.sr.hilite = None
        self._dragging = False
        self.Prepare_()

    def Prepare_(self):
        uicls.GradientSprite(bgParent=self, rotation=0, rgbData=[(0, (1.0, 1.0, 1.0))], alphaData=[(0.0, 0.0),
         (0.1, 0.1),
         (0.9, 0.1),
         (1.0, 0.0)])
        self.hilite = uicls.Fill(name='hilite', parent=self, color=(1.0, 1.0, 1.0, 0.0))

    def OnMouseDown(self, btn, *args):
        pass

    def OnMouseMove(self, *etc):
        pass

    def OnMouseUp(self, btn, *args):
        pass

    def OnMouseEnter(self, *args):
        uicore.animations.FadeIn(self.hilite, 0.5, duration=0.2)

    def OnMouseExit(self, *args):
        uicore.animations.FadeOut(self.hilite, duration=0.2)