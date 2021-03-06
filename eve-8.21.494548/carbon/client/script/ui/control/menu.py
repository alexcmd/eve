#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/control/menu.py
import uthread
import base
import types
import log
import util
import uicls
import uiutil
import uiconst
import localization
DISABLED_ENTRY = [-1]

class Menu(object):

    def __init__(self):
        self.entrylist = []
        self.iconSize = 0

    def AddEntry(self, name, value, icon, identifier, enabled = 1, menuClass = None):
        m = uiutil.Bunch()
        m.caption = name
        m.value = value
        m.enabled = enabled
        m.icon = icon
        m.id = identifier
        m.menuClass = menuClass
        if not m.value:
            m.enabled = False
        self.entrylist.append(m)

    def AddSeparator(self):
        self.entrylist.append(None)

    def ActivateEntry(self, name):
        entry = self._GetEntry(name)
        if not entry.enabled:
            return
        uicore.Message('MenuActivate')
        if callable(entry.value):
            uthread.new(entry.value)
        uthread.new(uiutil.Flush, uicore.layer.menu)

    def GetEntries(self):
        return self.entrylist

    def _GetEntry(self, name):
        for each in self.entrylist:
            if getattr(each, 'id', None) == name:
                return each
        else:
            raise RuntimeError('Entry not found!', name)


class DropDownMenuCore(uicls.Container):
    __guid__ = 'uicls.DropDownMenuCore'

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.sr.entries = uicls.Container(parent=self, name='_entries')
        self.Prepare_()

    def Prepare_(self, *args):
        self.SetAlign(uiconst.TOPLEFT)
        self.Prepare_Background_()

    def Prepare_Background_(self, *args):
        uicls.Frame(name='__underlay', color=(0.5, 0.5, 0.5, 0.95), frameConst=uiconst.FRAME_FILLED_SHADOW_CORNER1, parent=self)

    def _OnClose(self):
        uicls.Container._OnClose(self)
        for each in self.sr.entries.children[:]:
            if hasattr(each, 'Collapse'):
                each.Collapse()

        self.menu = None

    def Setup(self, menu, parent = None, minwidth = None):
        log.LogInfo('Menu.Setup', id(self))
        entries = menu.GetEntries()
        wasLine = 0
        idNo = 0
        for i, entry in enumerate(entries):
            if entry is None:
                if not len(self.sr.entries.children) or i == len(entries) - 1 or wasLine:
                    continue
                item = uicls.Line(align=uiconst.TOTOP, parent=self.sr.entries)
                wasLine = 1
            else:
                size = settings.user.ui.Get('cmenufontsize', 10)
                menuEntryViewClass = entry.menuClass or uicls.MenuEntryView
                item = menuEntryViewClass(name='entry', align=uiconst.TOTOP, state=uiconst.UI_NORMAL, parent=self.sr.entries)
                item.Setup(entry, size, menu, idNo)
                idNo += 1
                wasLine = 0

        self.height = sum([ each.height for each in self.sr.entries.children ]) + self.sr.entries.top + self.sr.entries.height
        if len(self.sr.entries.children):
            self.width = max(max([ each.width for each in self.sr.entries.children ]) + 8, minwidth or 0) + self.sr.entries.left + self.sr.entries.width
        else:
            self.width = 100
        self.menu = menu
        log.LogInfo('Menu.Setup Completed', id(self))

    def ActivateEntry(self, name):
        error = self.menu.ActivateEntry(name)
        if error:
            apply(uicore.Message, error)

    def Collapse(self):
        if not self.destroyed:
            for each in self.sr.entries.children:
                if hasattr(each, 'Collapse'):
                    each.Collapse()

            self.Close()

    def Next(self):
        found = None
        for each in self.sr.entries.children:
            if not isinstance(each, MenuEntryViewCore):
                continue
            if found:
                each.OnMouseEnter()
                return
            if each.sr.hilite:
                each.OnMouseExit()
                found = each

        self.sr.entries.children[0].OnMouseEnter()

    def Prev(self):
        found = None
        lst = [ each for each in self.sr.entries.children ]
        lst.reverse()
        for each in lst:
            if not isinstance(each, MenuEntryViewCore):
                continue
            if found:
                each.OnMouseEnter()
                return
            if each.sr.hilite:
                each.OnMouseExit()
                found = each

        self.sr.entries.children[-1].OnMouseEnter()

    def ChooseHilited(self):
        for each in self.sr.entries.children:
            if not isinstance(each, MenuEntryViewCore):
                continue
            if each.sr.hilite:
                self.ActivateEntry(each.id)
                return


class MenuEntryViewCore(uicls.Container):
    __guid__ = 'uicls.MenuEntryViewCore'
    LABELVERTICALPADDING = 2
    LABELHORIZONTALPADDING = 8
    default_hiliteColor = (0.0, 0.0, 0.0, 0.25)
    default_fontsize = 10
    default_fontStyle = None
    default_fontFamily = None
    default_fontPath = None

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.fontStyle = attributes.get('fontStyle', self.default_fontStyle)
        self.fontFamily = attributes.get('fontFamily', self.default_fontFamily)
        self.fontPath = attributes.get('fontPath', self.default_fontPath)
        self.fontsize = attributes.get('fontsize', self.default_fontsize)
        self.cursor = 1
        self.clicked = 0
        self.submenu = None
        self.submenuview = None
        self.sr.hilite = None
        self._hiliteColor = attributes.get('hiliteColor', self.default_hiliteColor)
        self.Prepare()

    def Prepare(self, *args):
        self.Prepare_Triangle_()
        self.Prepare_Label_()
        self.sr.label.OnMouseDown = self.OnMouseDown
        self.sr.label.OnMouseUp = self.OnMouseUp

    def Prepare_Triangle_(self, *args):
        self.triangle = uicls.Icon(icon='ui_1_16_14', parent=self, align=uiconst.CENTERRIGHT, idx=0, state=uiconst.UI_HIDDEN)

    def Prepare_Label_(self, *args):
        label = uicls.Label(parent=self, pos=(8, 1, 0, 0), align=uiconst.CENTERLEFT, letterspace=1, fontStyle=self.fontStyle, fontFamily=self.fontFamily, fontPath=self.fontPath, fontsize=self.fontsize, state=uiconst.UI_DISABLED)
        self.sr.label = label

    def Prepare_Hilite_(self, *args):
        self.sr.hilite = uicls.Fill(parent=self, color=self._hiliteColor)

    def Setup(self, entry, size, menu, identifier):
        text = entry.caption
        self.sr.label.fontsize = size
        self.sr.label.text = text
        self.menu = menu
        menuIconSize = menu.iconSize
        icon = None
        if menuIconSize:
            icon = uicls.Icon(icon=entry.icon or 'ui_1_16_101', parent=self, pos=(0,
             0,
             menuIconSize,
             menuIconSize), align=uiconst.RELATIVE, idx=0, state=uiconst.UI_DISABLED, ignoreSize=True)
            icon.name = 'icon'
            self.sr.label.left += menuIconSize
        self.id = identifier
        if not entry.enabled:
            if icon:
                icon.SetAlpha(0.5)
            self.sr.label.SetRGB(1.0, 1.0, 1.0, 0.5)
            if isinstance(entry.value, basestring):
                self.sr.label.text += ' (' + entry.value + ')'
        self.width = self.sr.label.textwidth + self.sr.label.left + self.LABELHORIZONTALPADDING
        self.height = max(menuIconSize, self.sr.label.textheight + self.LABELVERTICALPADDING)
        if not entry.enabled:
            self.state = uiconst.UI_DISABLED
        if isinstance(entry.value, (list, tuple)):
            self.triangle.state = uiconst.UI_DISABLED
            self.submenu = entry.value

    def _OnClose(self):
        if self.submenuview is not None and not self.submenuview.destroyed:
            self.submenuview.Close()
            self.submenuview = None
        self.menu = None
        self.submenu = None
        self.expandTimer = None
        self.collapseTimer = None
        uicls.Container._OnClose(self)

    def OnMouseDown(self, *etc):
        uthread.new(self.MouseDown)

    def MouseDown(self):
        if not self.destroyed and self.submenu:
            self.Expand()

    def OnMouseUp(self, *etc):
        if not self.submenu and uicore.uilib.mouseOver in (self, self.sr.label):
            self.menu.ActivateEntry(self.id)
            uthread.new(uiutil.Flush, uicore.layer.menu)

    def OnMouseEnter(self, *args):
        uicore.Message('ContextMenuEnter')
        for each in self.parent.children:
            if each.sr.hilite:
                each.sr.hilite.Close()
                each.sr.hilite = None

        if self.sr.hilite is None:
            self.Prepare_Hilite_()
        self.expandTimer = base.AutoTimer(10, self.ExpandMenu)

    def ExpandMenu(self):
        for each in self.parent.children:
            if each != self and getattr(each, 'submenuview', None):
                each.Collapse()

        self.expandTimer = None
        if uicore.uilib.mouseOver in (self, self.sr.label) and self.submenu:
            self.Expand()

    def OnMouseExit(self, *args):
        pass

    def toggle(self):
        if self.submenuview:
            self.Collapse()
        else:
            self.Expand()

    def Collapse(self):
        self.collapseTimer = None
        if self.submenuview and self.submenuview.destroyed:
            self.submenuview = None
        elif self.submenuview:
            self.submenuview.Collapse()
            self.submenuview = None

    def Expand(self):
        if not self.submenuview:
            for each in self.parent.children:
                if each != self and getattr(each, 'submenuview', None):
                    each.Collapse()

            if self.submenu[0] == 'isDynamic':
                menu = CreateMenuView(CreateMenuFromList(apply(self.submenu[1], self.submenu[2])), self.parent)
            else:
                menu = CreateMenuView(CreateMenuFromList(self.submenu), self.parent)
            if not menu:
                return
            w = uicore.desktop.width
            h = uicore.desktop.height
            aL, aT, aW, aH = self.GetAbsolute()
            menu.top = max(0, min(h - menu.height, aT))
            if aL + aW + menu.width <= w:
                menu.left = aL + aW - 3
            else:
                aL, aT, aW, aH = self.GetAbsolute()
                menu.left = aL - menu.width + 5
            uicore.layer.menu.children.insert(0, menu)
            if not self or self.destroyed:
                uiutil.Flush(uicore.layer.menu)
                return
            self.submenuview = menu


class MenuLabel(tuple):

    def __new__(cls, text, kw = None):
        if kw is None:
            kw = {}
        return tuple.__new__(cls, (text, kw))


def CreateMenuView(menu, parent = None, minwidth = None):
    if menu is None:
        return
    m = uicls.DropDownMenu(name='menuview', align=uiconst.TOPLEFT, parent=None)
    m.Setup(menu, parent, minwidth)
    return m


def CreateMenuFromList(lst):
    while lst and lst[0] is None:
        lst = lst[1:]

    while lst and lst[-1] is None:
        lst = lst[:-1]

    if not lst:
        return
    iconSize = None
    m = Menu()
    import menu
    hasGroupMenuFunction = hasattr(menu, 'GetMenuGroup')
    ignoreMenuGrouping = prefs.GetValue('ignoreMenuGrouping', 0)
    allEntries = []
    for each in lst:
        if each is None:
            allEntries.append((None, None))
        else:
            groupID = None
            menuLabel, value = each[:2]
            if isinstance(menuLabel, uiutil.MenuLabel):
                labelPath, keywords = menuLabel
                labelPath = labelPath.strip()
                if hasGroupMenuFunction:
                    groupID = menu.GetMenuGroup(labelPath)
                caption = localization.GetByLabel(labelPath, **keywords)
            else:
                label = menuLabel
                keywords = {}
                if hasGroupMenuFunction:
                    if isinstance(label, basestring):
                        groupID = menu.GetMenuGroup(label.lower())
                caption = label
            if ignoreMenuGrouping:
                groupID = None
            if len(each) > 2:
                args = each[2]
                if args != DISABLED_ENTRY:
                    value = lambda f = value, args = args: f(*args)
                else:
                    value = None
                if len(args) == 2 and type(args[1]) == list and len(args[1]) > 1:
                    t = 0
                    for eacharg in args[1]:
                        t1 = None
                        if hasattr(eacharg, 'stacksize'):
                            t1 = eacharg.stacksize
                        if t1 is None and hasattr(eacharg, 'quantity'):
                            t1 = eacharg.quantity
                        if t1 is not None:
                            t += t1
                        else:
                            t += 1

                    caption += ' (%s)' % t
            icon = None
            if len(each) > 3:
                icon = each[3]
                if icon is not None:
                    thisIconSize = 16
                    if type(icon) == types.TupleType:
                        icon, thisIconSize = icon
                    iconSize = max(iconSize, thisIconSize)
            menuClass = None
            if len(each) > 4:
                menuClass = each[4]
            isCallableOrSubmenu = isinstance(value, types.MethodType) or isinstance(value, types.FunctionType) or isinstance(value, types.ListType) or isinstance(value, types.TupleType)
            allEntries.append((groupID, (caption,
              value,
              icon,
              isCallableOrSubmenu,
              menuClass)))

    m.iconSize = iconSize
    idNo = 0
    allEntries = SortMenuEntries(allEntries)
    lastGroupID = None
    for groupID, each in allEntries:
        if groupID is None:
            if each is None:
                m.AddSeparator()
                lastGroupID = groupID
                continue
        if groupID != lastGroupID:
            if isinstance(groupID, tuple) and isinstance(lastGroupID, tuple):
                if groupID[0] != lastGroupID[0]:
                    m.AddSeparator()
            else:
                m.AddSeparator()
        lastGroupID = groupID
        caption, value, icon, isCallableOrSubmenu, menuClass = each
        m.AddEntry(caption, value, icon, idNo, isCallableOrSubmenu, menuClass)
        idNo += 1

    return m


def SortMenuEntries(entryList, *args):
    import menu
    hasGroupMenuFunction = hasattr(menu, 'menuHierarchy')
    if not hasGroupMenuFunction:
        return entryList
    entryList.sort(cmp=CompareGroups)
    return entryList


def CompareGroups(x, y):
    import menu
    groupX = x[0]
    groupY = y[0]
    if groupX in menu.menuHierarchy:
        priorityX = menu.menuHierarchy.index(groupX)
    else:
        priorityX = -1
    if groupY in menu.menuHierarchy:
        priorityY = menu.menuHierarchy.index(groupY)
    else:
        priorityY = -1
    if priorityX < priorityY:
        return -1
    elif priorityX == priorityY:
        return 0
    else:
        return 1


def ShowMenu(object, auxObject = None):
    m = None
    menuFunc = getattr(object, 'GetMenu', None)
    if menuFunc:
        if type(menuFunc) == types.TupleType:
            func, args = menuFunc
            m = func(args)
        else:
            m = menuFunc()
    if not m or not filter(None, m):
        if auxObject and hasattr(auxObject, 'GetAuxiliaryMenuOptions'):
            m = auxObject.GetAuxiliaryMenuOptions()
        else:
            log.LogInfo('menu', 'ShowMenu: No Menu!')
            return
    elif auxObject and hasattr(auxObject, 'GetAuxiliaryMenuOptions'):
        m += auxObject.GetAuxiliaryMenuOptions()
    if getattr(object, 'showingMenu', 0):
        log.LogInfo('menu', 'ShowMenu: Already showing a menu')
        return
    object.showingMenu = 1
    try:
        d = uicore.desktop
        mv = CreateMenuView(CreateMenuFromList(m), None, getattr(object, 'minwidth', None))
        topLeft = 1
        func = getattr(object, 'GetMenuPosition', None)
        if func is not None:
            ret = func(object)
            if len(ret) == 2:
                x, y = ret
            else:
                x, y, topLeft = ret
        else:
            x, y = uicore.uilib.x + 10, uicore.uilib.y
        if topLeft:
            x, y = min(d.width - mv.width, x), min(d.height - mv.height, y)
        else:
            x, y = min(d.width - mv.width, x - mv.width), min(d.height - mv.height, y)
        mv.left, mv.top = x, y
        uicore.layer.menu.children.insert(0, mv)
    finally:
        object.showingMenu = 0

    log.LogInfo('menu', 'ShowMenu finished OK')


def KillAllMenus():
    uiutil.Flush(uicore.layer.menu)


exports = {'menu.ShowMenu': ShowMenu,
 'menu.KillAllMenus': KillAllMenus,
 'menu.CreateMenuView': CreateMenuView,
 'menu.CreateMenuFromList': CreateMenuFromList,
 'menu.DISABLED_ENTRY': DISABLED_ENTRY,
 'uiutil.MenuLabel': MenuLabel}