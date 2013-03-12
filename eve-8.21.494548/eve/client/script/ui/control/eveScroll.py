#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/control/eveScroll.py
import xtriui
import uix
import uiutil
import uiconst
import util
import _weakref
import weakref
import blue
import base
import uthread
import types
import listentry
import stackless
import lg
import html
import sys
import dbg
import trinity
import fontConst
import uicls
import uiutil
import uiconst
SCROLLMARGIN = 0
MINCOLUMNWIDTH = 24

class Scroll(uicls.ScrollCore):
    __guid__ = 'uicls.Scroll'
    headerFontSize = fontConst.EVE_SMALL_FONTSIZE
    sortGroups = False

    def ApplyAttributes(self, attributes):
        uicls.ScrollCore.ApplyAttributes(self, attributes)
        sm.GetService('window').CheckControlAppearance(self)

    def Prepare_ScrollControls_(self):
        self.sr.scrollcontrols = uicls.ScrollControls(name='__scrollcontrols', parent=self.sr.maincontainer, align=uiconst.TORIGHT, width=7, state=uiconst.UI_HIDDEN, idx=0)
        self.sr.scrollcontrols.Startup(self)

    def Prepare_Underlay_(self):
        self.sr.underlay = uicls.BumpedUnderlay(parent=self, name='background')

    def Startup(self, minZ = None):
        pass

    def HideBackground(self, alwaysHidden = 0):
        frame = None
        if uiutil.GetAttrs(self, 'sr', 'underlay'):
            self.sr.underlay.state = uiconst.UI_HIDDEN
            frame = self.sr.underlay
        if frame and getattr(frame, 'parent'):
            underlayFrame = frame.parent.FindChild('underlayFrame')
            underlayFill = frame.parent.FindChild('underlayFill')
            if underlayFrame:
                underlayFrame.state = uiconst.UI_HIDDEN
            if underlayFill:
                underlayFill.state = uiconst.UI_HIDDEN
        if alwaysHidden:
            self.SetNoBackgroundFlag(alwaysHidden)

    def OnMouseWheel(self, *etc):
        if getattr(self, 'wheeling', 0):
            return 1
        if len(uicore.layer.menu.children):
            focus = uicore.registry.GetFocus()
            if focus and isinstance(focus, uicls.ScrollCore):
                if not uiutil.IsUnder(focus, uicore.layer.menu):
                    return 1
        self.wheeling = 1
        self.Scroll(uicore.uilib.dz / 240.0)
        self.wheeling = 0
        self.sr.scrollcontrols.AnimFade()
        return 1

    def GetNoItemNode(self, text, sublevel = 0, *args):
        return listentry.Get('Generic', {'label': text,
         'sublevel': sublevel})

    def ShowHint(self, hint = None):
        isNew = self.sr.hint is None or self.sr.hint.text != hint
        if self.sr.hint is None and hint:
            clipperWidth = self.GetContentWidth()
            self.sr.hint = uicls.EveCaptionMedium(parent=self.sr.clipper, align=uiconst.TOPLEFT, left=16, top=32, width=clipperWidth - 32, text=hint)
        elif self.sr.hint is not None and hint:
            self.sr.hint.text = hint
            self.sr.hint.state = uiconst.UI_DISABLED
            isNew = isNew or self.sr.hint.display == False
        elif self.sr.hint is not None and not hint:
            self.sr.hint.state = uiconst.UI_HIDDEN
        if self.sr.hint and self.sr.hint.display and isNew:
            uicore.animations.FadeTo(self.sr.hint, 0.0, 0.5, duration=0.3)

    def RecyclePanel(self, panel, fromWhere = None):
        if panel.__guid__ == 'listentry.VirtualContainerRow':
            subnodes = [ node for node in panel.sr.node.internalNodes if node is not None ]
            for node in subnodes:
                node.panel = None

        uicls.ScrollCore.RecyclePanel(self, panel, fromWhere)


class ScrollControls(uicls.ScrollControlsCore):
    __guid__ = 'uicls.ScrollControls'

    def ApplyAttributes(self, attributes):
        uicls.ScrollControlsCore.ApplyAttributes(self, attributes)
        self.animFadeThread = None

    def Prepare_(self):
        self.Prepare_ScrollHandle_()
        uicls.Fill(name='underlay', bgParent=self, color=util.Color.GetGrayRGBA(0.3, 0.1), shadowOffset=(-1, 0))

    def Prepare_ScrollHandle_(self):
        subparent = uicls.Container(name='subparent', parent=self, align=uiconst.TOALL, padding=(0, 0, 0, 0))
        self.sr.scrollhandle = uicls.ScrollHandle(name='__scrollhandle', parent=subparent, align=uiconst.TOPLEFT, pos=(0, 0, 0, 0), state=uiconst.UI_NORMAL)

    def AnimFade(self):
        self.fadeEndTime = blue.os.GetTime() + 0.3 * SEC
        if not self.animFadeThread:
            uicore.animations.FadeIn(self.sr.scrollhandle.sr.hilite, 0.5, duration=0.1)
            uthread.new(self._AnimFadeThread)

    def _AnimFadeThread(self):
        while blue.os.GetTime() < self.fadeEndTime:
            blue.synchro.Yield()

        if uicore.uilib.mouseOver != self.sr.scrollhandle:
            uicore.animations.FadeOut(self.sr.scrollhandle.sr.hilite, duration=0.5)
        self.animFadeThread = None


class ScrollHandle(uicls.ScrollHandleCore):
    __guid__ = 'uicls.ScrollHandle'

    def Prepare_(self):
        self.fill = uicls.GradientSprite(bgParent=self, rotation=0, rgbData=[(0, (1.0, 1.0, 1.0))], alphaData=[(0.0, 0.0),
         (0.1, 0.1),
         (0.9, 0.1),
         (1.0, 0.0)])
        self.Prepare_Hilite_()

    def Prepare_Hilite_(self):
        self.sr.hilite = uicls.Fill(name='hilite', parent=self, color=(1.0, 1.0, 1.0, 0.0))


class ColumnHeader(uicls.ScrollColumnHeaderCore):
    __guid__ = 'uicls.ScrollColumnHeader'

    def Prepare_Label_(self):
        textclipper = uicls.Container(name='textclipper', parent=self, align=uiconst.TOALL, padding=(6, 2, 6, 0), state=uiconst.UI_PICKCHILDREN, clipChildren=1)
        self.sr.label = uicls.EveLabelSmall(text='', parent=textclipper, hilightable=1, state=uiconst.UI_DISABLED)