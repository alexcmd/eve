#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/control/dragResizeCont.py
import uicls
import uiconst

class DragResizeCont(uicls.Container):
    __guid__ = 'uicls.DragResizeCont'
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL
    default_maxSize = 200
    default_minSize = 50
    default_defaultSize = 150
    default_settingsID = None
    default_dragAreaSize = 4

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.maxSize = attributes.Get('maxSize', self.default_maxSize)
        self.minSize = attributes.Get('minSize', self.default_minSize)
        self.settingsID = attributes.Get('settingsID', self.default_settingsID)
        self.onResizeCallback = attributes.Get('onResizeCallback', None)
        dragAreaSize = attributes.Get('dragAreaSize', self.default_dragAreaSize)
        defaultSize = attributes.Get('defaultSize', self.default_defaultSize)
        dividerAlign = {uiconst.TOLEFT: uiconst.TORIGHT,
         uiconst.TORIGHT: uiconst.TOLEFT,
         uiconst.TOTOP: uiconst.TOBOTTOM,
         uiconst.TOBOTTOM: uiconst.TOTOP,
         uiconst.TOLEFT_PROP: uiconst.TORIGHT,
         uiconst.TORIGHT_PROP: uiconst.TOLEFT,
         uiconst.TOTOP_PROP: uiconst.TOBOTTOM,
         uiconst.TOBOTTOM_PROP: uiconst.TOTOP}
        if self.align not in dividerAlign:
            raise ValueError('Invalid alignment mode selected. Must be push aligned to LEFT, TOP, RIGHT or BOTTOM')
        self.isHorizontal = self.align in (uiconst.TOLEFT,
         uiconst.TORIGHT,
         uiconst.TOLEFT_PROP,
         uiconst.TORIGHT_PROP)
        self.isProportional = self.align in (uiconst.TOLEFT_PROP,
         uiconst.TOTOP_PROP,
         uiconst.TORIGHT_PROP,
         uiconst.TOBOTTOM_PROP)
        self.isInverse = self.align in (uiconst.TORIGHT,
         uiconst.TORIGHT_PROP,
         uiconst.TOBOTTOM,
         uiconst.TOBOTTOM_PROP)
        self.isDraggin = False
        self.initialPos = None
        size = settings.user.ui.Get(self.settingsID, defaultSize)
        self._SetSize(size)
        self.dragArea = uicls.Container(name='dragArea', parent=self, state=uiconst.UI_NORMAL, align=dividerAlign[self.align], width=dragAreaSize, height=dragAreaSize)
        self.dragArea.cursor = 18 if self.isHorizontal else 11
        self.dragArea.OnMouseDown = self.OnDragAreaMouseDown
        self.dragArea.OnMouseUp = self.OnDragAreaMouseUp
        self.dragArea.OnMouseMove = self.OnDragAreaMouseMove
        self.mainCont = uicls.Container(parent=self, name='mainCont')

    def _GetPos(self):
        if self.isHorizontal:
            return uicore.uilib.x
        return uicore.uilib.y

    def OnDragAreaMouseDown(self, *args):
        self.isDraggin = True
        self.initialPos = self._GetPos()
        self.parSize = self._GetParSize()

    def DisableDragResize(self):
        self.dragArea.Disable()

    def EnableDragResize(self):
        self.dragArea.Enable()

    def _GetParSize(self):
        parWidth, parHeight = self.parent.GetAbsoluteSize()
        parSize = parWidth if self.isHorizontal else parHeight
        return parSize

    def OnDragAreaMouseUp(self, *args):
        self.isDraggin = False
        settings.user.ui.Set(self.settingsID, self._GetSize())
        if self.onResizeCallback:
            self.onResizeCallback()

    def OnDragAreaMouseMove(self, *args):
        if not self.isDraggin:
            return
        newPos = self._GetPos()
        if self.isInverse:
            self._ChangeSize(self.initialPos - newPos)
        else:
            self._ChangeSize(newPos - self.initialPos)
        l, t, w, h = self.GetAbsolute()
        if self.align in (uiconst.TOLEFT, uiconst.TOLEFT_PROP):
            self.initialPos = max(l + self.minSize, min(newPos, l + w))
        elif self.align in (uiconst.TORIGHT, uiconst.TORIGHT_PROP):
            self.initialPos = max(l, min(newPos, l + w - self.minSize))
        elif self.align in (uiconst.TOTOP, uiconst.TOTOP_PROP):
            self.initialPos = max(t + self.minSize, min(newPos, t + h))
        elif self.align in (uiconst.TOBOTTOM, uiconst.TOBOTTOM_PROP):
            self.initialPos = max(t, min(newPos, t + h - self.minSize))

    def _GetSize(self):
        if self.isHorizontal:
            return self.width
        else:
            return self.height

    def GetMaxSize(self):
        return self._ConvertSize(self.maxSize)

    def SetMaxSize(self, maxSize):
        self.maxSize = maxSize

    def GetMinSize(self):
        return self._ConvertSize(self.minSize)

    def SetMinSize(self, minSize):
        self.minSize = minSize

    def _ConvertSize(self, size):
        self.parSize = self._GetParSize()
        if size > 1:
            if self.isProportional:
                return float(size) / self.parSize
            else:
                return size
        else:
            if self.isProportional:
                return size
            return size * self.parSize

    def _OnSizeChange_NoBlock(self, width, height):
        self._UpdateSize(width, height)

    def UpdateSize(self):
        width, height = self.GetAbsoluteSize()
        self._UpdateSize(width, height)

    def _UpdateSize(self, width = None, height = None):
        if not self.pickState:
            return
        size = width if self.isHorizontal else height
        size = self._ConvertSize(size)
        minSize = self._ConvertSize(self.minSize)
        if size < minSize:
            self._SetSize(minSize)
        maxSize = self._ConvertSize(self.maxSize)
        if size > maxSize:
            self._SetSize(maxSize)

    def _SetSize(self, size):
        minSize = self._ConvertSize(self.minSize)
        maxSize = self._ConvertSize(self.maxSize)
        size = max(minSize, min(size, maxSize))
        if self.isHorizontal:
            self.width = size
        else:
            self.height = size

    def _ChangeSize(self, diff):
        size = self._GetSize()
        if self.isProportional:
            size += float(diff) / self.parSize
        else:
            size += diff
        self._SetSize(size)