#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/control/expandablemenu.py
import xtriui
import uix
import uiutil
import mathUtil
import uthread
import blue
import uicls
import uiconst
import random

class ExpandableMenuContainer(uicls.Container):
    __guid__ = 'xtriui.ExpandableMenuContainer'

    def init(self):
        self.sizecallback = None
        self.multipleExpanded = False
        self.headerApperance = 'default'
        self.sr.menus = []
        self.sr.menusByLabel = {}

    def _OnClose(self):
        self.sizecallback = None
        self.sr.menus = None
        self.sr.menusByLabel = None

    def Load(self, menuData, prefsKey = None):
        self.singleton = bool(len(menuData) == 1)
        for data in menuData:
            em = xtriui.ExpandableMenu(parent=self, align=uiconst.TOTOP, height=18, state=uiconst.UI_NORMAL, name=data[0], padBottom=4)
            em.prefsKey = prefsKey
            self.sr.menus.append(em)
            self.sr.menusByLabel[data[0]] = em
            em.Load(*data)

        if prefsKey and not self.multipleExpanded:
            active = settings.user.ui.Get('expandableMenu', {}).get(prefsKey, None)
            if active:
                for each in self.children:
                    if each.name == active:
                        uthread.new(each.Expand)

            else:
                uthread.new(self.children[0].Expand)

    def AutoCollapseIfNeeded(self, ignoreMenu = None):
        if getattr(self, '_autoCollapsing', False):
            return
        self._autoCollapsing = True
        blue.pyos.synchro.SleepWallclock(10)
        expanded = []
        totalHeight = 0
        for each in self.children:
            totalHeight += each.height + each.padTop + each.padBottom
            if isinstance(each, xtriui.ExpandableMenu) and each._expanded and each is not ignoreMenu:
                expanded.append(each)

        pl, pt, pw, ph = self.GetAbsolute()
        collapseMenus = []
        random.shuffle(expanded)
        while totalHeight > ph and expanded:
            collapse = expanded.pop()
            collapseMenus.append(collapse)
            totalHeight -= collapse.height

        for each in collapseMenus:
            each.Collapse()

        self._autoCollapsing = False

    def ExpandMenuByLabel(self, label):
        if label in self.sr.menusByLabel:
            self.sr.menusByLabel[label].Expand()

    def _OnSizeChange_NoBlock(self, *args, **kwds):
        uicls.Container._OnSizeChange_NoBlock(self, *args, **kwds)
        for each in self.children:
            if not each._changing and each._expanded:
                endHeight = each.GetExpandedHeight()
                each.height = endHeight
                each.sr.content.height = endHeight - each.GetCollapsedHeight() - each.sr.content.top


class ExpandableMenu(uicls.Container):
    __guid__ = 'xtriui.ExpandableMenu'
    default_clipChildren = True

    def AddHeaderContent(self, content, hideOnMaximize = 1):
        self._hideHeaderContentOnMaximize = hideOnMaximize
        self.sr.headerContent = content
        self.sr.headerParent.children.insert(0, content)
        if self.sr.content.state == uiconst.UI_HIDDEN:
            self.sr.headerContent.opacity = 1.0
        elif hideOnMaximize:
            self.sr.headerContent.opacity = 0.0

    def Load(self, label, content, callback, dropCallback = None, maxHeight = None, headerContent = None, hideHeaderContentOnMaximize = 1, expandedByDefault = 1):
        self._changing = False
        self._break = False
        self._expanded = False
        self._maxHeight = maxHeight
        self._loaded = False
        self._lastExpandedHeight = None
        self._hideHeaderContentOnMaximize = hideHeaderContentOnMaximize
        headerParent = uicls.Container(parent=self, name='headerParent', align=uiconst.TOTOP, state=uiconst.UI_PICKCHILDREN, height=24, padBottom=-1)
        self.sr.headerParent = headerParent
        contentParent = uicls.Container(parent=self, name='contentParent', align=uiconst.TOALL, state=uiconst.UI_NORMAL, pos=(0, 1, 0, 1))
        self.sr.content = content
        self.sr.callback = callback
        if dropCallback:
            self.OnDropData = dropCallback
        t = uicls.EveLabelMedium(text='<b>' + label + '</b>', parent=headerParent, state=uiconst.UI_DISABLED, left=22, top=1, align=uiconst.CENTERLEFT)
        self.sr.headerLabel = t
        self._headerLabel = label
        expander = uicls.Icon(icon='ui_38_16_228', align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, left=4, top=1)
        expander.SetAlpha(0.8)
        headerParent.children.append(expander)
        self.sr.backgroundFrame = uicls.RaisedUnderlay(bgParent=headerParent, alphaDiff=0.15)
        self.sr.expanderIcon = expander
        headerParent.height = max(20, t.textheight + 2)
        self._minHeight = headerParent.height
        if content:
            contentParent.children.append(content)
        if headerContent:
            self.AddHeaderContent(headerContent, hideHeaderContentOnMaximize)
        if self.parent.multipleExpanded:
            current = settings.user.ui.Get('multipleExpandableMenu', {})
            if self.prefsKey in current and self.name in current[self.prefsKey]:
                lastHeight, expanded = current[self.prefsKey][self.name]
                if expanded:
                    uthread.new(self.Expand, lastHeight, startup=True)
                    return
            elif expandedByDefault:
                uthread.new(self.Expand, startup=True)
                return
        self.Collapse(startup=1)
        self._loaded = True

    def SetHeader(self, newlabel, addon = 0, hint = None):
        if addon:
            newlabel = self._headerLabel + newlabel
        self.sr.headerLabel.text = '<b>' + newlabel + '</b>'
        if hint:
            self.sr.headerLabel.state = uiconst.UI_NORMAL
            self.sr.headerLabel.hint = hint
            self.sr.headerLabel.OnClick = self.OnClick
        else:
            self.sr.headerLabel.state = uiconst.UI_DISABLED

    def OnClick(self, *args):
        if not self._changing:
            if self._expanded:
                self.Collapse()
            else:
                self.Expand()

    def Expand(self, lastHeight = None, time = None, startup = False, *args):
        if self._changing:
            return
        self._changing = True
        if not self.parent.multipleExpanded:
            for each in self.parent.children[:]:
                if isinstance(each, ExpandableMenu) and each is not self:
                    uthread.new(each.Collapse)

        if self.sr.callback:
            self.sr.callback(not self._loaded)
        self.sr.content.align = uiconst.TOTOP
        self._loaded = True
        sh = self.height
        endHeight = self.GetExpandedHeight()
        self.sr.expanderIcon.LoadIcon('ui_38_16_229')
        self.sr.content.state = uiconst.UI_NORMAL
        self.sr.content.height = endHeight - self.GetCollapsedHeight() - self.sr.content.top
        if time == -1:
            self.height = endHeight
            self.sr.content.opacity = 1.0
            if self.parent.sizecallback:
                self.parent.sizecallback(self)
        else:
            start, ndt = blue.os.GetWallclockTime(), 0.0
            time = time or 250.0
            while ndt != 1.0:
                ndt = max(ndt, min(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime()) / time, 1.0))
                self.height = sh + int((endHeight - sh) * ndt)
                self.sr.content.opacity = 1.0 * ndt
                if self.sr.headerContent and self._hideHeaderContentOnMaximize:
                    self.sr.headerContent.opacity = 1.0 - 1.0 * ndt
                if self.parent.sizecallback:
                    self.parent.sizecallback(self)
                blue.pyos.synchro.Yield()
                if self.destroyed or self._break:
                    break

        if self.destroyed:
            return
        self.height = endHeight
        self._changing = False
        self._break = False
        self._expanded = True
        self._lastExpandedHeight = self.height
        self.sr.content.opacity = 1.0
        if self.sr.headerContent and self._hideHeaderContentOnMaximize:
            self.sr.headerContent.opacity = 0.0
        if startup:
            uthread.new(self.parent.AutoCollapseIfNeeded)
        else:
            uthread.new(self.parent.AutoCollapseIfNeeded, ignoreMenu=self)
        self.Register()

    def Register(self):
        if self.prefsKey:
            if self.parent.multipleExpanded:
                current = settings.user.ui.Get('multipleExpandableMenu', {})
                if self.prefsKey not in current:
                    current[self.prefsKey] = {}
                current[self.prefsKey][self.name] = (self._lastExpandedHeight, self._expanded)
                settings.user.ui.Set('multipleExpandableMenu', current)
            else:
                current = settings.user.ui.Get('expandableMenu', {})
                if self._expanded:
                    current[self.prefsKey] = self.name
                elif self.prefsKey in current and current[self.prefsKey] == self.name:
                    del current[self.prefsKey]
                settings.user.ui.Set('expandableMenu', current)

    def Collapse(self, startup = 0):
        if self._changing:
            self._break = True
        self._changing = True
        sh = self.height
        endHeight = self.GetCollapsedHeight()
        pl, pt, pw, ph = self.parent.GetAbsolute()
        self.sr.expanderIcon.LoadIcon('ui_38_16_228')
        if not startup:
            if self.sr.headerContent:
                sho = self.sr.headerContent.opacity
            start, ndt = blue.os.GetWallclockTime(), 0.0
            time = 250.0
            while ndt != 1.0:
                ndt = max(ndt, min(blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime()) / time, 1.0))
                self.height = sh - int((sh - endHeight) * ndt)
                self.sr.content.opacity = 1.0 - 1.0 * ndt
                if self.sr.headerContent and self._hideHeaderContentOnMaximize:
                    self.sr.headerContent.opacity = mathUtil.Lerp(sho, 1.0, ndt)
                if self.parent.sizecallback:
                    self.parent.sizecallback(self)
                blue.pyos.synchro.Yield()
                if self.destroyed or self._break:
                    break

        if self.destroyed:
            return
        self._changing = False
        self._break = False
        self.height = endHeight
        self._expanded = False
        self.sr.content.state = uiconst.UI_HIDDEN
        self.sr.content.opacity = 0.0
        if self.sr.headerContent:
            self.sr.headerContent.opacity = 1.0
        if not startup:
            self.Register()

    def GetCollapsedHeight(self):
        return self._minHeight

    def GetExpandedHeight(self):
        endHeight = self.GetMaxHeight()
        if not endHeight and not self.parent.multipleExpanded:
            pw, ph = self.parent.GetAbsoluteSize()
            total = 0
            for each in self.parent.children:
                if isinstance(each, ExpandableMenu):
                    total += each.GetCollapsedHeight()

            endHeight = ph - total
        return endHeight

    def GetMaxHeight(self):
        if hasattr(self.sr.content, 'GetTotalHeight'):
            totalHeight = self.sr.content.top + self.sr.content.GetTotalHeight() + self.GetCollapsedHeight() + 5
            if self._maxHeight:
                return min(totalHeight, self._maxHeight)
            return totalHeight
        if hasattr(self.sr.content, 'GetContentHeight'):
            totalHeight = self.sr.content.top + self.sr.content.GetContentHeight() + self.GetCollapsedHeight() + 5
            if self._maxHeight:
                return min(totalHeight, self._maxHeight)
            return totalHeight
        return self._maxHeight