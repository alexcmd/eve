#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/control/eveSinglelineEdit.py
import weakref
import uiconst
import log
import uicls
import localization
import util
import uiutil

class SinglelineEdit(uicls.SinglelineEditCore):
    __guid__ = 'uicls.SinglelineEdit'
    default_left = 0
    default_top = 2
    default_width = 80
    default_height = 18
    default_align = uiconst.TOPLEFT

    def ApplyAttributes(self, attributes):
        uicls.SinglelineEditCore.ApplyAttributes(self, attributes)
        self.displayHistory = True
        if self.GetAlign() == uiconst.TOALL:
            self.height = 0
        else:
            self.height = self.default_height
        self.isTypeField = attributes.isTypeField
        self.isCharacterField = attributes.isCharacterField

    def Prepare_(self):
        self.sr.text = uicls.EveLabelMedium(name='edittext', parent=self._textClipper, left=self.TEXTLEFTMARGIN, state=uiconst.UI_DISABLED, maxLines=1, align=uiconst.CENTERLEFT)
        self.sr.hinttext = uicls.EveLabelMedium(parent=self._textClipper, name='hinttext', align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, maxLines=1, left=self.TEXTLEFTMARGIN)
        self.capsWarning = uicls.CapsHint(parent=uicore.layer.hint, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, idx=0)
        self.capsWarning.editControl = self
        self.capsWarning.pointer.SetTexturePath('res:/UI/Texture/classes/Hint/pointerToTopLeft.png')
        self.sr.background = uicls.Container(name='_underlay', parent=self, state=uiconst.UI_DISABLED)
        self.sr.backgroundFrame = uicls.BumpedUnderlay(parent=self.sr.background)
        sm.GetService('window').CheckControlAppearance(self)
        self.Prepare_ActiveFrame_()

    def SetLabel(self, text):
        self.sr.label = uicls.EveLabelSmall(parent=self, name='__caption', text=text, state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT, idx=0)
        self.sr.label.top = -self.sr.label.textheight
        if self.adjustWidth:
            self.width = max(self.width, self.sr.label.textwidth)

    def OnDropData(self, dragObj, nodes):
        uicls.SinglelineEditCore.OnDropData(self, dragObj, nodes)
        if self.isTypeField:
            self.OnDropType(dragObj, nodes)
        if self.isCharacterField:
            self.OnDropCharacter(dragObj, nodes)

    def OnDropType(self, dragObj, nodes):
        node = nodes[0]
        guid = node.Get('__guid__', None)
        typeID = None
        if guid in ('xtriui.ShipUIModule', 'xtriui.InvItem', 'listentry.InvItem', 'listentry.InvAssetItem'):
            typeID = getattr(node.item, 'typeID', None)
        elif guid in ('listentry.GenericMarketItem', 'listentry.QuickbarItem'):
            typeID = getattr(node, 'typeID', None)
        if typeID:
            typeName = cfg.invtypes.Get(typeID).name
            self.SetValue(typeName)

    def OnDropCharacter(self, dragObj, nodes):
        node = nodes[0]
        charID = None
        if node.Get('__guid__', None) == 'TextLink' and node.Get('url', '').startswith('showinfo'):
            parts = node.Get('url', '').split('//')
            charID = int(parts[-1])
        elif node.Get('__guid__', None) not in uiutil.AllUserEntries() + ['TextLink']:
            return
        if charID is None:
            charID = node.charID
        if util.IsCharacter(charID):
            charName = cfg.eveowners.Get(charID).name
            self.SetValue(charName)


class CapsHint(uicls.Hint):
    __guid__ = 'uicls.CapsHint'
    default_name = 'capshint'

    def Prepare_(self):
        uicls.Hint.Prepare_(self)
        self.frame.SetRGBA(0, 0, 0, 1)
        self.pointer = uicls.Sprite(parent=self, name='leftPointer', pos=(-8, -8, 18, 12), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Hint/pointerToTopLeft.png', color=(1, 1, 1, 1))

    def ShowHint(self):
        if self.parent:
            self.LoadHint(localization.GetByLabel('/Carbon/UI/Common/CapsLockWarning'))
            self.left = self.editControl.absoluteRight + 10
            self.top = self.editControl.absoluteTop + self.pointer.height