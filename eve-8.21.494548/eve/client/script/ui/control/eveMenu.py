#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/control/eveMenu.py
import uicls
import uiutil
import uiconst
import crimewatchConst

class DropDownMenu(uicls.DropDownMenuCore):
    __guid__ = 'uicls.DropDownMenu'

    def Prepare_Background_(self, *args):
        self.sr.underlay = uicls.WindowUnderlay(parent=self, transparent=False, padding=(0, 0, 0, 0))


class MenuEntryView(uicls.MenuEntryViewCore):
    __guid__ = 'uicls.MenuEntryView'

    def Prepare_Label_(self, *args):
        self.sr.label = uicls.EveLabelSmall(parent=self, left=8, top=1, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)

    def Prepare_Hilite_(self, *args):
        self.sr.hilite = uicls.Fill(parent=self, color=(1.0, 1.0, 1.0, 0.25), padTop=1)


class SuspectMenuEntryView(MenuEntryView):
    __guid__ = 'uicls.SuspectMenuEntryView'
    default_warningColor = crimewatchConst.Colors.Suspect.GetRGBA()

    def ApplyAttributes(self, attributes):
        MenuEntryView.ApplyAttributes(self, attributes)
        uicls.Sprite(texturePath='res:/UI/Texture/Crimewatch/Crimewatch_SuspectCriminal_Small.png', parent=self, pos=(4, 3, 9, 10), align=uiconst.RELATIVE, idx=0, state=uiconst.UI_DISABLED, color=self.default_warningColor)
        self.sr.label.left = 16
        self.sr.label.color.SetRGBA(*self.default_warningColor)


class CriminalMenuEntryView(SuspectMenuEntryView):
    __guid__ = 'uicls.CriminalMenuEntryView'
    default_warningColor = crimewatchConst.Colors.Criminal.GetRGBA()