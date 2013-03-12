#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/stateFlag.py
import uiconst
import uicls

class StateFlag(uicls.Container):
    __guid__ = 'uicls.StateFlag'
    default_width = 9
    default_height = 9
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOPRIGHT
    default_name = 'flag'
    default_idx = 0

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.flagIcon = uicls.Sprite(parent=self, pos=(0, 0, 10, 10), name='icon', state=uiconst.UI_DISABLED, rectWidth=10, rectHeight=10, texturePath='res:/UI/Texture/classes/Bracket/flagIcons.png', align=uiconst.RELATIVE)
        self.flagBackground = uicls.Fill(parent=self)
        self.LoadFromFlag()

    def LoadFromFlag(self, flagCode = 0, showHint = False):
        if flagCode:
            stateSvc = sm.GetService('state')
            uiSvc = sm.GetService('ui')
            props = stateSvc.GetStateProps(flagCode)
            self.flagIcon.color.SetRGBA(*props.iconColor)
            col = stateSvc.GetStateFlagColor(flagCode)
            blink = stateSvc.GetStateFlagBlink(flagCode)
            self.flagBackground.color.SetRGB(*col)
            self.flagBackground.color.a *= 0.75
            if blink:
                uiSvc.BlinkSpriteA(self.flagIcon, 1.0, 500, None, passColor=0)
                uiSvc.BlinkSpriteA(self.flagBackground, self.flagIcon.color.a, 500, None, passColor=0)
            else:
                uiSvc.StopBlink(self.flagIcon)
                uiSvc.StopBlink(self.flagBackground)
            iconNum = props.iconIndex + 1
            if showHint:
                self.hint = props.text
            self.flagIcon.rectLeft = iconNum * 10
            self.display = True
        else:
            self.display = False