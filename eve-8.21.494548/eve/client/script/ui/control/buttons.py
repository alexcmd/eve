#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/control/buttons.py
import localization
import uix
import uiutil
import base
import uthread
import uicls
import uiconst
import blue
import trinity
import audioConst
FRAME_COLOR = (1.0,
 1.0,
 1.0,
 0.25)

class PushButtonGroup(uicls.Container):
    __guid__ = 'uicls.PushButtonGroup'
    default_align = uiconst.RELATIVE
    default_idx = 0
    default_unisize = False
    default_toggleEnabled = True
    default_multiSelect = False

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.unisize = attributes.get('unisize', self.default_unisize)
        self.toggleEnabled = attributes.get('toggleEnabled', self.default_toggleEnabled)
        self.multiSelect = attributes.get('multiSelect', self.default_multiSelect)
        mainParent = uicls.Container(name='mainParent', parent=self, idx=0, padding=(8, 3, 8, 3), align=uiconst.TOALL)
        self.sr.buttonParent = mainParent
        self.sr.selected = {}
        self.selectedRGBA = (0.0, 0.0, 0.0, 0.5)
        self.sr.hilite = {}
        self.hiliteRGBA = (1.0, 1.0, 1.0, 0.125)
        self.dividerColor = (1.0, 1.0, 1.0, 0.1)
        self.Prepare_Appearance_()

    def Prepare_Appearance_(self):
        uicls.Line(parent=self.sr.buttonParent, align=uiconst.TOLEFT, color=(0.0, 0.0, 0.0, 0.1))
        uicls.Line(parent=self.sr.buttonParent, align=uiconst.TORIGHT, color=(0.0, 0.0, 0.0, 0.1))
        shape = uicls.Container(parent=self, name='shape', state=uiconst.UI_DISABLED, align=uiconst.TOALL, padding=(3, 3, 3, 3))
        uicls.Frame(parent=shape, name='dot', texturePath='res:/UI/Texture/Shared/windowButtonDOT.png', cornerSize=2, spriteEffect=trinity.TR2_SFX_DOT, blendMode=trinity.TR2_SBM_ADD)
        uicls.Sprite(parent=shape, name='gradientFill', texturePath='res:/UI/Texture/Shared/windowButtonGradient.png', align=uiconst.TOALL, filter=False, color=(1, 1, 1, 0.8))
        uicls.Fill(name='solidFill', parent=shape, color=(0, 0, 0, 0.95))
        uicls.Frame(parent=shape, padding=(-4, -4, -4, -4), name='shadow', texturePath='res:/UI/Texture/Shared/windowShadow.png', cornerSize=9, state=uiconst.UI_DISABLED, color=(0.0, 0.0, 0.0, 0.5))

    def Startup(self, data, selectedArgs = None):
        btns = []
        maxTextHeight = 0
        for index, (label, panel, parentClass, hint, args) in enumerate(data):
            uicls.Line(parent=self.sr.buttonParent, name='leftLine', align=uiconst.TOLEFT, color=self.dividerColor)
            self.width += 1
            par = uicls.Container(name='buttonPar%d' % index, parent=self.sr.buttonParent, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL)
            par.OnMouseEnter = (self.BtnMouseEnter, par)
            par.OnMouseExit = (self.BtnMouseExit, par)
            par.OnMouseDown = (self.BtnMouseDown, par)
            par.OnMouseUp = (self.BtnMouseUp, par)
            par.OnClick = (self.Select, par)
            par.sr.args = args
            par.sr.parentClass = parentClass
            par.sr.panel = panel
            par.sr.panelName = label
            par.selected = 0
            par.localizedLabel = label
            if hint:
                par.hint = hint
            t = uicls.EveLabelSmall(text=label, parent=par, left=1, state=uiconst.UI_DISABLED, align=uiconst.CENTER)
            par.sr.label = t
            par.width = t.textwidth + 12
            maxTextHeight = max(maxTextHeight, t.textheight + 9)
            par.minHeight = min(32, t.textheight + 9)
            self.sr.selected[par] = uicls.Fill(parent=par, color=self.selectedRGBA, state=uiconst.UI_HIDDEN)
            self.sr.hilite[par] = uicls.Fill(parent=par, color=self.hiliteRGBA, state=uiconst.UI_HIDDEN)
            self.sr.selected[par].SetOrder(-1)
            self.sr.hilite[par].SetOrder(-1)
            self.width += par.width
            btns.append(par)

        uicls.Line(parent=self.sr.buttonParent, name='endLine', align=uiconst.TOLEFT, color=self.dividerColor)
        self.width += 1
        self.buttons = btns
        self.height = min(32, maxTextHeight)
        self.width += 18
        for each in btns:
            each.height = self.height - 6

        self._AdjustButtons()
        if selectedArgs is None:
            self.DeselectAll()
        else:
            for name in selectedArgs:
                self.SelectPanelByArgs(name)

    def DeselectAll(self):
        for each in self.sr.buttonParent.children:
            if each.sr.label:
                self.Deselect(each)

        self.OnNoneSelected()

    def SelectPanelByName(self, panelName):
        for each in self.sr.buttonParent.children:
            if each.sr.panelName == panelName:
                self.Select(each)

    def SelectPanelByArgs(self, args):
        for each in self.sr.buttonParent.children:
            if each.sr.args == args:
                self.Select(each)

    def BtnMouseEnter(self, btn, *args):
        if not btn.selected:
            self.sr.hilite[btn].state = uiconst.UI_DISABLED

    def BtnMouseExit(self, btn, *args):
        self.sr.hilite[btn].state = uiconst.UI_HIDDEN

    def BtnMouseDown(self, btn, *args):
        btn.sr.label.top = 1

    def BtnMouseUp(self, btn, *args):
        if not btn.selected:
            btn.sr.label.top = 0

    def GetSelected(self):
        for each in self.sr.buttonParent.children:
            if getattr(each, 'selected', False):
                return each.sr.args

    def Select(self, btn, *args):
        if btn.sr.isDisabled:
            return
        if self.toggleEnabled and btn.selected:
            self.Deselect(btn)
            self.OnNoneSelected()
            return
        btn.selected = 1
        btn.sr.label.top = 0
        for each in btn.parent.children:
            if each.sr.label and each != btn and not self.multiSelect:
                self.Deselect(each)

        self.sr.hilite[btn].Hide()
        self.sr.selected[btn].state = uiconst.UI_DISABLED
        if btn.sr.panel:
            btn.sr.panel.state = uiconst.UI_PICKCHILDREN
        pc = btn.sr.parentClass
        if hasattr(pc, 'OnButtonSelected'):
            pc.OnButtonSelected(btn.sr.args)

    def Deselect(self, btn, *args):
        if btn.selected:
            self.sr.selected[btn].Hide()
        btn.selected = 0
        if btn.sr.panel:
            btn.sr.panel.state = uiconst.UI_HIDDEN
        if hasattr(btn.sr.parentClass, 'OnButtonDeselected'):
            btn.sr.parentClass.OnButtonDeselected(btn.sr.args)

    def OnNoneSelected(self, *args):
        for item in self.sr.buttonParent.children:
            if item.name.endswith('Par'):
                self.Select(item)
                return

    def _AdjustButtons(self):
        if self.unisize:
            pw, ph = self.sr.buttonParent.GetAbsoluteSize()
            if pw <= 0:
                return
            totalButtons = len(self.buttons)
            buttonWidth = (pw - (len(self.buttons) + 1)) / totalButtons
            totalWidth = 1
            for button in self.buttons:
                if button is self.buttons[-1]:
                    button.width = pw - totalWidth - 1
                else:
                    button.width = buttonWidth
                button.width = max(button.minHeight, button.width)
                totalWidth += button.width + 1

    def _OnResize(self):
        if self.sr.buttonParent:
            uthread.new(self._AdjustButtons)

    def EnableButton(self, panelName):
        for button in self.sr.buttonParent.children:
            if button.sr.panelName == panelName:
                button.sr.label.color.a = 1
                button.sr.isDisabled = False

    def DisableButton(self, panelName):
        for button in self.sr.buttonParent.children:
            if button.sr.panelName == panelName:
                button.sr.label.color.a = 0.4
                button.sr.isDisabled = True

    def ButtonSelect(self, button, *args):
        if hasattr(button, 'sr'):
            if button.sr.isDisabled:
                eve.Message('SelectLocation', {'location': button.sr.panelName})
            elif button.selected == 0:
                self.Select(button)


class FlatButtonGroup(PushButtonGroup):
    __guid__ = 'uicls.FlatButtonGroup'
    default_unisize = True

    def ApplyAttributes(self, attributes):
        PushButtonGroup.ApplyAttributes(self, attributes)
        self.sr.buttonParent.padLeft = self.sr.buttonParent.padRight = 0
        self.sr.buttonParent.clipChildren = True
        self.selectedRGBA = (1.0, 1.0, 1.0, 0.2)
        self.hiliteRGBA = (1.0, 1.0, 1.0, 0.125)
        self.dividerColor = FRAME_COLOR

    def Prepare_Appearance_(self, *args):
        uicls.Line(parent=self.sr.buttonParent, color=FRAME_COLOR, align=uiconst.TOTOP)
        uicls.Line(parent=self.sr.buttonParent, color=FRAME_COLOR, align=uiconst.TOBOTTOM)

    def BtnMouseEnter(self, btn, *args):
        PushButtonGroup.BtnMouseEnter(self, btn, *args)


class Button(uicls.ButtonCore):
    __guid__ = 'uicls.Button'
    default_alwaysLite = False
    default_iconSize = 32
    default_icon = None
    default_color = (1.0, 1.0, 1.0, 0.75)

    def ApplyAttributes(self, attributes):
        self.alwaysLite = attributes.get('alwaysLite', self.default_alwaysLite)
        self.color = attributes.get('color', self.default_color)
        self.iconPath = attributes.get('icon', self.default_icon)
        self.iconSize = attributes.get('iconSize', self.default_iconSize)
        args = attributes.get('args', None)
        uicls.ButtonCore.ApplyAttributes(self, attributes)
        if args == 'self':
            self.args = self

    def Prepare_(self):
        self.sr.label = uicls.EveLabelSmall(text='', parent=self, idx=0, align=uiconst.CENTER, state=uiconst.UI_DISABLED, color=self.color)
        if self.iconPath is not None:
            if self.iconSize:
                width = self.iconSize
                height = self.iconSize
            else:
                width = height = min(self.width, self.height)
            self.icon = uicls.Icon(parent=self, state=uiconst.UI_DISABLED, align=uiconst.CENTER, pos=(0,
             0,
             width,
             height), icon=self.iconPath, ignoreSize=True, color=self.color)
            self.sr.label.state = uiconst.UI_HIDDEN
            self.width = width + 4
            self.height = height + 4
        self.sr.activeframe = uicls.Frame(parent=self, name='activeline', state=uiconst.UI_HIDDEN, color=(1.0,
         1.0,
         1.0,
         uiconst.ACTIVE_FRAME_ALPHA))
        self.sr.hilite = uicls.Frame(parent=self, name='hiliteLite', state=uiconst.UI_HIDDEN, color=(1.0, 1.0, 1.0, 0.5))
        self.innerline = uicls.Frame(parent=self, padding=(2, 2, 2, 2), name='innerline', state=uiconst.UI_HIDDEN, color=(1.0, 1.0, 1.0, 0.5))
        self.shape = uicls.Container(parent=self, name='shape', state=uiconst.UI_DISABLED, align=uiconst.TOALL)
        uicls.Frame(parent=self.shape, name='dot', texturePath='res:/UI/Texture/Shared/windowButtonDOT.png', cornerSize=6, spriteEffect=trinity.TR2_SFX_DOT)
        uicls.WindowBaseColor(parent=self.shape, frameConst=('res:/UI/Texture/Shared/buttonShapeAndShadow.png', 9, -5))
        self.LiteMode(self.alwaysLite)
        isDefault = getattr(self, 'btn_default', 0)
        if isDefault and self.sr.activeframe:
            self.sr.defaultActiveFrame = uicls.Frame(parent=self, idx=0, name='isDefaultMarker', state=uiconst.UI_DISABLED, color=(1.0,
             1.0,
             1.0,
             uiconst.ACTIVE_FRAME_ALPHA))
        wnd = uiutil.GetWindowAbove(self)
        if wnd:
            self.LiteMode(wnd.IsPinned())

    def Update_Size_(self):
        if self.iconPath is None:
            self.width = min(256, self.fixedwidth or max(40, self.sr.label.width + 20))
            self.height = max(18, min(32, self.sr.label.textheight + 4))

    def SetLabel_(self, label):
        if not self or self.destroyed:
            return
        text = self.text = label
        self.sr.label.text = text
        self.Update_Size_()

    def OnSetFocus(self, *args):
        if self.disabled:
            return
        if self and not self.destroyed and self.parent and self.parent.name == 'inlines':
            if self.parent.parent and self.parent.parent.sr.node:
                browser = uiutil.GetBrowser(self)
                if browser:
                    uthread.new(browser.ShowObject, self)
        if self and not self.destroyed and self.sr and self.sr.activeframe:
            self.sr.activeframe.state = uiconst.UI_DISABLED
        btns = self.GetDefaultBtnsInSameWnd()
        if btns:
            self.SetWndDefaultFrameState(btns, 0)

    def LiteMode(self, on = True):
        if on:
            self.shape.state = uiconst.UI_HIDDEN
            self.innerline.state = uiconst.UI_DISABLED
        elif self.alwaysLite == False:
            self.shape.state = uiconst.UI_DISABLED
            self.innerline.state = uiconst.UI_HIDDEN


class BrowseButton(uicls.Container):
    __guid__ = 'uicls.BrowseButton'
    default_width = 60
    default_align = uiconst.TOPLEFT
    default_height = 16
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        prev = attributes.prev
        icon = attributes.icon
        if prev:
            icon = '38_227'
            align = uiconst.CENTERLEFT
            text = localization.GetByLabel('UI/Common/Prev')
            self.backforth = -1
        else:
            icon = '38_228'
            align = uiconst.CENTERRIGHT
            text = localization.GetByLabel('UI/Common/Next')
            self.backforth = 1
        self.func = attributes.func
        self.args = attributes.args or ()
        self.alphaOver = 1.0
        self.alphaNormal = 0.8
        self.alphaDisabled = 0.4
        if self.state == uiconst.UI_DISABLED:
            self.disabled = True
        else:
            self.disabled = False
        iconCont = uicls.Container(parent=self, align=align, width=16, height=16)
        textCont = uicls.Container(parent=self, align=uiconst.TOALL)
        self.sr.icon = uicls.Icon(icon=icon, parent=iconCont, pos=(0, 0, 16, 16), align=align, idx=0, state=uiconst.UI_DISABLED)
        self.sr.label = uicls.EveLabelMedium(text=text, parent=textCont, align=align, state=uiconst.UI_DISABLED, left=16)
        self.SetOpacity(self.alphaNormal)

    def OnClick(self, *args):
        if self.destroyed or self.disabled:
            return
        if self.func:
            self.func(self, *self.args)

    def OnMouseEnter(self, *args):
        if self.destroyed or self.disabled:
            return
        if getattr(self, 'alphaOver', None):
            self.SetOpacity(self.alphaOver)

    def OnMouseExit(self, *args):
        if self.destroyed or self.disabled:
            return
        if getattr(self, 'alphaNormal', None):
            self.SetOpacity(self.alphaNormal)

    def LoadIcon(self, *args, **kw):
        self.sr.icon.LoadIcon(*args, **kw)

    def Disable(self):
        self.opacity = self.alphaDisabled
        self.disabled = True

    def Enable(self):
        self.opacity = self.alphaNormal
        self.disabled = False


class ButtonIcon(uicls.Container):
    __guid__ = 'uicls.ButtonIcon'
    default_func = None
    default_args = None
    default_width = 32
    default_height = 32
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_texturePath = None
    default_isActive = True
    default_iconSize = 16
    default_noBgSize = 25
    OPACITY_IDLE = 0.75
    OPACITY_INACTIVE = 0.4
    OPACITY_MOUSEHOVER = 1.0
    OPACITY_MOUSECLICK = 1.2

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.func = attributes.get('func', self.default_func)
        self.args = attributes.get('args', self.default_args)
        self.isActive = attributes.get('isActive', True)
        self.texturePath = attributes.get('texturePath', self.default_texturePath)
        self.iconSize = attributes.get('iconSize', self.default_iconSize)
        if self.iconSize < self.default_noBgSize:
            self.isHoverBGUsed = True
        else:
            self.isHoverBGUsed = False
        self.enabled = True
        self.icon = self.ConstructIcon()
        width, height = self.GetAbsoluteSize()
        size = min(width, height)
        bgCont = uicls.Container(name='bgCont', parent=self, align=uiconst.CENTER, state=uiconst.UI_DISABLED, width=size, height=size)
        self.mouseEnterBG = uicls.Sprite(name='mouseEnterBG', bgParent=bgCont, texturePath='res:/UI/Texture/classes/ButtonIcon/mouseEnter.png', opacity=0.0)
        self.mouseDownBG = uicls.Sprite(name='mouseEnterBG', bgParent=bgCont, texturePath='res:/UI/Texture/classes/ButtonIcon/mouseDown.png', opacity=0.0)
        self.bgContainer = bgCont
        self.SetActive(self.isActive, animate=False)

    def ConstructIcon(self):
        return uicls.Sprite(name='icon', parent=self, align=uiconst.CENTER, width=self.iconSize, height=self.iconSize, texturePath=self.texturePath, state=uiconst.UI_DISABLED)

    def AccessIcon(self):
        return self.icon

    def AccessBackground(self):
        return self.bgContainer

    def Disable(self):
        self.opacity = 0.5
        self.enabled = 0
        self.mouseEnterBG.StopAnimations()
        self.mouseEnterBG.opacity = 0.0

    def Enable(self):
        self.opacity = 1.0
        self.enabled = 1

    def SetActive(self, isActive, animate = True):
        self.isActive = isActive
        if animate:
            if isActive:
                uicore.animations.FadeTo(self.icon, self.icon.opacity, self.OPACITY_IDLE, duration=0.2)
            else:
                uicore.animations.FadeTo(self.icon, self.icon.opacity, self.OPACITY_INACTIVE, duration=0.2)
        else:
            self.icon.opacity = self.OPACITY_IDLE if isActive else self.OPACITY_INACTIVE

    def Blink(self):
        uicore.animations.FadeTo(self.mouseEnterBG, 0.0, 0.9, duration=0.25, curveType=uiconst.ANIM_WAVE)

    def OnClick(self, *args):
        if not self.func or not self.enabled:
            return
        if audioConst.BTNCLICK_DEFAULT:
            uicore.Message(audioConst.BTNCLICK_DEFAULT)
        if type(self.args) == tuple:
            self.func(*self.args)
        elif self.args:
            self.func(self.args)
        else:
            self.func()

    def OnMouseEnter(self, *args):
        if not self.enabled:
            return
        uicore.animations.FadeTo(self.icon, self.icon.opacity, self.OPACITY_MOUSEHOVER, duration=0.2)
        if self.isHoverBGUsed:
            uicore.animations.FadeIn(self.mouseEnterBG, duration=0.2)

    def OnMouseExit(self, *args):
        self.SetActive(self.isActive)
        if self.isHoverBGUsed:
            uicore.animations.FadeOut(self.mouseEnterBG, duration=0.2)

    def OnMouseDown(self, *args):
        if not self.enabled:
            return
        self.SetActive(self.isActive)
        if self.isHoverBGUsed:
            uicore.animations.FadeIn(self.mouseDownBG, duration=0.1)
            uicore.animations.FadeOut(self.mouseEnterBG, duration=0.1)
        else:
            uicore.animations.FadeTo(self.icon, self.icon.opacity, self.OPACITY_MOUSECLICK, duration=0.1)

    def OnMouseUp(self, *args):
        if self.isHoverBGUsed:
            uicore.animations.FadeOut(self.mouseDownBG, duration=0.1)
        else:
            uicore.animations.FadeTo(self.icon, self.icon.opacity, self.OPACITY_IDLE, duration=0.1)
        if not self.enabled:
            return
        if uicore.uilib.mouseOver == self:
            if self.isHoverBGUsed:
                uicore.animations.FadeIn(self.mouseEnterBG, duration=0.1)
            else:
                uicore.animations.FadeTo(self.icon, self.icon.opacity, self.OPACITY_MOUSEHOVER, duration=0.1)

    def OnEndDrag(self, *args):
        if uicore.uilib.mouseOver != self:
            uicore.animations.FadeOut(self.mouseEnterBG, duration=0.2)
        elif self.isHoverBGUsed:
            uicore.animations.FadeIn(self.mouseEnterBG, duration=0.1)
        uicore.animations.FadeOut(self.mouseDownBG, duration=0.1)


class IconButton(uicls.Container):
    __guid__ = 'uicls.IconButton'
    default_alphaNormal = 0.6
    default_alphaOver = 1.0

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        icon = attributes.icon
        iconAlign = attributes.iconAlign
        if iconAlign is None:
            iconAlign = uiconst.TOALL
        self.func = attributes.func
        self.args = attributes.args or ()
        ignoreSize = attributes.ignoreSize or False
        iconPos = attributes.iconPos or (1, 2, 24, 24)
        self.alphaOver = attributes.alphaOver or self.default_alphaOver
        self.alphaNormal = attributes.alphaOver or self.default_alphaNormal
        self.state = attributes.state or uiconst.UI_NORMAL
        self.sr.icon = uicls.Icon(icon=icon, parent=self, pos=iconPos, align=iconAlign, idx=0, state=uiconst.UI_DISABLED, ignoreSize=ignoreSize)
        self.SetOpacity(self.default_alphaNormal)
        self.keepHighlight = False

    def OnClick(self, *args):
        if self.func:
            self.func(*self.args)

    def KeepHighlight(self, *args):
        self.keepHighlight = True
        self.SetOpacity(self.alphaOver)

    def RemoveHighlight(self, *args):
        self.keepHighlight = False
        self.SetOpacity(self.default_alphaNormal)

    def OnMouseEnter(self, *args):
        if not self.destroyed and getattr(self, 'alphaOver', None):
            self.SetOpacity(self.alphaOver)

    def OnMouseExit(self, *args):
        if not self.destroyed and getattr(self, 'default_alphaNormal', None) and not self.keepHighlight:
            self.SetOpacity(self.default_alphaNormal)

    def LoadIcon(self, *args, **kw):
        self.sr.icon.LoadIcon(*args, **kw)


class BaseButton(uicls.Container):
    __guid__ = 'xtriui.BaseButton'

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.sr.preleft = None
        self.sr.pretop = None
        self.sr.selection = None
        self.sr.selected = 0
        self.sr.enterAlt = 0
        self.sr.hilite = None
        self.Click = None
        self.DblClick = None
        self.MouseEnter = None
        self.MouseExit = None
        self.enabled = 1
        self.blinking = 0
        self.clicks = 0

    def Select(self):
        if self is None or self.destroyed:
            return
        if self.sr.selection is None:
            self.sr.selection = uicls.Sprite(parent=self, padding=(-int(self.width * 0.5),
             -int(self.width * 0.5),
             -int(self.width * 0.5),
             -int(self.width * 0.5)), name='selection', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/selectionglow.dds', color=(0.75, 0.75, 0.75, 1.0), align=uiconst.TOALL)
        self.sr.selected = 1

    def Deselect(self):
        if self and self.sr and self.sr.selection is not None:
            self.sr.selection.state = uiconst.UI_HIDDEN
            self.sr.selected = 0

    def Disable(self):
        self.opacity = 0.5
        self.enabled = 0

    def Enable(self):
        self.opacity = 1.0
        self.enabled = 1

    def OnDblClick(self, *etc):
        if not self.enabled:
            return
        if self.DblClick:
            self.clicks += 1
        elif self.Click:
            self.Click(self)

    def OnClick(self, *etc):
        if not self.enabled:
            return
        self.clicks += 1
        if self.DblClick:
            self.sr.clickTimer = base.AutoTimer(250, self.ClickTimer)
        elif self.Click:
            self.Click(self)

    def ClickTimer(self, *args):
        if self.clicks == 1:
            if self.Click:
                self.Click(self)
        elif self.clicks >= 2:
            if self.DblClick:
                self.DblClick(self)
        if not self.destroyed:
            self.clicks = 0
            self.sr.clickTimer = None

    def OnMouseEnter(self, *etc):
        if not self.enabled:
            return
        eve.Message('CCCellEnter')
        if getattr(self, 'over', None):
            if not getattr(self, 'active', 0):
                self.rectTop = self.over
        else:
            if not self.sr.pretop:
                self.sr.pretop = self.top
                self.sr.preRectTop = self.rectTop
            self.rectTop += self.rectHeight
            self.top -= self.sr.enterAlt
        if self.MouseEnter:
            self.MouseEnter(self)

    def OnMouseExit(self, *etc):
        if getattr(self, 'idle', None):
            if not getattr(self, 'active', 0):
                self.rectTop = self.idle
        elif self.sr.pretop is not None:
            self.top = self.sr.pretop
            self.rectTop = self.sr.preRectTop
        if self.MouseExit:
            self.MouseExit(self)

    def OnMouseDown(self, *args):
        if not self.enabled:
            return
        self.top += self.sr.enterAlt

    def OnMouseUp(self, *args):
        if not self.enabled:
            return
        self.top -= self.sr.enterAlt


class BigButton(BaseButton):
    __guid__ = 'xtriui.BigButton'
    default_align = uiconst.RELATIVE
    default_width = 64
    default_height = 64
    default_name = 'bigButton'
    default_state = uiconst.UI_NORMAL

    def Startup(self, width, height, iconMargin = 0):
        uicls.Frame(parent=self, name='dot', texturePath='res:/UI/Texture/Shared/windowButtonDOT.png', cornerSize=2, state=uiconst.UI_DISABLED, spriteEffect=trinity.TR2_SFX_DOT, blendMode=trinity.TR2_SBM_ADD)
        icon = uicls.Icon(parent=self, pos=(0, 0, 0, 0), padding=(iconMargin,
         iconMargin,
         iconMargin,
         iconMargin), name='icon', texturePath='res:/UI/Texture/none.dds', state=uiconst.UI_DISABLED, align=uiconst.TOALL, filter=True)
        uicls.Fill(parent=self, name='fill', color=(1.0, 1.0, 1.0, 0.05), state=uiconst.UI_DISABLED)
        self.sr.dot = uicls.Frame(parent=self, name='baseFrame', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Shared/buttonDOT.png', color=(1.0, 1.0, 1.0, 1.0), cornerSize=8, spriteEffect=trinity.TR2_SFX_DOT, blendMode=trinity.TR2_SBM_ADD)
        hilite = uicls.Frame(parent=self, name='hiliteFrame', state=uiconst.UI_HIDDEN, color=(0.18, 0.2, 0.22, 1.0), blendMode=trinity.TR2_SBM_ADD, frameConst=uiconst.FRAME_FILLED_BLUR3, padding=(2, 2, 2, 2))
        if width > 128:
            hilite.padding = 1
        activeHilite = uicls.Fill(parent=self, name='activeHiliteFrame', state=uiconst.UI_HIDDEN, color=(0.28, 0.3, 0.35, 1.0), blendMode=trinity.TR2_SBM_ADD)
        self.sr.shadow = uicls.Frame(parent=self, offset=-9, cornerSize=13, name='shadow', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/Shared/bigButtonShadow.png')
        self.setfocus = 0
        self.killfocus = 0
        self.blinking = 0
        self.width = width
        self.height = height
        self.sr.smallcaption = None
        self.sr.caption = None
        self.sr.hilite = hilite
        self.sr.icon = icon
        self.sr.activeHilite = activeHilite
        self.resetTop = None
        self.AdjustSizeAndPosition(width, height)

    def AdjustSizeAndPosition(self, width, height):
        self.sr.enterAlt = min(2, max(6, self.height / 16))

    def SetIconByIconID(self, iconID):
        if iconID is not None:
            self.sr.icon.LoadIcon(iconID)

    def SetInCaption(self, capstr):
        if self.sr.caption:
            self.sr.caption.Close()
        if '&' in capstr and ';' in capstr:
            capstr = self.ParseHTML(capstr)
        caption = uicls.EveLabelLargeUpper(text=capstr, parent=self, idx=0, align=uiconst.CENTER)
        caption.state = uiconst.UI_DISABLED
        self.sr.caption = caption

    def SetCaption(self, capstr):
        self.SetSmallCaption(capstr)

    def SetSmallCaption(self, capstr, inside = 0, maxWidth = None):
        if not self.sr.smallcaption:
            self.sr.smallcaption = uicls.EveLabelSmall(text='', parent=self, state=uiconst.UI_DISABLED, idx=0, width=self.width)
        self.sr.smallcaption.busy = 1
        if inside:
            self.sr.smallcaption.SetAlign(uiconst.CENTER)
        else:
            self.sr.smallcaption.SetAlign(uiconst.CENTERTOP)
            self.sr.smallcaption.top = self.height + 2
        self.sr.smallcaption.width = maxWidth or self.width
        self.sr.smallcaption.busy = 0
        self.sr.smallcaption.text = '<center>' + capstr

    def ParseHTML(self, text):
        for k in translatetbl:
            text = text.replace(k, translatetbl[k])

        return text

    def OnMouseExit(self, *etc):
        if not self.blinking:
            self.sr.hilite.state = uiconst.UI_HIDDEN
        if self.MouseExit:
            self.MouseExit(self)
        self.timer = None
        if self.resetTop is not None:
            self.top = self.resetTop
            self.resetTop = None

    def OnMouseEnter(self, *etc):
        eve.Message('CCCellEnter')
        if not self.blinking:
            self.sr.hilite.state = uiconst.UI_DISABLED
        if self.MouseEnter:
            self.MouseEnter(self)
        self.timer = base.AutoTimer(500, self.ResetHilite)
        if self.resetTop is not None:
            self.top += 1

    def ResetHilite(self, *args):
        if uicore.uilib.mouseOver is not self:
            self.timer = None
            if not self.blinking and not self.destroyed:
                self.sr.hilite.state = uiconst.UI_HIDDEN

    def OnMouseDown(self, *args):
        if not self.enabled:
            return
        self.Blink(0)
        self.sr.hilite.state = uiconst.UI_HIDDEN
        if self.resetTop is None:
            self.resetTop = self.top
            self.top = self.top + 2

    def OnMouseUp(self, *args):
        if uicore.uilib.mouseOver == self:
            self.sr.hilite.state = uiconst.UI_DISABLED
        if self.resetTop is not None:
            self.top = self.resetTop
            self.resetTop = None

    def Blink(self, on_off = 1, blinks = 3):
        if on_off:
            b = self.sr.hilite
            sm.GetService('ui').BlinkSpriteRGB(b, b.color.r, b.color.g, b.color.b, 750, blinks)
            self.sr.hilite.state = uiconst.UI_DISABLED
        else:
            self.sr.hilite.state = uiconst.UI_HIDDEN
            sm.GetService('ui').StopBlink(self.sr.hilite)
        self.blinking = on_off

    def OnSetFocus(self, *args):
        if self.setfocus:
            self.sr.activeHilite.state = uiconst.UI_DISABLED

    def OnKillFocus(self, *args):
        if self.killfocus:
            self.sr.activeHilite.state = uiconst.UI_HIDDEN


class ExpanderButton(uicls.Sprite):
    __guid__ = 'uicls.ExpanderButton'
    default_name = 'expanderButton'
    default_texturePath = 'res:/UI/Texture/Shared/expanderDown.png'
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOPLEFT
    default_top = 2
    default_width = 11
    default_height = 11

    def ApplyAttributes(self, attributes):
        uicls.Sprite.ApplyAttributes(self, attributes)
        self.expandFunc = attributes.expandFunc
        self.collapseFunc = attributes.collapseFunc
        self.expanded = attributes.expanded
        self._UpdateIcon()

    def OnClick(self, *args):
        self.expanded = not self.expanded
        self._OnExpandedStateChanged()

    def _OnExpandedStateChanged(self, applyCallback = True):
        self._UpdateIcon()
        if not applyCallback:
            return
        if self.expanded:
            if self.collapseFunc is not None:
                self.collapseFunc()
        elif self.expandFunc is not None:
            self.expandFunc()

    def SetButtonState(self, expanded, applyCallback = True):
        self.expanded = not expanded
        self._OnExpandedStateChanged(applyCallback)

    def _UpdateIcon(self):
        if self.expanded:
            self.texturePath = 'res:/UI/Texture/Shared/expanderDown.png'
        else:
            self.texturePath = 'res:/UI/Texture/Shared/expanderUp.png'


translatetbl = {'&aring;': '\xe5',
 '&gt;': '>',
 '&yen;': '\xa5',
 '&ograve;': '\xd2',
 '&bull;': '\x95',
 '&trade;': '\x99',
 '&Ntilde;': '\xd1',
 '&Yacute;': '\xdd',
 '&Atilde;': '\xc3',
 '&aelig;': '\xc6',
 '&oelig;': '\x9c',
 '&auml;': '\xc4',
 '&Uuml;': '\xdc',
 '&Yuml;': '\x9f',
 '&lt;': '<',
 '&Icirc;': '\xce',
 '&shy;': '\xad',
 '&Oacute;': '\xd3',
 '&yacute;': '\xfd',
 '&acute;': '\xb4',
 '&atilde;': '\xc3',
 '&cedil;': '\xb8',
 '&Ecirc;': '\xca',
 '&not;': '\xac',
 '&AElig;': '\xc6',
 '&oslash;': '\xf8',
 '&iquest;': '\xbf',
 '&laquo;': '\xab',
 '&Igrave;': '\xcc',
 '&ccedil;': '\xc7',
 '&nbsp;': '\xa0',
 '&Auml;': '\xc4',
 '&brvbar;': '\xa6',
 '&Otilde;': '\xd5',
 '&szlig;': '\xdf',
 '&agrave;': '\xe0',
 '&Ocirc;': '\xd4',
 '&egrave;': '\xc8',
 '&iexcl;': '\xa1',
 '&frac12;': '\xbd',
 '&ordf;': '\xaa',
 '&ntilde;': '\xd1',
 '&ocirc;': '\xd4',
 '&Oslash;': '\xd8',
 '&THORN;': '\xde',
 '&yuml;': '\x9f',
 '&Eacute;': '\xc9',
 '&ecirc;': '\xca',
 '&times;': '\xd7',
 '&Aring;': '\xc5',
 '&tilde;': '~',
 '&mdash;': '-',
 '&Ugrave;': '\xd9',
 '&Agrave;': '\xc0',
 '&sup1;': '\xb9',
 '&eth;': '\xd0',
 '&iuml;': '\xcf',
 '&reg;': '\xae',
 '&Egrave;': '\xc8',
 '&divide;': '\xf7',
 '&Ouml;': '\xd6',
 '&igrave;': '\xcc',
 '&otilde;': '\xd5',
 '&pound;': '\xa3',
 '&frasl;': '/',
 '&ETH;': '\xd0',
 '&plusmn;': '\xb1',
 '&sup2;': '\xb2',
 '&frac34;': '\xbe',
 '&Aacute;': '\xc1',
 '&cent;': '\xa2',
 '&frac14;': '\xbc',
 '&euml;': '\xcb',
 '&iacute;': '\xcd',
 '&para;': '\xb6',
 '&ordm;': '\xba',
 '&uuml;': '\xdc',
 '&icirc;': '\xce',
 '&copy;': '\xa9',
 '&Iuml;': '\xcf',
 '&Ograve;': '\xd2',
 '&Ucirc;': '\xdb',
 '&Zeta;': 'Z',
 '&minus;': '-',
 '&deg;': '\xb0',
 '&and;': '&',
 '&curren;': '\xa4',
 '&ucirc;': '\xdb',
 '&ugrave;': '\xd9',
 '&sup3;': '\xb3',
 '&Acirc;': '\xc2',
 '&quot;': '"',
 '&Uacute;': '\xda',
 '&OElig;': '\x8c',
 '&uacute;': '\xda',
 '&acirc;': '\xc2',
 '&macr;': '\xaf',
 '&Euml;': '\xcb',
 '&Ccedil;': '\xc7',
 '&aacute;': '\xc1',
 '&micro;': '\xb5',
 '&eacute;': '\xc9',
 '&middot;': '\xb7',
 '&Iacute;': '\xcd',
 '&amp;': '&',
 '&uml;': '\xa8',
 '&thorn;': '\xde',
 '&ouml;': '\xd6',
 '&raquo;': '\xbb',
 '&sect;': '\xa7',
 '&oacute;': '\xd3'}