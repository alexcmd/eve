#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/station/fw/warzoneControl.py
import uicls
import uiconst
import localization
import localizationUtil
import uthread
import facwarCommon
import blue
from math import pi, ceil
SIDE_WIDTH = 0.1

class FWWarzoneControl(uicls.Container):
    __guid__ = 'uicls.FWWarzoneControl'
    default_height = 140
    TIERHINTS = ('UI/FactionWarfare/Tier1Hint', 'UI/FactionWarfare/Tier2Hint', 'UI/FactionWarfare/Tier3Hint', 'UI/FactionWarfare/Tier4Hint', 'UI/FactionWarfare/Tier5Hint')

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        leftCont = uicls.Container(name='leftCont', parent=self, align=uiconst.TOLEFT_PROP, width=SIDE_WIDTH)
        self.friendIcon = uicls.LogoIcon(name='friendIcon', parent=leftCont, align=uiconst.CENTER, width=32, height=32, top=-20, ignoreSize=True)
        rightCont = uicls.Container(name='leftCont', parent=self, align=uiconst.TORIGHT_PROP, width=SIDE_WIDTH)
        self.foeIcon = uicls.LogoIcon(name='foeIcon', parent=rightCont, align=uiconst.CENTER, width=32, height=32, top=20, ignoreSize=True)
        self.topCont = uicls.Container(name='topCont', parent=self, align=uiconst.TOTOP_PROP, height=0.4)
        self.bottomCont = uicls.Container(name='bottomCont', parent=self, align=uiconst.TOBOTTOM_PROP, height=0.4)
        self.centerCont = uicls.Container(name='centerCont', parent=self, bgColor=facwarCommon.COLOR_CENTER_BG, padding=2)
        w, h = self.centerCont.GetAbsoluteSize()
        spWidth = 134 / 16.0 * h
        self.friendBar = uicls.Container(parent=self.centerCont, align=uiconst.TOLEFT_PROP, state=uiconst.UI_NORMAL, bgColor=facwarCommon.COLOR_FRIEND_BAR, clipChildren=True)
        self.friendBarSprite = uicls.Sprite(parent=self.friendBar, state=uiconst.UI_HIDDEN, texturePath='res:/ui/texture/classes/InfluenceBar/influenceBarPositive.png', color=facwarCommon.COLOR_FRIEND_LIGHT, align=uiconst.TOLEFT, width=spWidth)
        self.friendPointer = uicls.Container(name='friendPointer', align=uiconst.TOPLEFT_PROP, parent=self, pos=(0.0, 0.5, 2, 0.2), idx=0)
        uicls.Line(parent=self.friendPointer, align=uiconst.TOLEFT, weight=2, padBottom=2, color=facwarCommon.COLOR_FRIEND_LIGHT)
        self.friendPointerTxt = uicls.EveHeaderLarge(name='friendPointerTxt', parent=self.friendPointer, align=uiconst.CENTERTOP, top=-28)
        uicls.Sprite(name='friendTriangle', parent=self.friendPointer, texturePath='res:/ui/texture/icons/105_32_15.png', color=facwarCommon.COLOR_FRIEND_LIGHT, align=uiconst.CENTERTOP, rotation=pi / 2, width=32, height=32, top=-19)
        self.foeBar = uicls.Container(parent=self.centerCont, align=uiconst.TORIGHT_PROP, state=uiconst.UI_NORMAL, bgColor=facwarCommon.COLOR_FOE_BAR, clipChildren=True)
        self.foeBarSprite = uicls.Sprite(parent=self.foeBar, state=uiconst.UI_HIDDEN, texturePath='res:/ui/texture/classes/InfluenceBar/influenceBarPositive.png', color=facwarCommon.COLOR_FOE_LIGHT, align=uiconst.TORIGHT, width=spWidth)
        self.foePointer = uicls.Container(name='foePointer', align=uiconst.TOPLEFT_PROP, parent=self, pos=(0.0, 0.5, 2, 0.2), idx=0)
        uicls.Line(parent=self.foePointer, align=uiconst.TORIGHT, weight=2, padTop=2, color=facwarCommon.COLOR_FOE_LIGHT)
        self.foePointerTxt = uicls.EveHeaderLarge(name='foePointerTxt', parent=self.foePointer, align=uiconst.CENTERBOTTOM, top=-28)
        uicls.Sprite(name='foeTriangle', parent=self.foePointer, texturePath='res:/ui/texture/icons/105_32_15.png', color=facwarCommon.COLOR_FOE_LIGHT, align=uiconst.CENTERBOTTOM, rotation=-pi / 2, width=32, height=32, top=-19)
        uthread.new(self.FetchValues)
        uthread.new(self.AnimateBars)

    def FetchValues(self):
        fwSvc = sm.StartService('facwar')
        self.friendID = fwSvc.GetActiveFactionID()
        warzoneInfo = fwSvc.GetFacWarZoneInfo(self.friendID)
        self.foeID = warzoneInfo.enemyFactionID
        self.friendPoints = warzoneInfo.factionPoints
        self.foePoints = warzoneInfo.enemyFactionPoints
        self.totalPoints = warzoneInfo.maxWarZonePoints
        self.friendIsAdvancing = warzoneInfo.zonesAdvancing[self.friendID]
        self.foeIsAdvancing = warzoneInfo.zonesAdvancing[self.foeID]
        self.UpdateValues()

    def UpdateValues(self):
        friendProportion = self.friendPoints / self.totalPoints
        foeProportion = self.foePoints / self.totalPoints
        self.friendBar.width = friendProportion
        self.foeBar.width = foeProportion
        self.friendBar.hint = localization.GetByLabel('UI/FactionWarfare/WarzoneProgress', points=self.friendPoints, pointsTotal=int(self.totalPoints))
        self.foeBar.hint = localization.GetByLabel('UI/FactionWarfare/WarzoneProgress', points=self.foePoints, pointsTotal=int(self.totalPoints))
        self.friendPointer.left = SIDE_WIDTH + (1.0 - 2 * SIDE_WIDTH) * friendProportion
        self.foePointer.left = 1.0 - SIDE_WIDTH - (1.0 - 2 * SIDE_WIDTH) * foeProportion
        self.friendPointerTxt.text = '%s%%' % localizationUtil.FormatNumeric(100 * friendProportion, decimalPlaces=1)
        self.foePointerTxt.text = '%s%%' % localizationUtil.FormatNumeric(100 * foeProportion, decimalPlaces=1)
        self.ConstructFriendSquares(friendProportion)
        self.ConstructFoeSquares(foeProportion)
        iconID = self.friendIcon.GetFactionIconID(self.friendID, True)
        self.friendIcon.LoadIcon(iconID, True)
        iconID = self.foeIcon.GetFactionIconID(self.foeID, True)
        self.foeIcon.LoadIcon(iconID, True)

    def AnimateBars(self):
        duration = 7.0
        blue.synchro.Sleep(1000)
        while not self.destroyed:
            w, h = self.centerCont.GetAbsoluteSize()
            self.friendBarSprite.state = uiconst.UI_DISABLED
            if self.friendIsAdvancing:
                self.friendBarSprite.rotation = 0.0
                uicore.animations.MorphScalar(self.friendBarSprite, 'left', -w, w, curveType=uiconst.ANIM_LINEAR, duration=duration)
            else:
                self.friendBarSprite.rotation = pi
                uicore.animations.MorphScalar(self.friendBarSprite, 'left', w, -w, curveType=uiconst.ANIM_LINEAR, duration=duration)
            self.foeBarSprite.state = uiconst.UI_DISABLED
            if self.foeIsAdvancing:
                self.foeBarSprite.rotation = pi
                uicore.animations.MorphScalar(self.foeBarSprite, 'left', -w, w, curveType=uiconst.ANIM_LINEAR, duration=duration)
            else:
                self.foeBarSprite.rotation = 0.0
                uicore.animations.MorphScalar(self.foeBarSprite, 'left', w, -w, curveType=uiconst.ANIM_LINEAR, duration=duration)
            blue.synchro.SleepWallclock(duration * 1000)

    def ConstructFriendSquares(self, proportion):
        self.topCont.Flush()
        for i in xrange(5):
            cont = uicls.Container(parent=self.topCont, align=uiconst.TOLEFT_PROP, state=uiconst.UI_NORMAL, width=0.2, padding=(0, 20, 0, 2), hint=localization.GetByLabel(self.TIERHINTS[i]))
            subCont = uicls.Container(parent=cont, padding=(2, 0, 2, 0))
            uicls.Sprite(bgParent=subCont, texturePath='res:/UI/Texture/Classes/FWWindow/TierBlock.png', opacity=0.5)
            uicls.Fill(bgParent=subCont, color=facwarCommon.COLOR_FRIEND)
            if proportion * 5 < i:
                cont.opacity = 0.2
            uicls.EveHeaderLarge(parent=subCont, align=uiconst.CENTERTOP, top=-22, text=localization.GetByLabel('UI/FactionWarfare/TierNum', tierNum=i + 1), color=facwarCommon.COLOR_FRIEND_LIGHT)

    def ConstructFoeSquares(self, proportion):
        self.bottomCont.Flush()
        for i in xrange(int(ceil(proportion * 5))):
            cont = uicls.Container(parent=self.bottomCont, align=uiconst.TORIGHT_PROP, state=uiconst.UI_NORMAL, width=0.2, padding=(0, 2, 0, 20), hint=localization.GetByLabel(self.TIERHINTS[i]))
            subCont = uicls.Container(parent=cont, padding=(2, 0, 2, 0))
            uicls.Sprite(bgParent=subCont, texturePath='res:/UI/Texture/Classes/FWWindow/TierBlock.png', opacity=0.5)
            uicls.Fill(bgParent=subCont, color=facwarCommon.COLOR_FOE)
            uicls.EveHeaderLarge(parent=subCont, align=uiconst.CENTERBOTTOM, top=-22, text=localization.GetByLabel('UI/FactionWarfare/TierNum', tierNum=i + 1), color=facwarCommon.COLOR_FOE_LIGHT)