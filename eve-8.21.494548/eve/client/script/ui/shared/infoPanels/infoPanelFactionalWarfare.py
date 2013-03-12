#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/infoPanels/infoPanelFactionalWarfare.py
import uicls
import uiconst
import infoPanel
import util
import localization
import facwarCommon
import uthread

class InfoPanelFactionalWarfare(uicls.InfoPanelBase):
    __guid__ = 'uicls.InfoPanelFactionalWarfare'
    default_name = 'InfoPanelFactionalWarfare'
    default_iconTexturePath = 'res:/UI/Texture/Classes/InfoPanels/FactionalWarfare.png'
    default_state = uiconst.UI_PICKCHILDREN
    default_height = 120
    label = 'UI/Map/StarMap/FactionalWarfare'
    hasSettings = False
    panelTypeID = infoPanel.PANEL_FACTIONAL_WARFARE
    COLOR_RED = (0.5, 0.0, 0.0, 1.0)
    COLOR_WHITE = (0.5, 0.5, 0.5, 1.0)
    ICONSIZE = 20

    def ApplyAttributes(self, attributes):
        uicls.InfoPanelBase.ApplyAttributes(self, attributes)
        self.isGaugeInitialized = False
        self.benefitIcons = []
        self.factionIcon = None
        self.headerTextCont = uicls.Container(name='headerTextCont', parent=self.headerCont, align=uiconst.TOALL)
        self.title = self.headerCls(name='title', text='<color=white url=localsvc:service=cmd&method=OpenMilitia>%s</url>' % localization.GetByLabel('UI/FactionWarfare/FactionalWarfare'), parent=self.headerTextCont, align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL)
        self.subTitle = uicls.EveHeaderMedium(name='subtitle', parent=self.headerTextCont, align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL, left=self.title.width + 5, top=2, bold=True)
        self.headerControlGauge = uicls.Gauge(parent=self.headerCont, align=uiconst.TOALL, gaugeHeight=16, padTop=6, padRight=6, color=(0.5, 0.5, 0.5, 1.0), width=0, height=0, state=uiconst.UI_HIDDEN)
        self.headerControlGauge.OnClick = self.topCont.OnClick
        self.headerControlGauge.OnMouseEnter = self.topCont.OnMouseEnter
        self.headerControlGauge.OnMouseExit = self.topCont.OnMouseExit
        self.headerControlGauge.GetHint = self.GetGaugeHint
        self.controlGauge = uicls.Gauge(parent=self.mainCont, align=uiconst.TOTOP, padTop=2, gaugeHeight=15, color=(0.5, 0.5, 0.5, 1.0))
        self.controlGauge.GetHint = self.GetGaugeHint
        self.bottomContainer = uicls.ContainerAutoSize(parent=self.mainCont, name='bottomContainer', align=uiconst.TOTOP)
        self.bottomContainer.EnableAutoSize()
        self.mainCont.EnableAutoSize()

    @staticmethod
    def IsAvailable():
        return bool(session.solarsystemid2 in sm.GetService('facwar').GetFacWarSystems())

    def ConstructNormal(self):
        factionID = sm.GetService('facwar').GetSystemOccupier(session.solarsystemid2)
        self.subTitle.text = text = ('<url=showinfo:%s//%s>%s</url>' % (const.typeFaction, factionID, cfg.eveowners.Get(factionID).name),)
        self.upgradeLevel = sm.GetService('facwar').GetSolarSystemUpgradeLevel(session.solarsystemid2)
        self.bottomContainer.Flush()
        self.iconCont = uicls.Container(name='iconCont', align=uiconst.TOTOP, parent=self.bottomContainer, padTop=6, height=36)
        self.factionIcon = uicls.LogoIcon(name='factionIcon', itemID=factionID, parent=uicls.Container(parent=self.iconCont, align=uiconst.TOLEFT, width=36, padRight=5), align=uiconst.CENTER, size=32, ignoreSize=True, isSmall=True, opacity=0.0)
        if not self.upgradeLevel:
            text = localization.GetByLabel('UI/FactionWarfare/NoSystemBenefits')
        else:
            text = localization.GetByLabel('UI/FactionWarfare/SystemUpgradeBenefits', level=util.IntToRoman(self.upgradeLevel))
            benefits = sm.GetService('facwar').GetSystemUpgradeLevelBenefits(self.upgradeLevel)[:]
            benefits = list(benefits)
            benefits.reverse()
            self.benefitIcons = []
            for benefitType, benefitValue in benefits:
                benefitIcon = uicls.FWSystemBenefitIcon(parent=self.iconCont, align=uiconst.TOLEFT, padRight=12, benefitType=benefitType, benefitValue=benefitValue, opacity=0.0)
                self.benefitIcons.append(benefitIcon)

        benefitValue = sm.GetService('facwar').GetCurrentSystemEffectOfHeldDistricts()
        self.planetDistrictIcon = uicls.FWSystemBenefitIcon(align=uiconst.TORIGHT, parent=self.iconCont, height=self.ICONSIZE, padLeft=12, benefitType=facwarCommon.BENEFIT_PLANETDISTRICTS, benefitValue=benefitValue, opacity=0.0)
        self.benefitIcons.append(self.planetDistrictIcon)
        self.iconCont.display = bool(self.iconCont.children)
        self.UpdateGauge()

    def ConstructCompact(self):
        self.UpdateGauge()

    def OnStartModeChanged(self, oldMode):
        uthread.new(self._OnStartModeChanged, oldMode)

    def OnEndModeChanged(self, oldMode):
        if self.mode == infoPanel.MODE_NORMAL and oldMode:
            if self.factionIcon:
                uicore.animations.BlinkIn(self.factionIcon)
            for i, icon in enumerate(self.benefitIcons):
                uicore.animations.BlinkIn(icon, endVal=0.75, timeOffset=0.2 + i * 0.05)

        else:
            if self.factionIcon:
                self.factionIcon.opacity = 1.0
            for icon in self.benefitIcons:
                icon.opacity = 0.75

    def _OnStartModeChanged(self, oldMode):
        if self.mode == infoPanel.MODE_COMPACT:
            if oldMode:
                uicore.animations.FadeOut(self.headerTextCont, duration=0.3, sleep=True)
                self.headerTextCont.Hide()
                self.headerControlGauge.Show()
                uicore.animations.FadeTo(self.headerControlGauge, 0.0, 1.0, duration=0.3)
            else:
                self.headerTextCont.Hide()
                self.headerControlGauge.Show()
        elif self.headerControlGauge.display:
            uicore.animations.FadeOut(self.headerControlGauge, duration=0.3, sleep=True)
            self.headerControlGauge.Hide()
            self.headerTextCont.Show()
            uicore.animations.FadeTo(self.headerTextCont, 0.0, 1.0, duration=0.3)

    def UpdateGauge(self, animate = True):
        animate = animate and self.isGaugeInitialized
        for gauge in (self.controlGauge, self.headerControlGauge):
            fwSvc = sm.GetService('facwar')
            if fwSvc.GetSystemStatus() == const.contestionStateCaptured:
                gauge.SetValue(1.0)
                gauge.SetColor(self.COLOR_RED)
                uicore.animations.FadeTo(gauge, 0.5, 1.0, duration=1.5, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_WAVE)
            else:
                value = fwSvc.GetSystemContestedPercentage(session.solarsystemid2) / 100.0
                gauge.SetValue(value, animate=animate)
                if value >= 1.0:
                    gauge.SetColor(self.COLOR_RED)
                else:
                    gauge.SetColor(self.COLOR_WHITE)

        self.isGaugeInitialized = True

    def GetGaugeHint(self):
        captureStatus = sm.GetService('facwar').GetSystemCaptureStatus(session.solarsystemid2)
        hint = sm.GetService('facwar').GetSystemCaptureStatusTxt(session.solarsystemid2)
        if captureStatus == facwarCommon.STATE_CONTESTED:
            percentage = '%2.1f' % sm.GetService('facwar').GetSystemContestedPercentage(session.solarsystemid2)
            hint += '<br><color=gray>' + localization.GetByLabel('UI/FactionWarfare/StatusContestedHint', percentage=percentage)
        elif captureStatus == facwarCommon.STATE_VULNERABLE:
            hint += '<br><color=gray>' + localization.GetByLabel('UI/FactionWarfare/StatusVulnerableHint')
        return hint