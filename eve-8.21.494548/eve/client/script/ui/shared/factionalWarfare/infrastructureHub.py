#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/factionalWarfare/infrastructureHub.py
import uicls
import uiconst
import util
import uiutil
import localization
import localizationUtil
import blue
import uthread
import facwarCommon
import math
from math import pi

class FWInfrastructureHub(uicls.Window):
    __guid__ = 'form.FWInfrastructureHub'
    __notifyevents__ = ['OnSolarSystemLPChange', 'OnLPChange']
    default_windowID = 'FWInfrastructureHub'
    default_fixedWidth = 450
    default_fixedHeight = 620
    default_topParentHeight = 0
    default_iconNum = 'ui_61_128_3'
    default_caption = 'UI/FactionWarfare/IHub/IHubWndCaption'
    PADSIDE = 25
    PADTOP = 10

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.itemID = attributes.Get('itemID')
        lpPool = sm.GetService('facwar').GetSolarSystemLPs()
        topCont = uicls.Container(name='topCont', parent=self.sr.main, align=uiconst.TOTOP, height=40, padding=(self.PADSIDE,
         self.PADTOP,
         self.PADSIDE,
         self.PADSIDE))
        mainCont = uicls.ContainerAutoSize(name='mainCont', parent=self.sr.main, align=uiconst.TOTOP)
        bottomCont = uicls.Container(name='bottomCont', parent=self.sr.main, align=uiconst.TOBOTTOM, height=100, padTop=self.PADTOP)
        uicls.EveLabelLarge(parent=topCont, text=localization.GetByLabel('UI/FactionWarfare/IHub/SystemUpgradePanel', systemName=cfg.evelocations.Get(session.solarsystemid2).name), align=uiconst.TOPLEFT, top=5)
        uicls.EveLabelLarge(parent=topCont, text=localization.GetByLabel('UI/FactionWarfare/IHub/TotalLP'), align=uiconst.TOPRIGHT, top=5)
        self.lpPoolLabel = uicls.EveCaptionSmall(parent=topCont, align=uiconst.TOPRIGHT, top=25)
        limits = [0] + const.facwarSolarSystemUpgradeThresholds + [const.facwarSolarSystemMaxLPPool]
        self.upgradeBars = []
        for i in xrange(1, 7):
            bar = uicls.FWUpgradeLevelCont(parent=mainCont, align=uiconst.TOTOP, padding=(self.PADSIDE,
             0,
             10,
             10), lowerLimit=limits[i - 1], upperLimit=limits[i], lpAmount=lpPool, level=i, idx=0)
            self.upgradeBars.append(bar)

        self.bottomGradient = uicls.GradientSprite(bgParent=bottomCont, rotation=-pi / 2, rgbData=[(0, (0.3, 0.3, 0.3))], alphaData=[(0, 0.3), (0.9, 0.0)])
        self.bottomFlashEffect = uicls.GradientSprite(bgParent=bottomCont, rotation=-pi / 2, rgbData=[(0, (0.6, 0.6, 0.6))], alphaData=[(0, 0.3), (0.9, 0.0)], opacity=0.0)
        uicls.Line(parent=bottomCont, align=uiconst.TOTOP, color=(0.3, 0.3, 0.3, 0.3))
        bottomMainCont = uicls.Container(name='bottomMainCont', parent=bottomCont, align=uiconst.CENTER, width=450, height=100)
        self.myLPLabel = uicls.Label(parent=bottomMainCont, text=self.GetLPOwnedLabel(), align=uiconst.TOPLEFT, left=self.PADSIDE, top=self.PADTOP)
        self.bottomBottomCont = uicls.Container(name='bottomBottom', align=uiconst.TOPLEFT, pos=(self.PADSIDE,
         40,
         450,
         25), parent=bottomMainCont)
        self.donateAmountEdit = uicls.SinglelineEdit(parent=self.bottomBottomCont, name='donateAmountEdit', align=uiconst.TOLEFT, setvalue=0, width=155, OnReturn=self.OnDonateLPBtn, OnChange=self.OnDonateValueChanged)
        self.donateBtn = uicls.Button(parent=self.bottomBottomCont, align=uiconst.TOLEFT, func=self.OnDonateLPBtn, label=localization.GetByLabel('UI/FactionWarfare/IHub/DonateLPs'), padLeft=4)
        self.donationReceivedLabel = uicls.EveCaptionMedium(name='donationReceivedLabel', parent=bottomMainCont, align=uiconst.TOPLEFT, text=localization.GetByLabel('UI/FactionWarfare/IHub/DonationReceived'), left=self.PADSIDE, top=50, opacity=0.0)
        self.bottomTaxCont = uicls.Container(name='bottomTax', align=uiconst.TOPLEFT, pos=(self.PADSIDE,
         73,
         400,
         25), parent=bottomMainCont)
        self.myLPToIhubLabel = None
        factionID = sm.GetService('facwar').GetSystemOccupier(session.solarsystemid)
        self.myLPTaxLabel = uicls.Label(name='myLPTaxLabel', parent=self.bottomTaxCont, text=localization.GetByLabel('UI/FactionWarfare/IHub/maintenanceTax', tax=int(facwarCommon.GetDonationTax(factionID) * 100)), align=uiconst.TOLEFT, state=uiconst.UI_NORMAL, left=5)
        self.SetLPPoolAmount(lpPool)
        self.UpdateMyLPAmount()
        self.UpdateMyLPToIHubLabel()
        uthread.new(self.CheckOpenThread)

    def UpdateMyLPToIHubLabel(self, refreshTax = False):
        lpAmount = self.donateAmountEdit.GetValue()
        donationTax = facwarCommon.GetDonationTax(session.warfactionid)
        tax = math.ceil(donationTax * lpAmount)
        if self.myLPToIhubLabel:
            self.myLPToIhubLabel.Close()
        self.myLPToIhubLabel = uicls.Label(name='myLPToIhubLabel', parent=self.bottomTaxCont, align=uiconst.TOLEFT, idx=0, text=localization.GetByLabel('UI/FactionWarfare/IHub/TotalDonated', loyaltyPoints=localizationUtil.FormatNumeric(int(lpAmount - tax), useGrouping=True)))
        if refreshTax:
            if self.myLPTaxLabel:
                self.myLPTaxLabel.Close()
            self.myLPTaxLabel = uicls.Label(name='myLPTaxLabel', parent=self.bottomTaxCont, text=localization.GetByLabel('UI/FactionWarfare/IHub/maintenanceTax', tax=int(donationTax * 100)), align=uiconst.TOLEFT, state=uiconst.UI_NORMAL, left=5)
        self.myLPTaxLabel.hint = localization.GetByLabel('UI/FactionWarfare/LPAmount', lps=tax)

    def GetLPOwnedLabel(self):
        amount = self.GetMyLPs()
        factionID = sm.GetService('facwar').GetSystemOccupier(session.solarsystemid)
        militiaCorpID = sm.GetService('facwar').GetFactionMilitiaCorporation(factionID)
        return localization.GetByLabel('UI/FactionWarfare/IHub/LPOwned', LPCount=localizationUtil.FormatNumeric(amount, useGrouping=True), corpName=cfg.eveowners.Get(militiaCorpID).name)

    def CheckOpenThread(self):
        bp = sm.GetService('michelle').GetBallpark()
        while not self.destroyed:
            blue.synchro.SleepWallclock(1000)
            distance = bp.GetSurfaceDist(session.shipid, self.itemID)
            if distance > const.facwarIHubInteractDist:
                self.Close()

    def OnSessionChanged(self, *args):
        self.Close()

    def OnLPChange(self, changeType):
        self.UpdateMyLPAmount()

    def SetLPPoolAmount(self, amount):
        self.lpPoolLabel.SetText(localizationUtil.FormatNumeric(amount, useGrouping=True))

    def UpdateMyLPAmount(self):
        amount = self.GetMyLPs()
        self.myLPLabel.SetText(self.GetLPOwnedLabel())
        self.donateAmountEdit.IntMode(const.facwarMinLPDonation, amount)

    def OnDonateValueChanged(self, value):
        uthread.new(self.UpdateMyLPToIHubLabel)

    def OnDonateLPBtn(self, *args):
        if not self.bottomBottomCont.pickState:
            return
        pointsToDonate = self.donateAmountEdit.GetValue()
        if not pointsToDonate:
            return
        donationTax = facwarCommon.GetDonationTax(session.warfactionid)
        pointsToIHub = int(pointsToDonate - pointsToDonate * donationTax)
        try:
            sm.GetService('facwar').DonateLPsToSolarSystem(pointsToDonate, pointsToIHub)
        except UserError as e:
            if e.msg == 'FacWarDonationTaxChanged':
                sm.GetService('facwar').objectCaching.InvalidateCachedMethodCalls([('map', 'GetFacWarZoneInfo', (session.warfactionid,))])
                self.UpdateMyLPToIHubLabel(refreshTax=True)
                if uicore.Message('FacWarDonationTaxChanged', e.dict, uiconst.YESNO, uiconst.ID_YES) == uiconst.ID_YES:
                    newPointsToIhub = int(pointsToDonate * (1 - e.dict['taxNow'] / 100.0))
                    try:
                        sm.GetService('facwar').DonateLPsToSolarSystem(pointsToDonate, newPointsToIhub)
                    except UserError as e:
                        if e.msg == 'FacWarDonationTaxChanged':
                            return
                        raise 

                else:
                    return
            else:
                raise 

        self.donateAmountEdit.SetValue('0')
        uicore.animations.FadeIn(self.bottomFlashEffect, duration=0.3)
        self.bottomBottomCont.Disable()
        uicore.animations.FadeOut(self.bottomBottomCont, duration=0.1)
        self.bottomTaxCont.Disable()
        uicore.animations.FadeOut(self.bottomTaxCont, duration=0.1)
        blue.synchro.Sleep(300)
        uicore.animations.MoveInFromBottom(self.donationReceivedLabel, amount=5, duration=0.15)
        uicore.animations.FadeIn(self.donationReceivedLabel, sleep=True, duration=0.5)
        blue.synchro.Sleep(5000)
        uicore.animations.FadeOut(self.bottomFlashEffect, duration=0.3, sleep=True)
        uicore.animations.FadeOut(self.donationReceivedLabel, sleep=True, duration=0.3)
        uicore.animations.FadeIn(self.bottomBottomCont, duration=0.3)
        self.bottomBottomCont.Enable()
        uicore.animations.FadeIn(self.bottomTaxCont, duration=0.3)
        self.bottomTaxCont.Enable()

    def OnSolarSystemLPChange(self, oldPoints, newPoints):
        self.SetLPPoolAmount(newPoints)
        myLPs = self.GetMyLPs()
        self.donateAmountEdit.IntMode(const.facwarMinLPDonation, myLPs)
        self.UpdateMyLPAmount()
        if newPoints > oldPoints:
            for bar in self.upgradeBars:
                bar.SetLPAmount(newPoints)

        else:
            for bar in reversed(self.upgradeBars):
                bar.SetLPAmount(newPoints)

    def GetMyLPs(self):
        militiaCorpID = sm.GetService('facwar').GetFactionMilitiaCorporation(session.warfactionid)
        return sm.GetService('lpstore').GetMyLPs(militiaCorpID)


class FWUpgradeLevelCont(uicls.Container):
    __guid__ = 'uicls.FWUpgradeLevelCont'
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL
    default_height = 60
    default_opacity = 0.0

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.lowerLimit = attributes.lowerLimit
        self.upperLimit = attributes.upperLimit
        self.lpAmount = attributes.lpAmount
        self.lastAmount = 0
        self.level = attributes.level
        self.leftCont = uicls.Container(name='leftCont', parent=self, align=uiconst.TOLEFT_PROP, width=0.75)
        self.rightCont = uicls.Container(name='rightCont', parent=self)
        self.bgFrame = uicls.Frame(bgParent=self.leftCont, frameConst=uiconst.FRAME_BORDER1_CORNER1)
        self.bgGradient = uicls.GradientSprite(bgParent=self.leftCont, rotation=-pi / 2)
        levelName = uicls.EveCaptionLarge(parent=self.leftCont, text=self.GetLevelName(), top=5, left=10)
        if self.level == 6:
            levelName.fontsize = 16
        self.progressGauge = uicls.Gauge(parent=self.leftCont, value=0.0, color=(0.0, 0.31, 0.4, 1.0), backgroundColor=(0.1, 0.1, 0.1, 1.0), align=uiconst.TOBOTTOM, gaugeHeight=15, padding=2, opacity=0.0)
        self.progressGauge.GetHint = self.GetProgressGaugeHint
        self.iconCont = uicls.Container(name='iconCont', parent=self.leftCont, align=uiconst.TOPRIGHT, pos=(10, 4, 300, 20))
        self.ConstructIcons()
        self.checkboxSprite = uicls.Sprite(name='checkboxSprite', parent=self.rightCont, align=uiconst.CENTERLEFT, pos=(15, 0, 16, 16))
        uicls.EveLabelLarge(parent=self.rightCont, text=localizationUtil.FormatNumeric(self.upperLimit, useGrouping=True), align=uiconst.CENTERLEFT, left=50)
        self.SetLPAmount(self.lpAmount, init=True)

    def GetProgressGaugeHint(self):
        if self.lpAmount > self.lowerLimit and self.lpAmount < self.upperLimit:
            return localization.GetByLabel('UI/FactionWarfare/IHub/LevelUnlockHint', num=self.lpAmount - self.lowerLimit, numTotal=self.upperLimit - self.lowerLimit)

    def ConstructIcons(self):
        benefits = sm.GetService('facwar').GetSystemUpgradeLevelBenefits(self.level)
        for benefitType, benefitValue in benefits:
            uicls.FWSystemBenefitIcon(parent=self.iconCont, align=uiconst.TORIGHT, height=self.iconCont.height, padLeft=12, benefitType=benefitType, benefitValue=benefitValue)

    def GetLevelName(self):
        if self.level == 6:
            return localization.GetByLabel('UI/FactionWarfare/IHub/Buffer')
        return uiutil.IntToRoman(self.level)

    def SetLPAmount(self, lpAmount, init = False):
        self.lastAmount = self.lpAmount
        self.lpAmount = lpAmount
        if not init:
            if self.lpAmount < self.lowerLimit and self.lastAmount < self.lowerLimit:
                return
            if self.lpAmount >= self.upperLimit and self.lastAmount >= self.upperLimit:
                return
        if self.lpAmount >= self.upperLimit:
            uicore.animations.FadeIn(self)
            self.bgGradient.SetGradient([(0, (0.3, 0.5, 0.3))], [(0, 0.2), (1.0, 0.7)])
            self.HideBar(init=init)
            self.SetBGFrameColor((0.0, 0.4, 0.0, 0.3), init)
            self.checkboxSprite.texturePath = 'res:/UI/Texture/icons/38_16_193.png'
            self.checkboxSprite.opacity = 1.0
            self.iconCont.opacity = 1.0
        elif self.lpAmount >= self.lowerLimit:
            uicore.animations.FadeIn(self)
            self.ShowBar(init=init)
            self.bgGradient.SetGradient([(0, (0.3, 0.3, 0.3))], [(0, 0.2), (1.0, 0.7)])
            self.SetBGFrameColor(util.Color.GetGrayRGBA(0.5, 0.3), init)
            self.checkboxSprite.texturePath = 'res:/UI/Texture/classes/FWInfrastructureHub/smallCircle.png'
            self.checkboxSprite.opacity = 0.3
            self.iconCont.opacity = 0.3
        else:
            uicore.animations.FadeTo(self, self.opacity, 0.3)
            self.bgGradient.SetGradient([(0, (0.3, 0.3, 0.3))], [(0, 0.2), (1.0, 0.7)])
            self.HideBar(init=init)
            self.SetBGFrameColor(util.Color.GetGrayRGBA(0.5, 0.3), init)
            self.checkboxSprite.texturePath = 'res:/UI/Texture/classes/FWInfrastructureHub/smallCircle.png'
            self.checkboxSprite.opacity = 1.0
            self.iconCont.opacity = 1.0

    def SetBGFrameColor(self, color, init):
        color = util.Color.GetGrayRGBA(0.5, 0.3)
        if not init:
            uicore.animations.SpColorMorphTo(self.bgFrame, endColor=color)
        else:
            self.bgFrame.color = color

    def ShowBar(self, init = False):
        if self.lastAmount and self.lastAmount > self.lpAmount:
            self.progressGauge.SetValueInstantly(self.GetLastValue())
        if init:
            self.progressGauge.opacity = 1.0
        else:
            uicore.animations.FadeIn(self.progressGauge)
        self.progressGauge.SetValue(self.GetValue())

    def HideBar(self, init = False):
        if not init:
            self.progressGauge.SetValueInstantly(self.GetLastValue())
            self.progressGauge.SetValue(self.GetValue())
            if self.progressGauge.opacity < 1.0:
                uicore.animations.FadeIn(self.progressGauge, duration=0.1, sleep=True)
            uicore.animations.FadeOut(self.progressGauge, sleep=True)

    def GetValue(self):
        value = (self.lpAmount - self.lowerLimit) / float(self.upperLimit - self.lowerLimit)
        return max(0.0, min(value, 1.0))

    def GetLastValue(self):
        value = (self.lastAmount - self.lowerLimit) / float(self.upperLimit - self.lowerLimit)
        return max(0.0, min(value, 1.0))


class FWSystemBenefitIcon(uicls.ContainerAutoSize):
    __guid__ = 'uicls.FWSystemBenefitIcon'
    default_state = uiconst.UI_NORMAL
    default_width = 22

    def ApplyAttributes(self, attributes):
        uicls.ContainerAutoSize.ApplyAttributes(self, attributes)
        self.benefitType = attributes.benefitType
        self.benefitValue = attributes.benefitValue
        uicls.Sprite(parent=self, state=uiconst.UI_DISABLED, align=uiconst.TOTOP, texturePath=self.GetTexturePath(), height=self.width, opacity=0.75)
        labelCont = uicls.Container(name='labelCont', parent=self, align=uiconst.TOTOP, height=12)
        uicls.EveLabelSmall(parent=labelCont, align=uiconst.CENTER, padTop=3, text=self.GetLabel(), color=util.Color.WHITE)

    def GetTexturePath(self):
        return {facwarCommon.BENEFIT_MEDICALCLONES: 'res:/ui/texture/classes/FWInfrastructureHub/medicalClones.png',
         facwarCommon.BENEFIT_MARKETREDUCTION: 'res:/ui/texture/classes/FWInfrastructureHub/marketReduction.png',
         facwarCommon.BENEFIT_STATIONCOPYSLOTS: 'res:/ui/texture/classes/FWInfrastructureHub/stationCopySlots.png',
         facwarCommon.BENEFIT_PLANETDISTRICTS: 'res:/ui/texture/classes/FWInfrastructureHub/planetDistrict.png'}.get(self.benefitType)

    def GetLabel(self):
        return {facwarCommon.BENEFIT_MEDICALCLONES: '%s%%',
         facwarCommon.BENEFIT_MARKETREDUCTION: '%s%%',
         facwarCommon.BENEFIT_STATIONCOPYSLOTS: '+%s',
         facwarCommon.BENEFIT_PLANETDISTRICTS: '%2.1f%%'}.get(self.benefitType) % self.benefitValue

    def GetHint(self):
        if self.benefitType == facwarCommon.BENEFIT_MEDICALCLONES:
            return localization.GetByLabel('UI/FactionWarfare/IHub/UpgradeHintMedicalClones', num=self.benefitValue)
        if self.benefitType == facwarCommon.BENEFIT_MARKETREDUCTION:
            return localization.GetByLabel('UI/FactionWarfare/IHub/UpgradeHintMarketReduction', num=self.benefitValue)
        if self.benefitType == facwarCommon.BENEFIT_STATIONCOPYSLOTS:
            return localization.GetByLabel('UI/FactionWarfare/IHub/UpgradeHintStationSlots', num=self.benefitValue)
        if self.benefitType == facwarCommon.BENEFIT_PLANETDISTRICTS:
            fwSvc = sm.GetService('facwar')
            base = const.facwarBaseVictoryPointsThreshold
            modifier = fwSvc.GetCurrentSystemEffectOfHeldDistricts()
            if modifier < 0:
                sign = '-'
            else:
                sign = '+'
            total = fwSvc.GetCurrentSystemVictoryPointThreshold()
            return localization.GetByLabel('UI/FactionWarfare/IHub/UpgradeHintPlanetDistrict', base=base, sign=sign, modifier=math.fabs(modifier), total=total)