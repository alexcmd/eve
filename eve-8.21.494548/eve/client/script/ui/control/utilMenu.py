#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/control/utilMenu.py
import uiconst
import uicls
import uiutil
import blue
import base
import weakref
import audioConst
import uthread
FRAMECOLOR = (1, 1, 1, 0.15)
BGCOLOR = (0.0, 0.0, 0.0, 0.95)
IDLE_OPACITY = 0.8
MOUSEOVER_OPACITY = 1.0
TOGGLEACTIVE_OPACITY = 0.8
TOGGLEINACTIVE_OPACITY = 0.6
DISABLED_OPACITY = 0.2

class UtilMenu(uicls.ButtonIcon):
    __guid__ = 'uicls.UtilMenu'
    default_name = 'UtilMenu'
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_texturePath = 'res:/UI/Texture/Icons/77_32_30.png'
    default_iconSize = 16
    default_width = 20
    default_height = 20
    default_maxWidth = None
    default_menuAlign = uiconst.TOPLEFT
    _getMenuFunction = None
    _expanded = False
    _menu = None
    _label = None
    _menuButton = None

    def Close(self, *args):
        if self.destroyed:
            return
        self._getMenuFunction = None
        uicls.ButtonIcon.Close(self, *args)
        if self.IsExpanded():
            self.CloseMenu()

    def CloseMenu(self, *args):
        if self._menu:
            menu = self._menu()
            if menu:
                menu.Close()

    def OnMenuClosed(self, *args):
        if self._menuButton:
            menuButton = self._menuButton()
            if menuButton:
                menuButton.Close()

    def ApplyAttributes(self, attributes):
        uicls.ButtonIcon.ApplyAttributes(self, attributes)
        self._label = None
        self._menu = None
        self._menuButton = None
        if attributes.GetUtilMenu:
            self._getMenuFunction = attributes.GetUtilMenu
        else:
            raise RuntimeError('GetUtilMenu has to be provided in order to use UtilMenu')
        texturePath = attributes.get('texturePath', self.default_texturePath)
        closeTexturePath = attributes.get('closeTexturePath', None)
        iconSize = attributes.get('iconSize', self.default_iconSize)
        self.texturePath = texturePath
        self.iconSize = iconSize
        self.menuAlign = attributes.get('menuAlign', self.default_menuAlign)
        self.closeTexturePath = closeTexturePath or texturePath
        self.maxWidth = attributes.get('maxWidth', self.default_maxWidth)
        if attributes.label:
            self.SetLabel(attributes.label, attributes.labelAlign or uiconst.CENTERLEFT)

    def SetLabel(self, label, labelAlign):
        if labelAlign not in (uiconst.CENTERLEFT, uiconst.CENTERRIGHT):
            raise RuntimeError('SetLabel labelAlign has to be CENTERLEFT or CENTERRIGHT')
        if labelAlign == uiconst.CENTERLEFT:
            iconAlign = uiconst.CENTERRIGHT
        else:
            iconAlign = uiconst.CENTERLEFT
        if self._label is None:
            self._label = uicls.EveLabelMedium(parent=self, text=label, align=labelAlign, bold=True, left=const.defaultPadding * 2)
        else:
            self._label.text = label
        margin = self.height - self.iconSize
        self.width = self.GetFullWidth()
        if self.maxWidth:
            self.width = min(self.maxWidth, self.width)
            self._label.SetRightAlphaFade(self.maxWidth - const.defaultPadding * 6, 10)
        icon = self.AccessIcon()
        icon.align = iconAlign
        icon.left = margin
        background = self.AccessBackground()
        background.align = uiconst.CENTERLEFT
        background.width = self.width

    def GetFullWidth(self):
        margin = self.height - self.iconSize
        if self._label:
            return self._label.left + self._label.width + self.iconSize + 2 * margin
        else:
            return self.iconSize + margin

    def GetHint(self):
        if self.maxWidth and self.maxWidth < self.GetFullWidth():
            if self._label:
                return self._label.text

    def OnClick(self, *args):
        if not self.enabled:
            return
        if audioConst.BTNCLICK_DEFAULT:
            uicore.Message(audioConst.BTNCLICK_DEFAULT)
        self.ExpandMenu()

    def IsExpanded(self):
        return bool(self._menu and self._menu())

    def ExpandMenu(self, *args):
        if self.destroyed:
            return
        if self.IsExpanded():
            self.CloseMenu()
            return
        background = self.AccessBackground()
        icon = self.AccessIcon()
        l, t, w, h = background.GetAbsolute()
        buttonCopy = uicls.Container(parent=uicore.layer.utilmenu, align=uiconst.TOPLEFT, pos=(l,
         t,
         self.GetFullWidth(),
         h), state=uiconst.UI_NORMAL, idx=0)
        buttonCopy.OnMouseDown = self.CloseMenu
        if self._label is not None:
            label = uicls.EveLabelMedium(parent=buttonCopy, text=self._label.text, align=self._label.align, bold=True, left=self._label.left)
        uicls.Sprite(parent=buttonCopy, texturePath=self.closeTexturePath, state=uiconst.UI_DISABLED, align=icon.align, width=icon.width, height=icon.height, left=icon.left)
        topOrBottomLine = uicls.Line(parent=buttonCopy, color=FRAMECOLOR, align=uiconst.TOTOP)
        if self.menuAlign in (uiconst.BOTTOMLEFT, uiconst.BOTTOMRIGHT):
            topOrBottomLine.align = uiconst.TOBOTTOM
        uicls.Line(parent=buttonCopy, color=FRAMECOLOR, align=uiconst.TOLEFT)
        uicls.Line(parent=buttonCopy, color=FRAMECOLOR, align=uiconst.TORIGHT)
        uicls.Fill(bgParent=buttonCopy, color=BGCOLOR)
        menuParent = uicls.ExpandedUtilMenu(parent=uicore.layer.utilmenu, controller=self, GetUtilMenu=self._getMenuFunction, minWidth=self.GetFullWidth() + 16, idx=1, menuAlign=self.menuAlign)
        self._menu = weakref.ref(menuParent)
        self._menuButton = weakref.ref(buttonCopy)
        uicore.animations.MorphScalar(buttonCopy, 'opacity', startVal=0.5, endVal=1.0, duration=0.2)
        uthread.new(uicore.registry.SetFocus, menuParent)


class ExpandedUtilMenu(uicls.ContainerAutoSize):
    __guid__ = 'uicls.ExpandedUtilMenu'
    default_name = 'ExpandedUtilMenu'
    default_state = uiconst.UI_NORMAL
    default_opacity = 0
    default_menuAlign = uiconst.TOPLEFT
    minWidth = 0

    def ApplyAttributes(self, attributes):
        attributes.align = uiconst.TOPLEFT
        attributes.width = 128
        attributes.height = 128
        uicls.ContainerAutoSize.ApplyAttributes(self, attributes)
        if attributes.GetUtilMenu:
            self._getMenuFunction = attributes.GetUtilMenu
        else:
            raise RuntimeError('GetUtilMenu has to be provided in order to use UtilMenu')
        self.controller = attributes.controller
        self.isTopLevelWindow = True
        self.menuAlign = attributes.Get('menuAlign', self.default_menuAlign)
        self.minWidth = attributes.minWidth or 0
        uicls.Frame(bgParent=self, color=FRAMECOLOR)
        uicls.Fill(bgParent=self, color=BGCOLOR)
        uicls.Frame(bgParent=self, frameConst=('ui_105_32_26', 15, 0), color=(0, 0, 0, 0.25), padding=(-12, -5, -12, -15))
        uicore.uilib.RegisterForTriuiEvents([uiconst.UI_MOUSEDOWN], self.OnGlobalMouseDown)
        self.ReloadMenu()
        self.AnimFadeIn()
        self.UpdateMenuPosition()

    def OnGlobalMouseDown(self, *args):
        if self.destroyed:
            return False
        for layer in (uicore.layer.utilmenu, uicore.layer.modal):
            if uiutil.IsUnder(uicore.uilib.mouseOver, layer):
                return True

        self.Close()
        return False

    def AnimFadeIn(self):
        uicore.animations.FadeIn(self, duration=0.2)

    def Close(self, *args):
        if self.controller and hasattr(self.controller, 'OnMenuClosed'):
            self.controller.OnMenuClosed()
        uicls.ContainerAutoSize.Close(self, *args)

    def _OnSizeChange_NoBlock(self, *args, **kwds):
        uicls.ContainerAutoSize._OnSizeChange_NoBlock(self, *args, **kwds)
        self.OnSizeChanged()

    def OnSizeChanged(self, *args):
        self.UpdateMenuPosition()

    def _SetSizeAutomatically(self):
        width = self.minWidth
        for each in self.children:
            if hasattr(each, 'GetEntryWidth'):
                width = max(width, each.GetEntryWidth())

        self.width = width
        uicls.ContainerAutoSize._SetSizeAutomatically(self)

    def ReloadMenu(self):
        self.Flush()
        getMenuFunction = self._getMenuFunction
        if callable(getMenuFunction):
            getMenuFunction(self)
        elif isinstance(getMenuFunction, tuple):
            func = getMenuFunction[0]
            if callable(func):
                func(self, *getMenuFunction[1:])

    def UpdateMenuPosition(self, *args):
        if self.controller.destroyed:
            return
        l, t, w, h = self.controller.GetAbsolute()
        shiftAmount = 0
        if self.menuAlign in (uiconst.TOPRIGHT, uiconst.BOTTOMRIGHT):
            self.left = l - self.width + w
            shiftAmount = -w
        else:
            self.left = l
            shiftAmount = w
        if self.menuAlign in (uiconst.BOTTOMLEFT, uiconst.BOTTOMRIGHT):
            self.top = t - self.height
        else:
            self.top = t + h - 1
        shiftToSide = False
        if self.top < 0:
            self.top = 0
            shiftToSide = True
        elif self.top + self.height > uicore.desktop.height:
            self.top = uicore.desktop.height - self.height
            shiftToSide = True
        if shiftToSide:
            if self.left + self.width + shiftAmount < uicore.desktop.width:
                self.left += shiftAmount
            else:
                self.left = self.left - self.width
        if self.left < 0:
            self.left = l + w
        elif self.left + self.width > uicore.desktop.width:
            self.left = l - self.width

    def VerifyCallback(self, callback):
        if callable(callback):
            return True
        if isinstance(callback, tuple):
            func = callback[0]
            if callable(func):
                return True
        raise RuntimeError('Callback has to be callable or tuple with callable as first argument')

    def AddHeader(self, text, callback = None, hint = None, icon = None):
        if callback:
            self.VerifyCallback(callback)
        return uicls.UtilMenuHeader(parent=self, text=text, callback=callback, hint=hint, icon=icon)

    def AddIconEntry(self, icon, text, callback = None, hint = None, toggleMode = None):
        if callback:
            self.VerifyCallback(callback)
        return uicls.UtilMenuIconEntry(parent=self, icon=icon, text=text, callback=callback, hint=hint, toggleMode=toggleMode)

    def AddButton(self, text, callback = None, hint = None, toggleMode = None):
        if callback:
            self.VerifyCallback(callback)
        return uicls.UtilMenuButton(parent=self, text=text, callback=callback, hint=hint, toggleMode=toggleMode)

    def AddCheckBox(self, text, checked, callback = None, icon = None, hint = None, indentation = None):
        if callback:
            self.VerifyCallback(callback)
        return uicls.UtilMenuCheckBox(parent=self, text=text, checked=checked, icon=icon, hint=hint, callback=callback, indentation=indentation)

    def AddCheckBoxWithSubIcon(self, text, checked, subIcon, callback = None, subIconCallback = None, icon = None, subIconHint = None, hint = None):
        if callback:
            self.VerifyCallback(callback)
        uicls.UtilMenuCheckBoxWithButton(parent=self, text=text, checked=checked, icon=icon, hint=hint, callback=callback, subIcon=subIcon, subIconCallback=subIconCallback, subIconHint=subIconHint)

    def AddRadioButton(self, text, checked, callback = None, icon = None, hint = None):
        if callback:
            self.VerifyCallback(callback)
        return uicls.UtilMenuRadioBox(parent=self, text=text, checked=checked, icon=icon, hint=hint, callback=callback)

    def AddText(self, text, minTextWidth = 100):
        return uicls.UtilMenuText(parent=self, text=text, minTextWidth=minTextWidth)

    def AddSpace(self, height = 5):
        return uicls.UtilMenuSpace(parent=self, height=height)

    def AddDivider(self, padding = 0):
        return uicls.UtilMenuDivider(parent=self, padding=padding)

    def AddContainer(self, *args, **kwargs):
        return uicls.UtilMenuContainer(parent=self, *args, **kwargs)


class UtilMenuEntryBase(uicls.Container):
    __guid__ = 'uicls.UtilMenuEntryBase'
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL
    default_icon = None
    _hiliteSprite = None
    callback = None
    isToggleEntry = False

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        labelLeft = 22
        iconLeft = 3
        if attributes.indentation:
            labelLeft += attributes.indentation
            iconLeft += attributes.indentation
        self.label = uicls.EveLabelMedium(parent=self, text=attributes.text, align=uiconst.CENTERLEFT, left=labelLeft, state=uiconst.UI_DISABLED)
        icon = attributes.Get('icon', self.default_icon)
        if icon is not None:
            self.icon = uicls.Icon(parent=self, icon=icon, state=uiconst.UI_DISABLED, left=iconLeft, width=16, height=16, align=uiconst.CENTERLEFT, ignoreSize=True)
        self.ResetOpacity()
        self.UpdateEntryHeight()

    def UpdateEntryHeight(self):
        self.height = max(18, self.label.textheight + 4)

    def GetEntryWidth(self):
        return self.label.width + self.label.left + 12

    def ResetOpacity(self):
        if not self.callback:
            self.opacity = DISABLED_OPACITY
        elif self.isToggleEntry:
            if self.isChecked:
                self.opacity = TOGGLEACTIVE_OPACITY
            else:
                self.opacity = TOGGLEINACTIVE_OPACITY
        else:
            self.opacity = IDLE_OPACITY

    def OnClick(self, *args):
        callback = self.callback
        if callback:
            if callable(callback):
                callback()
            elif isinstance(callback, tuple):
                func = callback[0]
                if callable(func):
                    func(*callback[1:])
        if self.parent:
            if self.isToggleEntry:
                self.parent.ReloadMenu()
            else:
                self.parent.Close()

    def OnMouseEnter(self, *args):
        if not self.callback:
            self.opacity = DISABLED_OPACITY
        else:
            self.opacity = MOUSEOVER_OPACITY
            uicore.Message('ListEntryEnter')
            if not self._hiliteSprite:
                self._hiliteSprite = uicls.Sprite(parent=self, name='hiliteSprite', texturePath='res:/UI/Texture/classes/UtilMenu/entryHilite.png', color=(0.15, 0.15, 0.15, 1), padding=(1, 0, 1, 0), align=uiconst.TOALL, state=uiconst.UI_DISABLED)
                self._hiliteSprite.display = False
            if not self._hiliteSprite.display:
                self._hiliteSprite.display = True
                uicore.animations.SpMaskIn(self._hiliteSprite, duration=0.25)
                self.hiliteTimer = base.AutoTimer(1, self._CheckIfStillHilited)

    def OnMouseExit(self, *args):
        if not (uiutil.IsUnder(uicore.uilib.mouseOver, self) or uicore.uilib.mouseOver is self):
            self.ShowNotHilited()

    def ShowNotHilited(self):
        self.ResetOpacity()
        self.hiliteTimer = None
        if self._hiliteSprite and self._hiliteSprite.display:
            uicore.animations.SpMaskOut(self._hiliteSprite, duration=0.06, callback=self._hiliteSprite.Hide)

    def _CheckIfStillHilited(self):
        if uiutil.IsUnder(uicore.uilib.mouseOver, self) or uicore.uilib.mouseOver is self:
            return
        self.ShowNotHilited()


class UtilMenuIconEntry(UtilMenuEntryBase):
    __guid__ = 'uicls.UtilMenuIconEntry'

    def ApplyAttributes(self, attributes):
        self.callback = attributes.callback
        if self.callback and attributes.toggleMode:
            self.isToggleEntry = True
            self.isChecked = True
        uicls.UtilMenuEntryBase.ApplyAttributes(self, attributes)


class UtilMenuButton(UtilMenuIconEntry):
    __guid__ = 'uicls.UtilMenuButton'
    default_icon = 'res:/UI/Texture/classes/UtilMenu/BulletIcon.png'


class UtilMenuCheckBox(UtilMenuEntryBase):
    __guid__ = 'uicls.UtilMenuCheckBox'
    isToggleEntry = True
    isChecked = False

    def ApplyAttributes(self, attributes):
        self.callback = attributes.callback
        self.isChecked = attributes.checked
        self.isToggleEntry = True
        if attributes.icon is None:
            if attributes.checked:
                attributes.icon = 'res:/UI/Texture/classes/UtilMenu/checkBoxActive.png'
            else:
                attributes.icon = 'res:/UI/Texture/classes/UtilMenu/checkBoxInactive.png'
        uicls.UtilMenuEntryBase.ApplyAttributes(self, attributes)


class UtilMenuCheckBoxWithButton(UtilMenuCheckBox):
    __guid__ = 'uicls.UtilMenuCheckBoxWithButton'

    def ApplyAttributes(self, attributes):
        UtilMenuCheckBox.ApplyAttributes(self, attributes)
        self.subIcon = uicls.Icon(parent=self, icon=attributes.subIcon, state=uiconst.UI_DISABLED, left=3, width=16, height=16, align=uiconst.CENTERRIGHT, ignoreSize=True)
        if attributes.subIconCallback:
            self.subIcon.hint = attributes.subIconHint
            self.subIcon.state = uiconst.UI_NORMAL
            self.subIcon.OnClick = self.OnSubIconClick
            self.subIcon.OnMouseEnter = self.OnMouseEnter
            self.subIconCallback = attributes.subIconCallback

    def OnSubIconClick(self, *args):
        callback = self.subIconCallback
        if callback:
            if callable(callback):
                callback()
            elif isinstance(callback, tuple):
                func = callback[0]
                if callable(func):
                    func(*callback[1:])
        if self.parent:
            if self.isToggleEntry:
                self.parent.ReloadMenu()
            else:
                self.parent.Close()

    def GetEntryWidth(self):
        width = UtilMenuCheckBox.GetEntryWidth(self)
        return (width + 20) / 16 * 16 + 16


class UtilMenuRadioBox(UtilMenuEntryBase):
    __guid__ = 'uicls.UtilMenuRadioBox'

    def ApplyAttributes(self, attributes):
        self.callback = attributes.callback
        self.isChecked = attributes.checked
        self.isToggleEntry = True
        if attributes.icon is None:
            if attributes.checked:
                attributes.icon = 'res:/UI/Texture/classes/UtilMenu/radioButtonActive.png'
            else:
                attributes.icon = 'res:/UI/Texture/classes/UtilMenu/radioButtonInactive.png'
        uicls.UtilMenuEntryBase.ApplyAttributes(self, attributes)


class UtilMenuHeader(UtilMenuEntryBase):
    __guid__ = 'uicls.UtilMenuHeader'
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_DISABLED

    def ApplyAttributes(self, attributes):
        self.callback = attributes.callback
        if self.callback:
            attributes.state = uiconst.UI_NORMAL
            self.isToggleEntry = True
        uicls.UtilMenuEntryBase.ApplyAttributes(self, attributes)
        iconLeft = 0
        if attributes.icon:
            self.label.left = 22
        else:
            self.label.left = 6
        self.label.bold = True
        self.label.letterspace = 1
        uicls.Sprite(parent=self, align=uiconst.TOALL, texturePath='res:/UI/Texture/classes/UtilMenu/headerGradient.png', color=(1, 1, 1, 0.1), padLeft=1, padRight=1, state=uiconst.UI_DISABLED)
        self.UpdateEntryHeight()

    def ResetOpacity(self):
        pass

    def GetEntryWidth(self):
        return self.label.width + self.label.left * 2


class UtilMenuText(uicls.Container):
    __guid__ = 'uicls.UtilMenuText'
    default_align = uiconst.TOTOP
    default_height = 22
    default_minTextWidth = 100

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.minTextWidth = attributes.get('minTextWidth', self.default_minTextWidth)
        self.text = uicls.EveLabelMedium(parent=self, text=attributes.text, align=uiconst.TOTOP, padding=6, color=(1, 1, 1, 0.8), state=uiconst.UI_DISABLED)
        self.text._OnSizeChange_NoBlock = self.OnTextSizeChange
        self.height = self.text.textheight + 12

    def GetEntryWidth(self):
        return self.minTextWidth + 12

    def OnTextSizeChange(self, newWidth, newHeight):
        uicls.EveLabelMedium._OnSizeChange_NoBlock(self.text, newWidth, newHeight)
        self.height = self.text.textheight + 12


class UtilMenuSpace(uicls.Container):
    __guid__ = 'uicls.UtilMenuSpace'
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)

    def GetEntryWidth(self):
        return 0


class UtilMenuDivider(uicls.Container):
    __guid__ = 'uicls.UtilMenuDivider'
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        padding = attributes.padding or 0
        attributes.height = 1 + padding * 2
        uicls.Container.ApplyAttributes(self, attributes)
        uicls.Line(parent=self, align=uiconst.TOTOP, padTop=padding, padLeft=1, padRight=1, color=FRAMECOLOR)

    def GetEntryWidth(self):
        return 0


class UtilMenuContainer(UtilMenuEntryBase, uicls.ContainerAutoSize):
    __guid__ = 'uicls.UtilMenuContainer'

    def ApplyAttributes(self, attributes):
        uicls.ContainerAutoSize.ApplyAttributes(self, attributes)
        self.ResetOpacity()
        self.UpdateEntryHeight()

    def GetEntryWidth(self):
        return 100

    def UpdateEntryHeight(self):
        pass

    def ResetOpacity(self):
        pass

    def OnClick(self, *args):
        pass

    def OnMouseEnter(self, *args):
        self.opacity = TOGGLEACTIVE_OPACITY