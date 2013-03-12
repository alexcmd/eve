#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/infoPanels/infoPanelContainer.py
import uicls
import uiconst
import infoPanel
import util
import uiutil
import math
import uthread
import blue
import log
from infoPanel import MODE_COLLAPSED, MODE_COMPACT, MODE_NORMAL

class InfoPanelContainer(uicls.ContainerAutoSize):
    __guid__ = 'uicls.InfoPanelContainer'
    default_name = 'InfoPanelContainer'
    ICONSIZE = 18

    def ApplyAttributes(self, attributes):
        uicls.ContainerAutoSize.ApplyAttributes(self, attributes)
        self.infoPanelsByTypeID = {}
        self.infoPanelButtonsByTypeID = {}
        self.isDraggingButton = False
        self.topCont = uicls.Container(name='topCont', parent=self, align=uiconst.TOTOP, height=self.ICONSIZE, padding=(infoPanel.LEFTPAD,
         0,
         0,
         5))
        self.dropIndicatorLine = uicls.Line(name='dropIndicatorLine', parent=self.topCont, align=uiconst.TOLEFT_NOPUSH, state=uiconst.UI_HIDDEN, color=util.Color.GetGrayRGBA(1.0, 0.6), padding=(0, 2, 0, 2))
        self.iconCont = uicls.ContainerAutoSize(name='iconCont', parent=self.topCont, state=uiconst.UI_NORMAL, align=uiconst.TOLEFT)
        self.mainCont = uicls.ContainerAutoSize(name='mainCont', parent=self, align=uiconst.TOTOP)
        self.Reconstruct()

    def ConstructTopIcons(self):
        self.iconCont.Flush()
        infoPanelSvc = sm.GetService('infoPanel')
        for infoPanelCls in infoPanelSvc.GetCurrentPanelClasses():
            button = uicls.ButtonIconInfoPanel(infoPanelCls=infoPanelCls, name=infoPanelCls.__guid__, parent=self.iconCont, controller=self, texturePath=infoPanelCls.default_iconTexturePath, func=infoPanelCls.OnPanelContainerIconPressed, align=uiconst.TOLEFT, width=self.ICONSIZE)
            if not infoPanelCls.IsAvailable():
                button.Hide()
            self.infoPanelButtonsByTypeID[infoPanelCls.panelTypeID] = button

    def ConstructInfoPanels(self):
        infoPanelSvc = sm.GetService('infoPanel')
        self.mainCont.Flush()
        for infoPanelCls in infoPanelSvc.GetCurrentPanelClasses():
            mode = infoPanelSvc.GetModeForPanel(infoPanelCls.panelTypeID)
            panel = infoPanelCls(parent=self.mainCont, mode=mode)
            self.infoPanelsByTypeID[infoPanelCls.panelTypeID] = panel
            if not infoPanelCls.IsAvailable():
                panel.Hide()

        infoPanelSvc.CheckAllPanelsFit()

    def Reconstruct(self, animate = False):
        uthread.Lock(self)
        try:
            self.ConstructTopIcons()
            if animate:
                uicore.animations.FadeOut(self.mainCont, sleep=True, duration=0.3)
            self.ConstructInfoPanels()
            uicore.animations.FadeIn(self.mainCont, duration=0.3)
        finally:
            uthread.UnLock(self)

    def ClosePanel(self, panelTypeID):
        panel = self.GetPanelByTypeID(panelTypeID)
        if panel:
            self.infoPanelsByTypeID.pop(panelTypeID)
            panel.Close()

    def GetPanelByTypeID(self, panelTypeID):
        return self.infoPanelsByTypeID.get(panelTypeID, None)

    def GetPanelButtonByTypeID(self, panelTypeID):
        return self.infoPanelButtonsByTypeID.get(panelTypeID, None)

    def OnButtonDragStart(self, infoPanelCls):
        self.isDraggingButton = infoPanelCls
        uicore.uilib.RegisterForTriuiEvents(uiconst.UI_MOUSEMOVE, self.OnButtonDragMove)

    def OnButtonDragEnd(self, infoPanelCls):
        self.dropIndicatorLine.Hide()
        self.isDraggingButton = False
        if self.IsDraggingOverIcons():
            idx = self.GetDropIconIdx()
            if idx < len(self.mainCont.children):
                currAtIdx = self.mainCont.children[idx]
                oldTypeID = currAtIdx.panelTypeID
            else:
                oldTypeID = None
            sm.GetService('infoPanel').MovePanelInFrontOf(infoPanelCls, oldTypeID)

    def OnButtonDragMove(self, *args):
        if not self.isDraggingButton:
            return False
        if self.IsDraggingOverIcons():
            self.dropIndicatorLine.state = uiconst.UI_DISABLED
            self.SetDropIndicatorLinePosition()
        else:
            self.dropIndicatorLine.Hide()
        return True

    def IsDraggingOverIcons(self):
        return uiutil.IsUnder(uicore.uilib.mouseOver, self.iconCont) or uicore.uilib.mouseOver == self.iconCont

    def SetDropIndicatorLinePosition(self):
        idx = self.GetDropIconIdx()
        dragIdx = sm.GetService('infoPanel').GetCurrentPanelTypes().index(self.isDraggingButton.panelTypeID)
        if idx in (dragIdx, dragIdx + 1):
            self.dropIndicatorLine.Hide()
        else:
            self.dropIndicatorLine.Show()
        numIcons = self.GetNumVisible()
        left, _, width, _ = self.iconCont.GetAbsolute()
        self.dropIndicatorLine.left = idx * (width / numIcons) - 2

    def GetDropIconIdx(self):
        numIcons = self.GetNumVisible()
        left, _, width, _ = self.iconCont.GetAbsolute()
        x = uicore.uilib.x - left
        numSlots = numIcons * 2
        pos = max(0, min(x / float(width), 1.0))
        idx = numSlots * pos
        idx = int(float(idx) / 2 + 0.5)
        return idx

    def GetNumVisible(self):
        return len([ child for child in self.iconCont.children if child.display ])

    def IsLastPanelClipped(self):
        if self.destroyed:
            return
        if not self.mainCont.children:
            return False
        lastChild = self.GetLastVisiblePanel()
        if not lastChild:
            return False
        _, pt, _, ph = self.parent.GetAbsolute()
        if ph == 0:
            log.LogWarn("InfoPanels: Container parent height is zero, so don't collapse any panels")
            return False
        _, t, _, h = lastChild.GetAbsolute()
        return t - pt + h > ph

    def GetLastVisiblePanel(self):
        children = self.mainCont.children[:]
        children.reverse()
        for child in children:
            if child.mode != MODE_COLLAPSED:
                return child


class ButtonIconInfoPanel(uicls.ButtonIcon):
    __guid__ = 'uicls.ButtonIconInfoPanel'
    __notifyevents__ = ['OnInfoPanelSettingChanged']
    default_padRight = 4
    default_iconSize = 18
    isDragObject = True

    def ApplyAttributes(self, attributes):
        uicls.ButtonIcon.ApplyAttributes(self, attributes)
        sm.RegisterNotify(self)
        self.utilMenu = None
        self.controller = attributes.controller
        self.infoPanelCls = attributes.infoPanelCls
        self.bgCollapsedFill = uicls.Fill(bgParent=self, opacity=0.0)
        self.UpdateMode()

    def GetHint(self):
        return self.infoPanelCls.GetClassHint()

    def OnInfoPanelSettingChanged(self, panelTypeID, mode):
        if panelTypeID == self.infoPanelCls.panelTypeID:
            self.UpdateMode()

    def UpdateMode(self):
        mode = self.GetMode()
        if mode == MODE_COLLAPSED:
            self.opacity = 1.0
            self.bgCollapsedFill.opacity = 0.15
        else:
            self.opacity = 0.5
            self.bgCollapsedFill.opacity = 0.0

    def GetMode(self):
        return sm.GetService('infoPanel').GetModeForPanel(self.infoPanelCls.panelTypeID)

    def GetDragData(self):
        self.controller.OnButtonDragStart(self.infoPanelCls)
        return (InfoPanelDragData(self.infoPanelCls),)

    def OnEndDrag(self, *args):
        uicls.ButtonIcon.OnEndDrag(self, *args)
        self.controller.OnButtonDragEnd(self.infoPanelCls)

    def OnMouseEnter(self):
        uicls.ButtonIcon.OnMouseEnter(self)
        uthread.new(self._OnMouseEnter)

    def _OnMouseEnter(self):
        if self.GetMode() != infoPanel.MODE_COLLAPSED:
            return
        blue.synchro.SleepWallclock(300)
        if self.GetMode() != infoPanel.MODE_COLLAPSED:
            return
        if uicore.uilib.leftbtn or uicore.uilib.mouseOver != self:
            return
        if self.utilMenu and not self.utilMenu.destroyed:
            return
        uicore.layer.utilmenu.Flush()
        self.utilMenu = uicls.ExpandedUtilMenu(parent=uicore.layer.utilmenu, controller=self, minWidth=infoPanel.PANELWIDTH + 10, menuAlign=uiconst.TOPLEFT, GetUtilMenu=self.GetUtilMenu)

    def GetUtilMenu(self, parent):
        cont = uicls.ContainerAutoSize(parent=parent, align=uiconst.TOTOP, padRight=10)
        self.infoPanelCls(parent=cont, mode=infoPanel.MODE_NORMAL, isModeFixed=True)

    def OnDblClick(self, *args):
        pass


class InfoPanelDragData:
    __guid__ = 'uiutil.InfoPanelDragData'

    def __init__(self, infoPanelCls):
        self.infoPanelCls = infoPanelCls