#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/neocom/corporation/corp_ui_recruitment.py
import form
import listentry
import uix
import uiutil
import uthread
import util
import xtriui
import blue
import uiconst
import uicls
import log
import math
import contractutils
import localization
import fontConst
import corputil
import base
import time
from math import pi
AREA_OF_OPERATIONS_GROUPID = 6
TIMEZONE_GROUPID = 8
PLAYSTYLE_GROUPID = 11
LANGUAGE_GROUPID = 10
ENGLISH_TYPEID = 8
GERMAN_TYPEID = 9
SPANISH_TYPEID = 10
RUSSIAN_TYPEID = 11
FRENCH_TYPEID = 12
JAPANESE_TYPEID = 43
EXPLORATION_TYPEID = 29
MISSIONRUNNING_TYPEID = 26
NEWPILOTFRIENTLY_TYPEID = 36
ALLIANCEWARFARE_TYPEID = 27
FACTIONWARFARE_TYPEID = 33
PIRACY_TYPEID = 34
SMALLSCALEGANGS_TYPEID = 35
TRADEANDINDUSTRY_TYPEID = 25
MINING_TYPEID = 30
ROLEPLAY_TYPEID = 42
INCURSIONS_TYPEID = 44
MANUFACTURING_TYPEID = 45
RESEARCH_TYPEID = 46
BOUNTYHUNTING_TYPEID = 47
HIGHSEC_TYPEID = 13
LOWSEC_TYPEID = 39
NULLSEC_TYPEID = 40
WORMHOLESPACE_TYPEID = 41
PVECOMBINED_ID = 100
PVPCOMBINED_ID = 200
TRADECOMBINED_ID = 300
OTHERCOMBINED_ID = 400
PVECOMBINED_TYPEIDS = (EXPLORATION_TYPEID, MISSIONRUNNING_TYPEID, INCURSIONS_TYPEID)
PVPCOMBINED_TYPEIDS = (ALLIANCEWARFARE_TYPEID,
 BOUNTYHUNTING_TYPEID,
 FACTIONWARFARE_TYPEID,
 PIRACY_TYPEID,
 SMALLSCALEGANGS_TYPEID)
TRADECOMBINED_TYPEIDS = (TRADEANDINDUSTRY_TYPEID,
 MINING_TYPEID,
 RESEARCH_TYPEID,
 MANUFACTURING_TYPEID)
OTHER_TYPEIDS = (NEWPILOTFRIENTLY_TYPEID, ROLEPLAY_TYPEID)
PLAYSTYLE_GROUPS = (PVECOMBINED_ID,
 PVPCOMBINED_ID,
 TRADECOMBINED_ID,
 OTHERCOMBINED_ID)
COMBINED_GROUPS = {PVECOMBINED_ID: uiutil.Bunch(playstyleTypeIDs=PVECOMBINED_TYPEIDS, combinedNamePath='UI/Corporations/CorporationWindow/Recruitment/PVE'),
 PVPCOMBINED_ID: uiutil.Bunch(playstyleTypeIDs=PVPCOMBINED_TYPEIDS, combinedNamePath='UI/Corporations/CorporationWindow/Recruitment/PVP'),
 TRADECOMBINED_ID: uiutil.Bunch(playstyleTypeIDs=TRADECOMBINED_TYPEIDS, combinedNamePath='UI/Corporations/CorporationWindow/Recruitment/Trade'),
 OTHERCOMBINED_ID: uiutil.Bunch(playstyleTypeIDs=OTHER_TYPEIDS, combinedNamePath='UI/Corporations/CorporationWindow/Recruitment/Other')}
FILTERSTATE_WANT = 1
SHOWSEARCHMATCH = True
CHECKBOX_ACTIVE_ICON = 'res:/UI/Texture/classes/UtilMenu/checkBoxActive.png'
CHECKBOX_INACTIVE_ICON = 'res:/UI/Texture/classes/UtilMenu/checkBoxInactive.png'
MATCHED_COLOR = '<color=0xbfffffff>'
UNMATCHED_COLOR = '<color=0x2fffffff>'
WHITE_COLOR = '<color=0xffffffff>'

def HasAccess(corporationID):
    if corporationID != session.corpid:
        return False
    if const.corpRolePersonnelManager & session.corprole != const.corpRolePersonnelManager:
        return False
    return True


class CorpRecruitment(uicls.Container):
    __guid__ = 'form.CorpRecruitment'
    __nonpersistvars__ = []
    __notifyevents__ = ['OnCorporationChanged']

    def init(self):
        self.corpSvc = sm.GetService('corp')

    def Load(self, args):
        if not self.sr.Get('inited', 0):
            self.sr.inited = 1
            self.corpAdvertContainer = uicls.Container(parent=self, name='corpAdvertContainer', align=uiconst.TOALL)
            self.corpAdvertContentContainer = uicls.Container(parent=self.corpAdvertContainer, name='corpAdvertContentContainer', align=uiconst.TOALL)
            self.searchContainer = uicls.CorpRecruitmentContainerSearch(parent=self, name='searchContainer', align=uiconst.TOALL)
            tabs = []
            tabs.append([localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/RecruitmentAdSearch'),
             self.searchContainer,
             self,
             'search'])
            if session.corprole == 0 or util.IsNPC(session.corpid):
                self.applications = uicls.ApplicationsTab(name='myApplications', parent=self, ownerID=session.charid)
                tabs.append([localization.GetByLabel('UI/Corporations/CorpApplications/MyApplications'),
                 self.applications,
                 self,
                 'myApplications'])
            if not util.IsNPC(session.corpid) and HasAccess(session.corpid):
                text = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/CorporationAds')
                tabs.append([text,
                 self.corpAdvertContainer,
                 self,
                 'corp'])
            if not util.IsNPC(session.corpid) and HasAccess(session.corpid):
                self.corpApplications = uicls.ApplicationsTab(name='corpApplications', parent=self, ownerID=session.corpid)
                tabs.append([localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationsToCorp', corporationName=cfg.eveowners.Get(session.corpid).name),
                 self.corpApplications,
                 self,
                 'corpApplications'])
            tabGroup = uicls.TabGroup(name='tabparent', parent=self, idx=0)
            tabGroup.Startup(tabs, 'corporationrecruitment', UIIDPrefix='corporationRecruitmentTab')
            self.sr.tabs = tabGroup
        if args == 'corp':
            if not getattr(self, 'corpAdvertsInited', False):
                self.corpAdvertsInited = True
                self.ShowCorpAdverts()
            self.LoadAdverts()
        elif args == 'search':
            if not getattr(self, 'searchInited', False):
                self.searchInited = True
                self.searchContainer.PopulateSearch()
        elif args == 'myApplications':
            if not getattr(self, 'applicationsInited', False):
                self.applicationsInited = True
                self.applications.LoadApplications()
        elif args == 'corpApplications':
            if not getattr(self, 'corpApplicationsInited', False):
                self.corpApplicationsInited = True
                self.corpApplications.LoadApplications()
        sm.GetService('corpui').LoadTop('ui_7_64_8', localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/RecruitmentLabel'))

    def OnCorporationApplicationChanged(self, corpID, applicantID, applicationID, newApplication):
        if hasattr(self, 'applications') and self.applications and newApplication.characterID == session.charid:
            self.applications.OnCorporationApplicationChanged(corpID, applicantID, applicationID, newApplication)
        if hasattr(self, 'corpApplications') and self.corpApplications and newApplication.corporationID == session.corpid:
            self.corpApplications.OnCorporationApplicationChanged(corpID, applicantID, applicationID, newApplication)

    def GetCorpRecruitmentAds(self, *args):
        ads = self.corpSvc.GetRecruitmentAdsForCorporation()
        ownersToPrime = set()
        for ad in ads:
            if ad.corporationID:
                ownersToPrime.add(ad.corporationID)
            if ad.allianceID:
                ownersToPrime.add(ad.allianceID)

        if ownersToPrime:
            cfg.eveowners.Prime(list(ownersToPrime))
        return ads

    def ShowCorpAdverts(self, *args):
        self.corpAdvertContentContainer.Show()
        self.corpAdvertContentContainer.Flush()
        if HasAccess(session.corpid):
            sm.RegisterNotify(self)
            buttonContainer = uicls.Container(parent=self.corpAdvertContentContainer, name='buttonContainer', align=uiconst.TOBOTTOM, height=42, padding=const.defaultPadding)
            text = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/CreateRecruitmentAdButtonLabel')
            createAdBtn = uicls.Button(parent=buttonContainer, label=text, left=const.defaultPadding, func=self.CreateCorpAdvertClick, align=uiconst.TOPLEFT)
            text = localization.GetByLabel('UI/Corporations/Applications/EditWelcomeMail')
            welcomeMailBtn = uicls.Button(parent=buttonContainer, name='welcomeMailBtn', label=text, left=createAdBtn.left + createAdBtn.width + 10, func=self.OpenWelcomeMailWnd, align=uiconst.TOPLEFT, top=createAdBtn.top)
            corp = sm.GetService('corp').GetCorporation()
            checkboxCont = uicls.Container(parent=buttonContainer, name='checkboxCont', align=uiconst.TOLEFT, padding=(createAdBtn.left,
             20,
             const.defaultPadding,
             0), width=500)
            self.applicationsEnabled = uicls.Checkbox(text=localization.GetByLabel('UI/Corporations/CorpDetails/MembershipApplicationEnabled'), parent=checkboxCont, configName='applicationsEnabled', retval=None, checked=corp.isRecruiting, callback=self.OnCheckboxRecruitmentChange)
            checkboxCont.width = self.applicationsEnabled.sr.label.textwidth + 30
        self.corpAdvertsScroll = uicls.BasicDynamicScroll(parent=self.corpAdvertContentContainer, padding=const.defaultPadding)

    def OnCheckboxRecruitmentChange(self, cb, *args):
        corp = sm.GetService('corp').GetCorporation()
        appEnabled = cb.checked
        sm.GetService('corp').UpdateCorporation(description=corp.description, url=corp.url, taxRate=corp.taxRate, acceptApplications=appEnabled)

    def UpdateCreateButton(self):
        if HasAccess(session.corpid):
            btn = getattr(self, 'createButton', None)
            if btn is None:
                return
            if len(self.GetCorpRecruitmentAds()) >= const.corporationMaxRecruitmentAds:
                btn.Disable()
            else:
                btn.Enable()

    def OnCorporationChanged(self, corpID, change, *args):
        if 'isRecruiting' in change:
            cb = getattr(self, 'applicationsEnabled', None)
            if cb is None or cb.destroyed:
                return
            isChecked = change['isRecruiting'][1]
            cb.SetChecked(isChecked, report=0)

    def LoadAdverts(self):
        adverts = self.GetCorpRecruitmentAds()
        scrolllist = self.GetCorpAdvertScrollEntries(adverts)
        self.corpAdvertsScroll.Clear()
        self.corpAdvertsScroll.AddNodes(0, scrolllist)
        if len(adverts):
            self.corpAdvertsScroll.ShowHint(None)
        else:
            corpName = cfg.eveowners.Get(session.corpid).name
            hint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/CorpHasNoRecruitmentAdvertisements', corpName=corpName)
            self.corpAdvertsScroll.ShowHint(hint)

    def CreateCorpAdvertClick(self, clickObj):
        windowID = 'newCorpAd'
        wnd = uicls.CorpRecruitmentAdCreationAndEdit.GetIfOpen(windowID=windowID)
        if wnd:
            wnd.Maximize()
        else:
            caption = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/CreateNewAdvert')
            uicls.CorpRecruitmentAdCreationAndEdit(windowID=windowID, caption=caption)

    def OpenWelcomeMailWnd(self, *args):
        uicls.WelcomeMailWindow()

    def OnCorporationRecruitmentAdChanged(self):
        log.LogInfo('OnCorporationRecruitmentAdChanged')
        if self.destroyed or self.IsHidden():
            log.LogInfo('OnCorporationRecruitmentAdChanged self.destroyed')
            return
        if self.corpAdvertContainer.IsHidden():
            self.sr.tabs.BlinkPanelByName(localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/MyCorporationTab'))
        elif not self.IsHidden():
            self.LoadAdverts()
        self.UpdateCreateButton()

    def HasAccess(self, corporationID):
        if corporationID != session.corpid:
            return False
        if const.corpRolePersonnelManager & session.corprole != const.corpRolePersonnelManager:
            return False
        return True

    def GetCorpAdvertScrollEntries(self, adverts, *args):
        scrolllist = []
        if adverts:
            corpIDs = []
            for advert in adverts:
                corpIDs.append(advert.corporationID)

            corpIDs = list(set(corpIDs))
            cfg.eveowners.Prime(corpIDs)
            cfg.corptickernames.Prime(corpIDs)
            expandedAd = settings.char.ui.Get('corporation_recruitmentad_expanded', {})
            adGroups = sm.GetService('corp').GetCorpAdvertGroups()
            adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
            adTypesByGroupID = sm.GetService('corp').GetCorpAdvertTypesByGroupID()
            for advert in adverts:
                data = util.KeyVal()
                data.advert = advert
                data.corporationID = advert.corporationID
                data.allianceID = advert.allianceID
                data.channelID = advert.channelID
                data.editFunc = self.OpenEditWindow
                data.corpView = True
                data.standaloneMode = False
                data.advertGroups = adGroups
                data.advertTypesByGroupID = adTypesByGroupID
                data.advertTypesByTypeID = adTypesByTypeID
                data.adTitle = advert.title
                data.timeZoneMask1 = advert.hourMask1
                data.timeZoneMask2 = advert.hourMask2
                data.expandedView = expandedAd.get(data.corpView, None) == advert.adID
                if data.expandedView:
                    data.recruiters = self.corpSvc.GetRecruiters(advert.adID)
                data.memberCount = len(self.corpSvc.GetMemberIDs())
                scrolllist.append(listentry.Get('RecruitmentEntry', data=data))

        return scrolllist

    def CorpViewRecruitmentMenu(self, entry, *args):
        if self.destroyed:
            return
        m = []
        if entry.sr.node.advert:
            if util.IsCorporation(entry.sr.node.corporationID):
                m += [(uiutil.MenuLabel('UI/Common/Corporation'), sm.GetService('menu').GetMenuFormItemIDTypeID(entry.sr.node.corporationID, const.typeCorporation))]
            if util.IsAlliance(entry.sr.node.allianceID):
                m += [(uiutil.MenuLabel('UI/Common/Alliance'), sm.GetService('menu').GetMenuFormItemIDTypeID(entry.sr.node.allianceID, const.typeAlliance))]
            if m:
                m += [None]
            return m

    def OpenEditWindow(self, advertData, *args):
        windowID = 'advert_%s' % advertData.adID
        wnd = uicls.CorpRecruitmentAdCreationAndEdit.GetIfOpen(windowID=windowID)
        if wnd:
            wnd.Maximize()
        else:
            caption = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/EditAdvert', adTitle=advertData.title)
            uicls.CorpRecruitmentAdCreationAndEdit(windowID=windowID, advertData=advertData, caption=caption)


class CorpApplicationContainer(uicls.Container):
    __guid__ = 'form.CorpApplicationContainer'
    default_align = uiconst.TOLEFT_PROP
    default_width = 0.333333333

    def ApplyAttributes(self, attributes):
        super(form.CorpApplicationContainer, self).ApplyAttributes(attributes)
        uicls.Frame(parent=self)


class ContactContainer(uicls.Container):
    __guid__ = 'uicls.ContactContainer'

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.charID = None
        self.removeFunc = attributes.Get('removeFunc', None)
        self.addCallback = attributes.Get('addCallback', None)
        self.corpMembers = attributes.Get('corpMembers', [])
        self.iconContainer = uicls.Container(parent=self, align=uiconst.CENTERLEFT, pos=(const.defaultPadding,
         0,
         24,
         24))
        self.iconContainer.Hide()
        self.contactNameLabel = uicls.EveLabelMedium(parent=self, align=uiconst.CENTERLEFT)
        self.removeContactButton = uicls.Button(parent=self, align=uiconst.CENTERRIGHT, left=const.defaultPadding, hint=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AdRemove'), func=self.RemoveClick, color=util.Color.RED, iconSize=16, icon='ui_73_16_45')
        uicls.Fill(parent=self, color=(0, 0, 0, 0.5))
        uicls.Frame(parent=self, color=(1, 1, 1, 0.15), idx=0)
        self.Clear()

    def Clear(self):
        self.iconContainer.Flush()
        self.charID = None
        self.contactNameLabel.left = const.defaultPadding
        self.contactNameLabel.text = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NoRecruiterAssigned')
        self.removeContactButton.Hide()
        self.iconContainer.Hide()

    def Set(self, charID = None):
        self.iconContainer.Flush()
        if charID:
            self.charID = charID
            uiutil.GetOwnerLogo(self.iconContainer, charID, size=self.iconContainer.width, orderIfMissing=True)
            self.iconContainer.Show()
            self.contactNameLabel.left += self.iconContainer.width + const.defaultPadding
            self.contactNameLabel.SetText(cfg.eveowners.Get(charID).name)
            self.removeContactButton.Show()
            self.addCallback(self, charID)

    def IsSet(self):
        return self.charID

    def RemoveClick(self, *args):
        if self.removeFunc and self.charID:
            self.removeFunc(self.charID)

    def OnDropData(self, dragObj, *args):
        if not self.IsSet() and dragObj.__class__ == listentry.User:
            if dragObj.sr.node.itemID in self.corpMembers:
                self.Set(dragObj.sr.node.itemID)


class CorpRecruitmentContainerBase(uicls.Container):
    __guid__ = 'uicls.CorpRecruitmentContainerBase'

    def AddTimeZonePicker(self, parent, callback, startTimeZoneProportion, endTimeZoneProportion, header = None, minRange = 1 / 24.0, OnEndDragChange = None):
        adGroups = sm.GetService('corp').GetCorpAdvertGroups()
        if header is None:
            self.CreateLabel(parent, adGroups[TIMEZONE_GROUPID].groupName, adGroups[TIMEZONE_GROUPID].description, padTop=6)
        else:
            self.CreateLabel(parent, header, padTop=6)
        incrs = []
        year1800 = const.YEAR365 * 199L
        for i in xrange(24):
            if not i % 6:
                date = year1800 + i * HOUR
                text = util.FmtDate(date, fmt='ns')
                size = 5
            else:
                text = ''
                size = 2
            incrs.append((text, size, i))

        midnightHour = localization.GetByLabel('/Carbon/UI/Common/DateTimeQuantity/DateTimeShort2Elements', value1='24', value2='00')
        incrs.append((midnightHour, 5, 24))
        timeZoneSelector = uicls.RangeSelector(parent=parent, align=uiconst.TOTOP, OnIncrementChange=callback, fromProportion=startTimeZoneProportion, toProportion=endTimeZoneProportion, canInvert=True, padLeft=const.defaultPadding * 2, OnEndDragChange=OnEndDragChange)
        timeZoneSelector.SetIncrements(incrs)
        timeZoneSelector.SetMinRange(minRange=minRange)
        return timeZoneSelector

    def GetDefaultLanguage(self):
        sessionLang = session.languageID
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
        if sessionLang == 'DE':
            defaultAdType = adTypesByTypeID[GERMAN_TYPEID][0]
        elif sessionLang == 'RU':
            defaultAdType = adTypesByTypeID[RUSSIAN_TYPEID][0]
        elif sessionLang == 'JA':
            defaultAdType = adTypesByTypeID[JAPANESE_TYPEID][0]
        else:
            defaultAdType = adTypesByTypeID[ENGLISH_TYPEID][0]
        return defaultAdType

    def AddUtilMenu(self, parent, header, menuFunction):
        menuParent = uicls.Container(parent=parent, align=uiconst.TOTOP)
        utilMenu = uicls.UtilMenu(parent=menuParent, align=uiconst.CENTERLEFT, GetUtilMenu=menuFunction, texturePath='res:/UI/Texture/Icons/38_16_229.png', label=header)
        menuParent.height = utilMenu.height
        hintText = uicls.EveLabelSmall(parent=parent, align=uiconst.TOTOP, padBottom=8, padLeft=const.defaultPadding * 2, state=uiconst.UI_NORMAL)
        hintText.OnMouseDown = (self.OnHintTextClick, utilMenu)
        return (menuParent, hintText)

    def OnHintTextClick(self, utilMenu, *args):
        if utilMenu.IsExpanded():
            return
        uthread.new(utilMenu.ExpandMenu)

    def CreateLabel(self, parent, text, hint = '', padTop = 0, padLeft = None, align = None):
        if padLeft is None:
            padLeft = const.defaultPadding * 2
        label = uicls.EveLabelMedium(parent=parent, text=text, hint=hint, state=uiconst.UI_NORMAL, align=align or uiconst.TOTOP, bold=True, padTop=padTop, padLeft=padLeft)
        return label

    def GetAreasOfOperation(self, *args):
        adTypesByGroupID = sm.GetService('corp').GetCorpAdvertTypesByGroupID()
        return adTypesByGroupID[AREA_OF_OPERATIONS_GROUPID]


class CorpRecruitmentAdCreationAndEdit(uicls.Window):
    __guid__ = 'uicls.CorpRecruitmentAdCreationAndEdit'

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.corpSvc = sm.GetService('corp')
        self.SetTopparentHeight(0)
        self.SetMinSize([500, 500], 0)
        recruitmentCont = uicls.CorpRecruitmentContainerCreation(parent=self.sr.main, ownerWnd=self, advertData=attributes.advertData)


class CorpRecruitmentContainerCreation(CorpRecruitmentContainerBase):
    __guid__ = 'uicls.CorpRecruitmentContainerCreation'

    def ApplyAttributes(self, attributes):
        self.corpSvc = sm.GetService('corp')
        uicls.CorpRecruitmentContainerBase.ApplyAttributes(self, attributes)
        self.PopulateCorpAdvertsEdit(advertData=attributes.advertData)
        self.ownerWnd = attributes.ownerWnd

    def PopulateCorpAdvertsEdit(self, advertData = None):
        self.Flush()
        if advertData:
            advertID = advertData.adID
            recruiters = self.corpSvc.GetRecruiters(advertID)
            daysRemaining = max(0, int((advertData.expiryDateTime - blue.os.GetWallclockTime()) / DAY))
            self.adCreateMask = advertData.typeMask
            self.adLanguageMask = advertData.langMask
            adTitle = advertData.title
            if advertData.hourMask1 is None:
                self.adCreateTimeZone1 = (0, 1.0)
            else:
                timezone = GetTimeZoneFromMask(advertData.hourMask1)
                self.adCreateTimeZone1 = (timezone[0] / 24.0, timezone[1] / 24.0)
            if advertData.hourMask2 is None:
                self.adCreateTimeZone2 = (0, 1.0)
            else:
                timezone = GetTimeZoneFromMask(advertData.hourMask2)
                self.adCreateTimeZone2 = (timezone[0] / 24.0, timezone[1] / 24.0)
        else:
            advertID = None
            recruiters = []
            daysRemaining = 0
            self.adCreateMask = settings.char.ui.Get('corp_recruitment_lastCreateMask', 0)
            self.adLanguageMask = settings.char.ui.Get('corp_recruitment_lastCreateLanguageMask', 0)
            self.adCreateTimeZone1 = settings.char.ui.Get('corp_recruitment_lastCreateTimeZone1', (0.0, 1.0))
            self.adCreateTimeZone2 = settings.char.ui.Get('corp_recruitment_lastCreateTimeZone2', (0.0, 1.0))
        self.adCreateAdvertID = advertID
        sidePanel = uicls.Container(parent=self, name='sidePanel', align=uiconst.TORIGHT, width=230)
        buttons = [[localization.GetByLabel('UI/Common/Buttons/Submit'),
          self.UpdateAdvert,
          (advertID,),
          None], [localization.GetByLabel('UI/Common/Buttons/Cancel'),
          self.CancelCorpAdvert,
          (None,),
          None]]
        buttons = uicls.ButtonGroup(btns=buttons, parent=sidePanel)
        mainArea = uicls.Container(parent=self, name='mainArea', align=uiconst.TOALL, padding=const.defaultPadding)
        corpAdvertDetailsContainer = uicls.Container(parent=sidePanel, name='corpAdvertDetailsContainer', align=uiconst.TOALL, padding=(const.defaultPadding,
         0,
         const.defaultPadding * 3,
         0))
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
        if advertID is None:
            haveSubPlayStyle = False
            for combinedGroupID in PLAYSTYLE_GROUPS:
                if combinedGroupID not in COMBINED_GROUPS:
                    continue
                adTypeIDs = COMBINED_GROUPS[combinedGroupID].playstyleTypeIDs
                for adTypeID in adTypeIDs:
                    adType = adTypesByTypeID[adTypeID][0]
                    if adType.typeMask & self.adCreateMask:
                        haveSubPlayStyle = True
                        break

            if not haveSubPlayStyle:
                adTypeIDs = COMBINED_GROUPS[PVECOMBINED_ID].playstyleTypeIDs
                for adTypeID in adTypeIDs:
                    adType = adTypesByTypeID[adTypeID][0]
                    self.adCreateMask = AddBitToMask(bit=adType.typeMask, mask=self.adCreateMask)

        adGroups = sm.GetService('corp').GetCorpAdvertGroups()
        playStyleMenu, playStyleHintText = self.AddUtilMenu(corpAdvertDetailsContainer, adGroups[PLAYSTYLE_GROUPID].groupName, self.GetAdCreatePlayStyleMenu)
        playStyleMenu.padTop = const.defaultPadding
        self.adCreate_playStyleHintText = playStyleHintText
        self.UpdateAdCreatePlayStyleHintText()
        if advertID is None:
            typeIDs = [ each.typeID for each in sm.GetService('corp').GetCorpAdvertTypesByGroupID()[AREA_OF_OPERATIONS_GROUPID] ]
            for adTypeID in typeIDs:
                adType = adTypesByTypeID[adTypeID][0]
                self.adCreateMask = AddBitToMask(bit=adType.typeMask, mask=self.adCreateMask)

        areaOfOperationMenu, areaOfOperationHint = self.AddUtilMenu(corpAdvertDetailsContainer, adGroups[AREA_OF_OPERATIONS_GROUPID].groupName, self.GetAdCreateAreaOfOperationsOptions)
        self.adCreate_areaOfOperationHint = areaOfOperationHint
        self.UpdateAdCreateAreaOfOperationHint()
        hasLanguage = False
        adTypesByGroupID = sm.GetService('corp').GetCorpAdvertTypesByGroupID()
        for adType in adTypesByGroupID[corputil.RECRUITMENT_GROUP_PRIMARY_LANGUAGE]:
            if adType.typeMask & self.adLanguageMask:
                hasLanguage = True
                break

        if not hasLanguage:
            adType = self.GetDefaultLanguage()
            self.adLanguageMask = AddBitToMask(bit=adType.typeMask, mask=self.adLanguageMask)
        languageMenu, languageHint = self.AddUtilMenu(corpAdvertDetailsContainer, adGroups[corputil.RECRUITMENT_GROUP_PRIMARY_LANGUAGE].groupName, self.GetAdCreateLanguageOptions)
        self.adCreate_languageHint = languageHint
        self.UpdateAdCreateLanguageHint()
        headerText = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/PrimaryTimeZone')
        self.AddTimeZonePicker(parent=corpAdvertDetailsContainer, callback=self.OnAdCreateTimezoneRangeChange, startTimeZoneProportion=self.adCreateTimeZone1[0], endTimeZoneProportion=self.adCreateTimeZone1[1], header=headerText)
        pad = uicls.Container(parent=corpAdvertDetailsContainer, align=uiconst.TOTOP, height=const.defaultPadding)
        headerText = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/SecondaryTimeZone')
        self.AddTimeZonePicker(parent=corpAdvertDetailsContainer, callback=self.OnAdCreateTimezone2RangeChange, startTimeZoneProportion=self.adCreateTimeZone2[0], endTimeZoneProportion=self.adCreateTimeZone2[1], header=headerText, minRange=0.0)
        pad = uicls.Container(parent=corpAdvertDetailsContainer, align=uiconst.TOTOP, height=const.defaultPadding)
        maxDurExtension = const.corporationMaxRecruitmentAdDuration - daysRemaining
        if maxDurExtension > 0:
            if not advertID:
                durationHeader = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/RecruitmentAdDuration')
            else:
                durationHeader = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/ExtendRecruitmentAdDuration')
            self.CreateLabel(corpAdvertDetailsContainer, durationHeader, padTop=const.defaultPadding)
            incrs = []
            tickTextAdded = False
            i = 0
            for i in xrange(maxDurExtension + 1):
                if i % 7:
                    incrs.append(('', 2, i))
                else:
                    incrs.append((str(i), 6, i))
                    if i > 0:
                        tickTextAdded = True

            if not tickTextAdded and i > 0:
                lastTuple = incrs[-1]
                newTuple = (str(i), lastTuple[1], lastTuple[2])
                incrs[-1] = newTuple
            defaultDuration = 1
            stepSize = 1.0 / (len(incrs) - 1)
            toProportion = stepSize * defaultDuration
            durationSelector = uicls.RangeSelector(parent=corpAdvertDetailsContainer, align=uiconst.TOTOP, OnIncrementChange=self.OnDurationChange, fromProportion=0.0, toProportion=toProportion, canInvert=False, padLeft=const.defaultPadding * 2)
            durationSelector.SetIncrements(incrs)
            durationSelector.SetFixedRange(fixedFromProportion=0.0)
            if advertID:
                durationSelector.SetMinRange(minRange=0.0)
            else:
                durationSelector.SetMinRange(minRange=stepSize)
            self.adCreateDurationHint = uicls.EveLabelSmall(parent=corpAdvertDetailsContainer, align=uiconst.TOTOP, padBottom=8, padLeft=const.defaultPadding * 2, state=uiconst.UI_NORMAL)
            self.UpdateDurationHint(defaultDuration)
        else:
            self.adCreateDuration = 0
        self.corpMembers = self.corpSvc.GetMemberIDs()
        self.contactsList = []
        recruitmentContainer = uicls.Container(parent=sidePanel, name='recruitmentContainer', align=uiconst.TOALL, padding=const.defaultPadding)
        self.contactsFilter = uicls.SinglelineEdit(parent=recruitmentContainer, name='contactsFilter', align=uiconst.TOTOP, maxLength=10, OnInsert=self.FilterOnInsert, hinttext=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/FilterRecruiterCandidates'), padBottom=const.defaultPadding)
        self.corpMemberPickerScroll = uicls.Scroll(parent=recruitmentContainer, align=uiconst.TOALL)
        buttonContainer = uicls.Container(parent=recruitmentContainer, name='buttonContainer', align=uiconst.TOBOTTOM, idx=0)
        advertAddContactButton = uicls.Button(parent=buttonContainer, name='advertAddContactButton', align=uiconst.CENTER, func=self.AddContactClick, label=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AddRecruiterToAd'))
        buttonContainer.height = advertAddContactButton.height + 8
        self.contactContainers = {}
        for i in xrange(0, 6):
            self.contactContainers[i] = uicls.ContactContainer(parent=recruitmentContainer, align=uiconst.TOBOTTOM, height=32, padTop=2, removeFunc=self.RemoveContact, addCallback=self.AddContactCallback, state=uiconst.UI_NORMAL, corpMembers=self.corpMembers, idx=0)

        channelParent = uicls.Container(parent=recruitmentContainer, name='channelParent', align=uiconst.TOBOTTOM, padTop=const.defaultPadding, padBottom=const.defaultPadding, idx=0)
        channelOptions = [(localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NoneRecruitmentChannelSelection'), 0)]
        selected = None
        lsc = sm.GetService('LSC')
        for channel in lsc.GetChannels():
            if channel.channelID and type(channel.channelID) is int and (channel.channelID < 0 or channel.channelID > 2100000000) and lsc.IsOperator(channel.channelID, session.charid):
                channelOptions.append((channel.displayName, channel.channelID))

        advertChannelLabel = uicls.EveLabelMedium(parent=channelParent, name='advertChannelLabel', align=uiconst.CENTERLEFT, text=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/RecruitmentChannelHeader'))
        if advertData:
            selected = advertData.channelID
        self.advertChannelCombo = uicls.Combo(parent=channelParent, options=channelOptions, name='advertChannelCombo', select=selected, adjustWidth=True, align=uiconst.CENTERLEFT, left=advertChannelLabel.width + const.defaultPadding)
        channelParent.height = max(self.advertChannelCombo.height, advertChannelLabel.height + 6)
        self.advertChannelCombo.width = min(self.advertChannelCombo.width, sidePanel.width - self.advertChannelCombo.left - 10)
        cfg.eveowners.Prime(self.corpMembers)
        scrollList = []
        for member in self.corpMembers:
            data = util.KeyVal()
            data.charID = member
            data.OnDblClick = self.OnContactDoubleClick
            scrollList.append((cfg.eveowners.Get(member).name, listentry.Get('User', data=data)))

        scrollList = uiutil.SortListOfTuples(scrollList)
        self.corpMemberPickerScroll.Load(contentList=scrollList)
        for contact in recruiters:
            self.AddContact(contact)

        self.CreateLabel(mainArea, localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AdEditTitle'), padTop=6, padLeft=0)
        self.corpTitleEdit = uicls.SinglelineEdit(parent=mainArea, name='corpTitleEdit', align=uiconst.TOTOP, maxLength=const.corporationRecMaxTitleLength)
        if advertData:
            self.corpTitleEdit.SetValue(adTitle)
        self.CreateLabel(mainArea, text=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AdEditMessage'), padTop=6, padLeft=0)
        self.corpMessageEdit = uicls.EditPlainText(parent=mainArea, align=uiconst.TOALL, name='corpMessageEdit', maxLength=const.corporationRecMaxMessageLength)
        if advertData:
            self.corpMessageEdit.SetValue(advertData.description)
        tabs = [[localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AdEditDetails'),
          corpAdvertDetailsContainer,
          self,
          'details'], [localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AdRecruiters'),
          recruitmentContainer,
          self,
          'recruiters']]
        tabGroup = uicls.TabGroup(name='corpAdEditTabGroup', parent=sidePanel, align=uiconst.TOTOP, padTop=const.defaultPadding * 2, idx=0)
        tabGroup.Startup(tabs)

    def TogglePlayStyleGroup(self, playStyleGroupID):
        mask = self.adCreateMask
        allChecked = True
        adTypeIDs = COMBINED_GROUPS[playStyleGroupID].playstyleTypeIDs
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
        for adTypeID in adTypeIDs:
            adType = adTypesByTypeID[adTypeID][0]
            if not adType.typeMask & mask:
                allChecked = False
                break

        for adTypeID in adTypeIDs:
            adType = adTypesByTypeID[adTypeID][0]
            if allChecked:
                mask = RemoveBitFromMask(bit=adType.typeMask, mask=mask)
            else:
                mask = AddBitToMask(bit=adType.typeMask, mask=mask)

        self.adCreateMask = mask
        self.UpdateAdCreatePlayStyleHintText()

    def OnAdCreatePlayStyleChange(self, adType, checked, *args):
        mask = self.adCreateMask
        if checked:
            mask = AddBitToMask(bit=adType.typeMask, mask=mask)
        else:
            mask = RemoveBitFromMask(bit=adType.typeMask, mask=mask)
        self.adCreateMask = mask
        self.UpdateAdCreatePlayStyleHintText()

    def UpdateAdCreatePlayStyleHintText(self):
        mask = self.adCreateMask
        hint = ''
        counter = 0
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
        for combinedGroupID in PLAYSTYLE_GROUPS:
            groupName = localization.GetByLabel(COMBINED_GROUPS[combinedGroupID].combinedNamePath)
            adTypeIDs = COMBINED_GROUPS[combinedGroupID].playstyleTypeIDs
            for adTypeID in adTypeIDs:
                adType = adTypesByTypeID[adTypeID][0]
                if adType.typeMask & mask:
                    counter += 1

        if counter > 0:
            hint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NumFiltersSelected', num=counter)
        else:
            hint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NoFiltersSelected')
        self.adCreate_playStyleHintText.text = hint

    def GetAdCreateAreaOfOperationsOptions(self, menuParent):
        mask = self.adCreateMask
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
        typeIDs = [ each.typeID for each in sm.GetService('corp').GetCorpAdvertTypesByGroupID()[AREA_OF_OPERATIONS_GROUPID] ]
        for adTypeID in typeIDs:
            adType = adTypesByTypeID[adTypeID][0]
            checked = adType.typeMask & mask
            typeName = adType.typeName
            menuParent.AddCheckBox(text=typeName, checked=checked, callback=(self.OnAdCreateAreaOfOperationChange, adType, not checked))

    def OnAdCreateAreaOfOperationChange(self, adType, checked):
        mask = self.adCreateMask
        if checked:
            mask = AddBitToMask(bit=adType.typeMask, mask=mask)
        else:
            mask = RemoveBitFromMask(bit=adType.typeMask, mask=mask)
        self.adCreateMask = mask
        self.UpdateAdCreateAreaOfOperationHint()

    def UpdateAdCreateAreaOfOperationHint(self):
        mask = self.adCreateMask
        hint = ''
        counter = 0
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
        typeIDs = [ each.typeID for each in sm.GetService('corp').GetCorpAdvertTypesByGroupID()[AREA_OF_OPERATIONS_GROUPID] ]
        for adTypeID in typeIDs:
            adType = adTypesByTypeID[adTypeID][0]
            if adType.typeMask & mask:
                counter += 1

        if counter > 0:
            hint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NumFiltersSelected', num=counter)
        else:
            hint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NoFiltersSelected')
        self.adCreate_areaOfOperationHint.text = hint

    def GetAdCreateLanguageOptions(self, menuParent):
        mask = self.adLanguageMask
        adTypesByGroupID = sm.GetService('corp').GetCorpAdvertTypesByGroupID()
        for adType in adTypesByGroupID[corputil.RECRUITMENT_GROUP_PRIMARY_LANGUAGE]:
            checked = adType.typeMask & mask
            menuParent.AddCheckBox(text=adType.typeName, checked=checked, callback=(self.OnAdCreateLanguageChange, adType, not checked))

    def OnAdCreateLanguageChange(self, adType, checked):
        mask = self.adLanguageMask
        if checked:
            mask = AddBitToMask(bit=adType.typeMask, mask=mask)
        else:
            mask = RemoveBitFromMask(bit=adType.typeMask, mask=mask)
        self.adLanguageMask = mask
        self.UpdateAdCreateLanguageHint()

    def UpdateAdCreateLanguageHint(self):
        mask = self.adLanguageMask
        hint = ''
        counter = 0
        adTypesByGroupID = sm.GetService('corp').GetCorpAdvertTypesByGroupID()
        for adType in adTypesByGroupID[corputil.RECRUITMENT_GROUP_PRIMARY_LANGUAGE]:
            if adType.typeMask & mask:
                counter += 1

        if counter > 0:
            hint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NumFiltersSelected', num=counter)
        else:
            hint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NoFiltersSelected')
        self.adCreate_languageHint.text = hint

    def OnAdCreateTimezone2RangeChange(self, rangeSelector, fromData, toData, fromProportion, toProportion):
        self.adCreateTimeZone2 = (fromProportion, toProportion)

    def OnDurationChange(self, rangeSelector, fromData, toData, *args):
        duration = max(0, toData[-1])
        self.UpdateDurationHint(duration)

    def UpdateDurationHint(self, duration):
        self.adCreateDuration = duration
        durationHint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/RecruitmentAdDurationOptionWithPrice', adDuration=duration * DAY, adPrice=contractutils.FmtISKWithDescription(self.AdvertPrice(duration), justDesc=True))
        self.adCreateDurationHint.text = durationHint

    def AdvertPrice(self, days):
        amount = days * const.corporationAdvertisementDailyRate
        if not self.adCreateAdvertID:
            amount += const.corporationAdvertisementFlatFee
        return amount

    def FilterOnInsert(self, *args):
        scrollList = []
        for member in self.corpMembers:
            if member not in self.contactsList and self.contactsFilter.GetValue().lower() in cfg.eveowners.Get(member).name.lower():
                data = util.KeyVal()
                data.charID = member
                data.OnDblClick = self.OnContactDoubleClick
                entry = listentry.Get('User', data=data)
                scrollList.append(entry)

        self.corpMemberPickerScroll.Load(contentList=scrollList)

    def AddContactClick(self, *args):
        selected = self.corpMemberPickerScroll.GetSelected()
        if len(selected) and len(self.contactsList) < 6:
            for item in selected:
                self.AddContact(item.itemID)

    def OnContactDoubleClick(self, entry, *args):
        self.AddContact(entry.sr.node.itemID)

    def AddContact(self, charID):
        for container in self.contactContainers.values():
            if not container.IsSet():
                container.Set(charID)
                break

    def AddContactCallback(self, callbackObj, charID):
        if charID in self.contactsList:
            callbackObj.Clear()
        else:
            self.contactsList.append(charID)
            self.FilterOnInsert()

    def RemoveContact(self, charID):
        for container in self.contactContainers.values():
            if container.IsSet() == charID:
                container.Clear()
                self.contactsList.remove(charID)
                self.FilterOnInsert()

    def OnHintTextClick(self, utilMenu, *args):
        if utilMenu.IsExpanded():
            return
        uthread.new(utilMenu.ExpandMenu)

    def RegisterDuration(self, checkbox):
        checkboxVal = checkbox.data['value']
        self.adCreateDuration = checkboxVal

    def UpdateAdvert(self, advertID = None):
        title = self.corpTitleEdit.GetValue().strip()
        if not title:
            raise UserError('CustomInfo', {'info': localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/EnterTitleForAd')})
        description = self.corpMessageEdit.GetValue()
        channel = self.advertChannelCombo.GetValue()
        recruiters = self.contactsList
        days = self.adCreateDuration
        typeMask = self.adCreateMask
        languageMask = self.adLanguageMask
        f, t = self.adCreateTimeZone1
        f2, t2 = self.adCreateTimeZone2
        timeZoneMask1 = BuildMask(f * 24, t * 24)
        timeZoneMask2 = BuildMask(f2 * 24, t2 * 24)
        if advertID:
            self.corpSvc.UpdateRecruitmentAd(advertID, typeMask, languageMask, description, channel, recruiters, title, days, timeZoneMask1, timeZoneMask2)
        else:
            settings.char.ui.Set('corp_recruitment_lastCreateMask', typeMask)
            settings.char.ui.Set('corp_recruitment_lastCreateLanguageMask', languageMask)
            self.corpSvc.CreateRecruitmentAd(days, typeMask, languageMask, description, channel, recruiters, title, timeZoneMask1, timeZoneMask2)
        self.CloseAdWindow()

    def OnAdCreateTimezoneRangeChange(self, rangeSelector, fromData, toData, fromProportion, toProportion):
        self.adCreateTimeZone1 = (fromProportion, toProportion)

    def CancelCorpAdvert(self, *args):
        self.CloseAdWindow()

    def CloseAdWindow(self, *args):
        if self.ownerWnd and not self.ownerWnd.destroyed:
            self.ownerWnd.Close()

    def GetAdCreatePlayStyleMenu(self, menuParent):
        mask = self.adCreateMask
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
        for combinedGroupID in PLAYSTYLE_GROUPS:
            groupName = localization.GetByLabel(COMBINED_GROUPS[combinedGroupID].combinedNamePath)
            adTypeIDs = COMBINED_GROUPS[combinedGroupID].playstyleTypeIDs
            headerChecked = True
            for adTypeID in adTypeIDs:
                adType = adTypesByTypeID[adTypeID][0]
                checked = adType.typeMask & mask
                if not checked:
                    headerChecked = False
                    break

            if headerChecked:
                icon = CHECKBOX_ACTIVE_ICON
            else:
                icon = CHECKBOX_INACTIVE_ICON
            menuParent.AddHeader(text=groupName, callback=(self.TogglePlayStyleGroup, combinedGroupID), icon=icon)
            menuParent.AddSpace()
            for adTypeID in adTypeIDs:
                adType = adTypesByTypeID[adTypeID][0]
                checked = bool(adType.typeMask & mask)
                menuParent.AddCheckBox(text=adType.typeName, checked=checked, callback=(self.OnAdCreatePlayStyleChange, adType, not checked), indentation=10)

            menuParent.AddSpace()


class CorpRecruitmentContainerSearch(CorpRecruitmentContainerBase):
    __guid__ = 'uicls.CorpRecruitmentContainerSearch'

    def ApplyAttributes(self, attributes):
        self.corpSvc = sm.GetService('corp')
        self.localTimeZoneDiff = time.gmtime().tm_hour - time.localtime().tm_hour
        uicls.CorpRecruitmentContainerBase.ApplyAttributes(self, attributes)

    def PopulateSearch(self):
        self.searchMask = settings.char.ui.Get('corporation_recruitment_types', 0)
        explanationCont = uicls.ContainerAutoSize(parent=self, name='explanationCont', size=100, align=uiconst.TOTOP)
        advertChannelLabel = uicls.EveLabelMedium(parent=explanationCont, name='advertChannelLabel', align=uiconst.TOTOP, text=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/SearchExplanation'), padding=(10, 6, 6, 10))
        corpSearchOptionsLeftContainer = uicls.Container(parent=self, name='corpSearchOptionsLeftContainer', align=uiconst.TOLEFT, padding=const.defaultPadding, width=200)
        searchCorpID = settings.char.ui.Get('corpRecruitmentSearchCorpID', None)
        if searchCorpID is not None:
            try:
                searchTerm = cfg.eveowners.Get(searchCorpID).name
            except KeyError:
                searchTerm = ''

        else:
            searchTerm = ''
        self.searchField = uicls.QuickFilterEdit(parent=corpSearchOptionsLeftContainer, align=uiconst.TOTOP, left=const.defaultPadding, setvalue=searchTerm, padBottom=10, padLeft=8, hinttext=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/SearchForCorporation'), OnClearFilter=self.OnSearchFieldChanged)
        self.searchField.ReloadFunction = self.OnSearchFieldChanged
        self.searchField.OnReturn = self.SearchByCorpName
        corpSearchOptionsContainer = uicls.Container(parent=corpSearchOptionsLeftContainer, name='corpSearchOptionsContainer', align=uiconst.TOALL)
        self.corpSearchOptionsContainer = corpSearchOptionsContainer
        filterStates = self.GetFilterStates()
        haveSubPlayStyle = False
        for combinedGroupID in PLAYSTYLE_GROUPS:
            adTypeIDs = COMBINED_GROUPS[combinedGroupID].playstyleTypeIDs
            for adTypeID in adTypeIDs:
                if adTypeID in filterStates:
                    haveSubPlayStyle = True
                    break

        if not haveSubPlayStyle:
            defaultAdTypeIDs = COMBINED_GROUPS[PVECOMBINED_ID].playstyleTypeIDs
            for combinedGroupID in PLAYSTYLE_GROUPS:
                adTypeIDs = COMBINED_GROUPS[combinedGroupID].playstyleTypeIDs
                for adTypeID in adTypeIDs:
                    if adTypeID in defaultAdTypeIDs:
                        filterStates[adTypeID] = FILTERSTATE_WANT

            filterStates[NEWPILOTFRIENTLY_TYPEID] = FILTERSTATE_WANT
        self.SetFilterStates(filterStates)
        adGroups = sm.GetService('corp').GetCorpAdvertGroups()
        playStyleMenu, playStyleHint = self.AddUtilMenu(corpSearchOptionsContainer, adGroups[PLAYSTYLE_GROUPID].groupName, self.GetSearchPlayStyleMenu)
        self.searchPlayStyleHint = playStyleHint
        hasAreaOfOperation = False
        typeIDs = [ each.typeID for each in sm.GetService('corp').GetCorpAdvertTypesByGroupID()[AREA_OF_OPERATIONS_GROUPID] ]
        for adTypeID in typeIDs:
            if adTypeID in filterStates:
                hasAreaOfOperation = True
                break

        if not hasAreaOfOperation:
            secClass = sm.GetService('map').GetSecurityClass(session.solarsystemid)
            key = HIGHSEC_TYPEID
            if secClass == const.securityClassZeroSec:
                if util.IsWormholeRegion(session.regionid):
                    key = WORMHOLESPACE_TYPEID
                else:
                    key = NULLSEC_TYPEID
            elif secClass == const.securityClassLowSec:
                key = LOWSEC_TYPEID
            filterStates[key] = FILTERSTATE_WANT
        areaOfOperationMenu, areaOfOperationHint = self.AddUtilMenu(corpSearchOptionsContainer, adGroups[AREA_OF_OPERATIONS_GROUPID].groupName, (self.GetSearchFilterOptions, typeIDs, 'areaOfOperations'))
        self.searchAreaOfOperationHint = areaOfOperationHint
        adTypesByGroupID = sm.GetService('corp').GetCorpAdvertTypesByGroupID()
        languageAdTypes = adTypesByGroupID.get(corputil.RECRUITMENT_GROUP_PRIMARY_LANGUAGE, None)
        filterStateLanguages = self.GetFilterStatesLanguages()
        if languageAdTypes:
            hasLanguage = False
            adTypeIDs = []
            for adType in languageAdTypes:
                adTypeIDs.append(adType.typeID)
                if adType.typeID in filterStateLanguages:
                    hasLanguage = True

            if not hasLanguage:
                defaultAdType = self.GetDefaultLanguage()
                filterStateLanguages[defaultAdType.typeID] = FILTERSTATE_WANT
                self.SetFilterStatesLanguages(filterStateLanguages)
            languageMenu, languageHint = self.AddUtilMenu(corpSearchOptionsContainer, adGroups[corputil.RECRUITMENT_GROUP_PRIMARY_LANGUAGE].groupName, (self.GetSearchFilterOptions, adTypeIDs, 'language'))
            self.searchLanguageHint = languageHint
        self.UpdateSearchFilterHints()
        startTimeZoneProportion, endTimeZoneProportion = settings.char.ui.Get('corp_recruitment_searchTimeZoneRange', (None, None))
        if startTimeZoneProportion is None and endTimeZoneProportion is None:
            currentTime = time.gmtime().tm_hour
            startTime = currentTime - 3
            endTime = currentTime + 3
            if startTime < 0:
                startTime = 24 + startTime
            if endTime > 23:
                endTime = endTime - 24
            startTimeZoneProportion = startTime / 24.0
            endTimeZoneProportion = endTime / 24.0
            settings.char.ui.Set('corp_recruitment_searchTimeZoneRange', (startTimeZoneProportion, endTimeZoneProportion))
        headerText = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/Playtime')
        rangeSelector = self.AddTimeZonePicker(parent=corpSearchOptionsContainer, callback=self.OnSearchTimezoneIncrementChange, OnEndDragChange=self.OnSearchTimezoneRangeChange, startTimeZoneProportion=startTimeZoneProportion, endTimeZoneProportion=endTimeZoneProportion, header=headerText)
        self.searchTimeZoneHint = uicls.EveLabelSmall(parent=corpSearchOptionsContainer, name='searchTimeZoneHint', align=uiconst.TOTOP, padBottom=8, padTop=4, padLeft=const.defaultPadding * 2)
        self.UpdateSearchTimeZoneHint(rangeSelector, int(startTimeZoneProportion * 24), int(endTimeZoneProportion * 24))
        self._corpSizeLabel = self.CreateLabel(corpSearchOptionsContainer, localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/CorporationSize'), padTop=16)
        sizeRange = [0,
         10,
         50,
         100,
         200,
         500,
         1000]
        step = 1.0 / len(sizeRange)
        incrs = [ (str(i), 5, i) for i in sizeRange ]
        maxCorpSize = 6300
        incrs.append(('res:/UI/Texture/classes/RangeSelector/infinity.png', 5, maxCorpSize))
        minMembers = settings.char.ui.Get('corporation_recruitment_minmembers', 0)
        if minMembers in sizeRange:
            fromProportion = sizeRange.index(minMembers) * step
        else:
            fromProportion = 0.0
        maxMembers = settings.char.ui.Get('corporation_recruitment_maxmembers', 6300)
        if maxMembers in sizeRange:
            toProportion = sizeRange.index(maxMembers) * step
        else:
            toProportion = 1.0
        corpSize = uicls.RangeSelector(parent=corpSearchOptionsContainer, align=uiconst.TOTOP, fromProportion=fromProportion, toProportion=toProportion, OnIncrementChange=self.OnCorporationSizeIncrementChange, OnEndDragChange=self.OnCorporationSizeRangeChange, padLeft=const.defaultPadding * 2)
        corpSize.SetIncrements(incrs)
        corpSize.SetMinRange(minRange=step)
        corpSize._DoOnChangeCallback()
        excludeAlliancesChecked = settings.char.ui.Get('corporation_recruitment_excludeAlliancesChecked', False)
        self.inAllianceCheckbox = uicls.Checkbox(text=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AllianceCheckboxText'), parent=corpSearchOptionsContainer, configName='allianceCheckbox', checked=excludeAlliancesChecked, align=uiconst.TOTOP, callback=self.OnAllianceCheckboxChange, padLeft=6, padTop=10)
        self.corpSearchResultsScroll = uicls.BasicDynamicScroll(parent=self, padding=const.defaultPadding)
        self._searchReady = True
        self.loadingWheel = uicls.LoadingWheel(parent=self.corpSearchResultsScroll, align=uiconst.CENTER)
        self.loadingWheel.display = False
        if searchCorpID and searchTerm != '':
            self.PopulateSearchResultsByCorpID(searchCorpID)
        else:
            self.SearchAdverts()

    def OnSearchFieldChanged(self, *args):
        if self.searchField.GetValue().strip() == '':
            self.EnableSearchOptions()
            self.corpSearchResultsScroll.RemoveNodes(self.corpSearchResultsScroll.GetNodes())
            self.DelayedSearchAdverts()
            settings.char.ui.Set('corpRecruitmentSearchCorpID', None)

    def SearchByCorpName(self, *args):
        searchText = self.searchField.GetValue().strip()
        if searchText.strip() == '':
            self.EnableSearchOptions()
            return
        corpID = uix.Search(searchText.lower(), const.groupCorporation, None, hideNPC=1, exact=const.searchByPartialTerms, searchWndName='corpRecruitment')
        if corpID is None:
            self.searchField.SetValue('')
            settings.char.ui.Set('corpRecruitmentSearchCorpID', None)
            return
        self.PopulateSearchResultsByCorpID(corpID)

    def PopulateSearchResultsByCorpID(self, corpID, *args):
        corpName = cfg.eveowners.Get(corpID).name
        self.searchField.SetValue(corpName)
        settings.char.ui.Set('corpRecruitmentSearchCorpID', corpID)
        self.DisableSearchOptions()
        ads = sm.GetService('corp').GetRecruitmentAdsForCorpID(corpID)
        newAds = [ (None, ad) for ad in ads ]
        entries = self.MakeRecruitmentEntriesFromAdList(newAds, None, None, {})
        self.corpSearchResultsScroll.Clear()
        if entries:
            self.corpSearchResultsScroll.AddNodes(-1, entries, updateScroll=True)
            hint = ''
        else:
            hint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NoAdsFound')
        self.corpSearchResultsScroll.ShowHint(hint)

    def MakeRecruitmentEntriesFromAdList(self, adList, wantMask, wantLanguageMask, expandedAd):
        allData = sm.GetService('corp').GetRecruitementEntryDataList(adList, wantMask, wantLanguageMask, expandedAd)
        entries = []
        now = blue.os.GetWallclockTime()
        for data in allData:
            if data.advert.expiryDateTime < now:
                continue
            entry = listentry.Get('RecruitmentEntry', data=data)
            entries.append(entry)

        return entries

    def EnableSearchOptions(self, *args):
        self.corpSearchOptionsContainer.Enable()
        self.corpSearchOptionsContainer.opacity = 1.0

    def DisableSearchOptions(self, *args):
        self.corpSearchOptionsContainer.Disable()
        self.corpSearchOptionsContainer.opacity = 0.3

    def GetSearchPlayStyleMenu(self, menuParent):
        for combinedGroupID in PLAYSTYLE_GROUPS:
            groupName = localization.GetByLabel(COMBINED_GROUPS[combinedGroupID].combinedNamePath)
            adTypeIDs = COMBINED_GROUPS[combinedGroupID].playstyleTypeIDs
            self.GetSearchFilterOptions(menuParent, adTypeIDs, 'playStyle', header=groupName)
            menuParent.AddSpace()

    def GetSearchFilterOptions(self, menuParent, adTypeIDs, configName, header = None):
        if configName == 'language':
            callback = self.ToggleSearchFilterStateLanguage
            filterStates = self.GetFilterStatesLanguages()
        else:
            callback = self.ToggleSearchFilterState
            filterStates = self.GetFilterStates()
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
        if header:
            headerChecked = True
            for adTypeID in adTypeIDs:
                adType = adTypesByTypeID[adTypeID][0]
                filterState = filterStates.get(adTypeID, False)
                if filterState != FILTERSTATE_WANT:
                    headerChecked = False
                    break

            if headerChecked:
                icon = CHECKBOX_ACTIVE_ICON
            else:
                icon = CHECKBOX_INACTIVE_ICON
            menuParent.AddHeader(text=header, callback=(self.ToggleSearchFilterStateOnGroup, adTypeIDs), icon=icon)
        for adTypeID in adTypeIDs:
            adType = adTypesByTypeID[adTypeID][0]
            filterState = filterStates.get(adTypeID, False)
            if filterState == FILTERSTATE_WANT:
                icon = CHECKBOX_ACTIVE_ICON
            else:
                icon = CHECKBOX_INACTIVE_ICON
            menuParent.AddCheckBox(text=adType.typeName, checked=filterState, icon=icon, callback=(callback, adType, filterState), indentation=10)

    def ToggleSearchFilterStateOnGroup(self, adTypeIDs):
        filterStates = self.GetFilterStates()
        all = {}
        currentGroupState = True
        for adTypeID in adTypeIDs:
            filterState = filterStates.get(adTypeID, False)
            if filterState != FILTERSTATE_WANT:
                currentGroupState = False
                break

        if currentGroupState:
            newGroupState = False
        else:
            newGroupState = FILTERSTATE_WANT
        for adTypeID in adTypeIDs:
            filterStates[adTypeID] = newGroupState

        self.SetFilterStates(filterStates)
        self.DelayedSearchAdverts()
        self.UpdateSearchFilterHints()

    def UpdateSearchFilterHints(self):
        adTypesByGroupID = sm.GetService('corp').GetCorpAdvertTypesByGroupID()
        typeIDs = [ each.typeID for each in adTypesByGroupID[PLAYSTYLE_GROUPID] ]
        text, hint = self.GetSearchFilterHintTextForTypeIDs(typeIDs, 'playStyle')
        self.searchPlayStyleHint.text = text
        self.searchPlayStyleHint.hint = hint
        typeIDs = [ each.typeID for each in adTypesByGroupID[AREA_OF_OPERATIONS_GROUPID] ]
        text, hint = self.GetSearchFilterHintTextForTypeIDs(typeIDs, 'areaOfOperations')
        self.searchAreaOfOperationHint.text = text
        self.searchAreaOfOperationHint.hint = hint
        typeIDs = [ each.typeID for each in adTypesByGroupID[LANGUAGE_GROUPID] ]
        text, hint = self.GetSearchFilterHintTextForTypeIDs(typeIDs, 'language')
        self.searchLanguageHint.text = text
        self.searchLanguageHint.hint = hint

    def GetSearchFilterHintTextForTypeIDs(self, adTypeIDs, configName):
        hint = []
        if configName == 'language':
            filterStates = self.GetFilterStatesLanguages()
        else:
            filterStates = self.GetFilterStates()
        wantCounter = 0
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
        for adTypeID in adTypeIDs:
            adType = adTypesByTypeID[adTypeID][0]
            filterState = filterStates.get(adTypeID, None)
            if filterState == FILTERSTATE_WANT:
                wantCounter += 1
                hint.append(adType.typeName)

        if wantCounter > 0:
            text = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NumFiltersSelected', num=wantCounter)
        else:
            text = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NoFiltersSelected')
        return (text, ', '.join(hint))

    def OnSearchTimezoneIncrementChange(self, rangeSelector, fromData, toData, fromProportion, toProportion):
        settings.char.ui.Set('corp_recruitment_searchTimeZoneRange', (fromProportion, toProportion))
        self.UpdateSearchTimeZoneHint(rangeSelector, fromData[2], toData[2])

    def OnSearchTimezoneRangeChange(self, rangeSelector, fromData, toData, fromProportion, toProportion):
        self.OnSearchTimezoneIncrementChange(rangeSelector, fromData, toData, fromProportion, toProportion)
        self.DelayedSearchAdverts(delay=200)

    def UpdateSearchTimeZoneHint(self, rangeSelector, fromHour, toHour):
        year1800 = const.YEAR365 * 199L
        if self.localTimeZoneDiff > 0:
            localFromHour = fromHour - self.localTimeZoneDiff + 24
            localToHour = toHour - self.localTimeZoneDiff + 24
        else:
            localFromHour = fromHour - self.localTimeZoneDiff
            localToHour = toHour - self.localTimeZoneDiff
        fromTime = util.FmtDate(localFromHour * HOUR + year1800, fmt='ns')
        if localToHour == 24:
            toTime = localization.GetByLabel('/Carbon/UI/Common/DateTimeQuantity/DateTimeShort2Elements', value1='24', value2='00')
        else:
            toTime = util.FmtDate(localToHour * HOUR + year1800, fmt='ns')
        rangeSelector._fromHandle.hint = fromTime
        rangeSelector._toHandle.hint = toTime
        text = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/LocalTime', fromTime=fromTime, toTime=toTime)
        self.searchTimeZoneHint.text = text
        self.IndicateLoadingState(loading=True)

    def OnCorporationSizeIncrementChange(self, rangeSelector, fromData, toData, *args):
        f = fromData[2]
        t = toData[2]
        settings.char.ui.Set('corporation_recruitment_minmembers', f)
        settings.char.ui.Set('corporation_recruitment_maxmembers', t)
        if t == 6300:
            t = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AnyCorporationSize')
        hint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/CorpSizeHint', fromNum=f, toNum=t)
        self._corpSizeLabel.text = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/CorporationSize') + ' ' + hint
        self.IndicateLoadingState(loading=True)

    def OnCorporationSizeRangeChange(self, rangeSelector, fromData, toData, *args):
        self.OnCorporationSizeIncrementChange(rangeSelector, fromData, toData)
        self.DelayedSearchAdverts(delay=200)

    def OnAllianceCheckboxChange(self, checkbox):
        newValue = checkbox.checked
        settings.char.ui.Set('corporation_recruitment_excludeAlliancesChecked', newValue)
        self.DelayedSearchAdverts()

    def DelayedSearchAdverts(self, delay = 800):
        if getattr(self, '_searchReady', False):
            self.delayedSearchAdverts = base.AutoTimer(delay, self.SearchAdverts)
            self.IndicateLoadingState(loading=True)

    def SearchAdverts(self):
        self.delayedSearchAdverts = None
        searchMask = self.searchMask
        settings.char.ui.Set('corporation_recruitment_types', searchMask)
        newResultsEntries = self.GetSearchResults()
        if newResultsEntries:
            hint = None
        else:
            hint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/NoAdsFound')
        scroll = self.corpSearchResultsScroll
        newByIDs = {}
        for each in newResultsEntries:
            newByIDs[each.advert.adID] = each

        removeNodes = []
        keepInScroll = []
        currentAdIDs = []
        for each in scroll.GetNodes():
            currentAdIDs.append(each.advert.adID)
            if each.advert.adID not in newByIDs:
                removeNodes.append(each)
            else:
                each.update(newByIDs[each.advert.adID])
                keepInScroll.append(each)

        for each in newResultsEntries[:]:
            if each.advert.adID in currentAdIDs:
                newResultsEntries.remove(each)
            else:
                each.name = cfg.eveowners.Get(each.corporationID).name

        self.corpSearchResultsScroll.ShowHint(hint)
        if removeNodes:
            self.corpSearchResultsScroll.RemoveNodes(removeNodes, updateScroll=False)
        if newResultsEntries:
            self.corpSearchResultsScroll.AddNodes(-1, newResultsEntries, updateScroll=False)
        allNodes = self.corpSearchResultsScroll.GetNodes()
        if allNodes:
            sortedAllNodes = sorted(allNodes, key=lambda x: (x.grade, x.createDateTime, x.name.lower()), reverse=True)
            self.corpSearchResultsScroll.SetOrderedNodes(sortedAllNodes)
        for each in keepInScroll:
            if each.panel:
                each.panel.Load(each)

        self.IndicateLoadingState(loading=0)

    def IndicateLoadingState(self, loading = False):
        try:
            if loading:
                self.loadingWheel.Show()
                self.corpSearchResultsScroll.sr.maincontainer.opacity = 0.2
            else:
                self.loadingWheel.Hide()
                self.corpSearchResultsScroll.sr.maincontainer.opacity = 1.0
        except:
            pass

    def GetSearchResults(self, *args):
        result = []
        primeCorpIDs = []
        expandedAd = settings.char.ui.Get('corporation_recruitmentad_expanded', {})
        minMembers = settings.char.ui.Get('corporation_recruitment_minmembers', 0)
        maxMembers = settings.char.ui.Get('corporation_recruitment_maxmembers', 1000)
        excludeAlliancesChecked = settings.char.ui.Get('corporation_recruitment_excludeAlliancesChecked', False)
        fromProportion, toProportion = settings.char.ui.Get('corp_recruitment_searchTimeZoneRange', (0.0, 1.0))
        fromHour = fromProportion * 24
        toHour = toProportion * 24
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()

        def GetSearchMask(myFilterStates):
            mask = 0
            for adTypeID, fs in myFilterStates.iteritems():
                if adTypeID in adTypesByTypeID:
                    adType = adTypesByTypeID[adTypeID][0]
                    if fs == FILTERSTATE_WANT:
                        mask = AddBitToMask(bit=adType.typeMask, mask=mask)

            return mask

        filterStates = self.GetFilterStates()
        filterStateLanguages = self.GetFilterStatesLanguages()
        wantMask = GetSearchMask(filterStates)
        wantLanguageMask = GetSearchMask(filterStateLanguages)
        searchTimeMask = BuildMask(fromHour, toHour)
        ads = sm.GetService('corp').GetRecruitmentAdsByCriteria(typeMask=wantMask, langMask=wantLanguageMask, excludeAlliances=excludeAlliancesChecked, minMembers=minMembers, maxMembers=maxMembers, searchTimeMask=searchTimeMask)
        entries = self.MakeRecruitmentEntriesFromAdList(ads, wantMask, wantLanguageMask, expandedAd)
        return entries

    def ToggleSearchFilterState(self, adType, filterState):
        filterState = not filterState
        filterStates = self.GetFilterStates()
        filterStates[adType.typeID] = filterState
        self.SetFilterStates(filterStates)
        self.DelayedSearchAdverts()
        self.UpdateSearchFilterHints()

    def ToggleSearchFilterStateLanguage(self, adType, filterState):
        filterState = not filterState
        filterStates = self.GetFilterStatesLanguages()
        filterStates[adType.typeID] = filterState
        self.SetFilterStatesLanguages(filterStates)
        self.DelayedSearchAdverts()
        self.UpdateSearchFilterHints()

    def GetFilterStates(self):
        return settings.char.ui.Get('corporation_recruitment_searchFilterStatesX', {})

    def SetFilterStates(self, filterStates):
        settings.char.ui.Set('corporation_recruitment_searchFilterStatesX', filterStates)

    def GetFilterStatesLanguages(self):
        return settings.char.ui.Get('corporation_recruitment_searchFilterStatesLanguagesX', {})

    def SetFilterStatesLanguages(self, filterStates):
        settings.char.ui.Set('corporation_recruitment_searchFilterStatesLanguagesX', filterStates)


class RecruitmentEntry(uicls.SE_BaseClassCore):
    __guid__ = 'listentry.RecruitmentEntry'
    __notifyevents__ = []
    isDragObject = True
    LOGOSIZE = 48
    LOGOPADDING = LOGOSIZE * 2 + 18
    TEXTPADDING = 18
    CORPNAMEPAD = (LOGOPADDING,
     0,
     const.defaultPadding,
     0)
    CORPNAMECLASS = uicls.EveLabelLarge
    DESCPAD = (0,
     const.defaultPadding,
     const.defaultPadding * 2,
     16)
    DESCCLASS = uicls.EveLabelMedium
    DETAILSPAD = (TEXTPADDING,
     const.defaultPadding,
     const.defaultPadding,
     const.defaultPadding)
    DETAILSCLASS = uicls.EveLabelMedium
    RECRUITERSPAD = (0,
     const.defaultPadding,
     const.defaultPadding,
     const.defaultPadding)
    RECRUITERSCLASS = uicls.EveLabelMedium
    RECRCUITERSCONTAINERHEIGHT = 80
    COLUMNMARGIN = 10
    HEADERCONTAINER_HEIGHT = 54

    def Startup(self, *args):
        node = self.sr.node
        self.isDragObject = True
        self.corpSvc = sm.GetService('corp')
        self.lscSvc = sm.GetService('LSC')
        underline = uicls.Line(parent=self, align=uiconst.TOBOTTOM, color=(1, 1, 1, 0.05))
        self.headerContainer = uicls.Container(parent=self, align=uiconst.TOTOP, name='headerContainer', height=self.HEADERCONTAINER_HEIGHT, state=uiconst.UI_NORMAL)
        self.headerContainer.isDragObject = True
        self.headerContainer.GetDragData = self.GetDragData
        if not self.sr.node.standaloneMode:
            self.headerContainer.OnClick = self.ToggleExpanded
        self.headerContainer.OnMouseEnter = self.OnHeaderMouseEnter
        self.headerContainer.GetMenu = self.GetMenu
        self.rightCont = uicls.Container(parent=self.headerContainer, align=uiconst.TORIGHT, name='rightCont', width=0, state=uiconst.UI_PICKCHILDREN)
        if not self.sr.node.standaloneMode:
            self.expander = uicls.Sprite(parent=self.headerContainer, state=uiconst.UI_DISABLED, name='expander', pos=(0, 0, 16, 16), texturePath='res:/UI/Texture/Shared/getMenuIcon.png', align=uiconst.CENTERLEFT)
            if self.sr.node.expandedView:
                self.expander.rotation = -pi * 0.5
        self.corpLogo = uiutil.GetLogoIcon(itemID=node.corporationID, parent=self.headerContainer, align=uiconst.CENTERLEFT, name='corpLogo', state=uiconst.UI_DISABLED, size=self.LOGOSIZE, ignoreSize=True, left=14, top=0)
        if node.allianceID:
            self.allianceLogo = uicls.Sprite(parent=self.headerContainer, align=uiconst.CENTERLEFT, name='allianceLogo', state=uiconst.UI_NORMAL, height=self.LOGOSIZE, width=self.LOGOSIZE, ignoreSize=True, left=self.LOGOSIZE + self.corpLogo.left, top=0)
            uthread.new(self.LoadAllianceLogo, self.allianceLogo, node.allianceID)
        else:
            self.allianceLogo = uicls.Sprite(parent=self.headerContainer, align=uiconst.CENTERLEFT, name='allianceLogo', state=uiconst.UI_NORMAL, pos=(self.LOGOSIZE + self.corpLogo.left,
             0,
             self.LOGOSIZE,
             self.LOGOSIZE), texturePath='res:/UI/Texture/defaultAlliance.dds')
            self.allianceLogo.opacity = 0.2
            self.allianceLogo.hint = localization.GetByLabel('UI/PeopleAndPlaces/OwnerNotInAnyAlliance', corpName=cfg.eveowners.Get(node.corporationID).ownerName)
        if not self.sr.node.standaloneMode:
            self.allianceLogo.OnClick = self.ToggleExpanded
        self.expiryLabel = uicls.EveLabelMedium(parent=self.rightCont, align=uiconst.TOPRIGHT, top=const.defaultPadding, left=const.defaultPadding)
        self.applyButton = uicls.Button(parent=self.rightCont, label=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/Apply'), align=uiconst.BOTTOMRIGHT, left=const.defaultPadding, top=const.defaultPadding, func=self.Apply, state=uiconst.UI_HIDDEN, opacity=0.0)
        self.editButton = uicls.Button(parent=self.rightCont, label=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AdEdit'), align=uiconst.BOTTOMRIGHT, left=const.defaultPadding, top=const.defaultPadding, func=self.EditRecruitmentAd, state=uiconst.UI_HIDDEN)
        self.removeButton = uicls.Button(parent=self.rightCont, label=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AdRemove'), align=uiconst.BOTTOMRIGHT, left=self.editButton.left + self.editButton.width + const.defaultPadding, top=const.defaultPadding, func=self.DeleteRecruitmentAd, state=uiconst.UI_HIDDEN)
        self.warIcon = uicls.ButtonIcon(parent=self.rightCont, align=uiconst.TOPRIGHT, left=const.defaultPadding, top=const.defaultPadding, iconSize=20, width=24, height=24, texturePath='res:/UI/Texture/Icons/swords.png', func=self.OpenWarTab)
        self.warIcon.display = False
        self.gradeLabel = uicls.EveLabelLarge(parent=self.rightCont, name='grade', left=10, top=6, text='', state=uiconst.UI_NORMAL, align=uiconst.TOPRIGHT)
        self.gradeLabel.hint = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/MatchHint')
        corpAndAllianceNameAndTitle = listentry.RecruitmentEntry.GetHeaderText(node.corporationID, node.adTitle)
        self.corpNameLabel = self.CORPNAMECLASS(parent=self.headerContainer, name='corpNameLabel', padding=self.CORPNAMEPAD, text=corpAndAllianceNameAndTitle, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
        corpNameHeight = self.corpNameLabel.height + self.corpNameLabel.padTop + self.corpNameLabel.padBottom
        self.headerContainer.height = max(self.HEADERCONTAINER_HEIGHT, corpNameHeight)
        self.expandedParent = uicls.Container(parent=self)
        self.detailsContainer = uicls.GridContainer(name='detailsContainer', parent=self.expandedParent, align=uiconst.TOTOP, padding=(self.TEXTPADDING,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding), lines=1, columns=2)
        uicls.Line(parent=self.expandedParent, align=uiconst.TOTOP, padTop=-5, color=(0.0, 0.0, 0.0, 0.15))
        self.descriptionContainer = uicls.ContainerAutoSize(parent=self.expandedParent, align=uiconst.TOTOP, padding=(self.TEXTPADDING,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        self.descriptionLabel = self.DESCCLASS(parent=self.descriptionContainer, name='descriptionLabel', align=uiconst.TOTOP, padding=self.DESCPAD, state=uiconst.UI_NORMAL)
        self.detailsContainerLeft = uicls.Container(parent=self.detailsContainer)
        self.detailsContainerRight = uicls.Container(parent=self.detailsContainer)
        self.expandedTextLabelLeft = self.DETAILSCLASS(parent=self.detailsContainerLeft, name='expandedTextLabel', align=uiconst.TOTOP, padRight=self.COLUMNMARGIN, state=uiconst.UI_NORMAL)
        self.expandedTextLabelLeft.OnSizeChanged = self.UpdateDetailsContainer
        self.expandedTextLabelRight = self.DETAILSCLASS(parent=self.detailsContainerRight, name='expandedTextLabelRight', align=uiconst.TOTOP, padLeft=self.COLUMNMARGIN, state=uiconst.UI_NORMAL)
        self.expandedTextLabelRight.OnSizeChanged = self.UpdateDetailsContainer
        self.recruitersContainer = uicls.Container(parent=self.expandedParent, name='recruitersContainer', align=uiconst.TOTOP, padding=self.DETAILSPAD, height=self.RECRCUITERSCONTAINERHEIGHT, state=uiconst.UI_HIDDEN)
        if not node.standaloneMode:
            uicls.Fill(bgParent=self.expandedParent, color=(0, 0, 0, 0.2))
            self.hilite = uicls.Fill(bgParent=self.headerContainer, color=(1, 1, 1, 0))

    def LoadAllianceLogo(self, logo, ownerID, *args):
        sm.GetService('photo').GetAllianceLogo(ownerID, 128, logo, orderIfMissing=True)
        logo.hint = cfg.eveowners.Get(ownerID).ownerName

    def _OnSizeChange_NoBlock(self, newWidth, newHeight):
        if getattr(self, 'corpNameLabel', None):
            self.UpdateTextFade(duration=0)

    def UpdateDetailsContainer(self, *args):
        self.detailsContainer.height = max(self.expandedTextLabelLeft.textheight, self.expandedTextLabelRight.textheight)

    def Load(self, node):
        if node.fadeSize:
            toHeight, fromHeight = node.fadeSize
            self.clipChildren = True
            uicore.animations.MorphScalar(self, 'height', startVal=fromHeight, endVal=toHeight, duration=0.3)
            self.expandedParent.opacity = 0.0
            uicore.animations.FadeIn(self.expandedParent, duration=0.3)
        node.fadeSize = None
        if not node.standaloneMode:
            if not self.sr.node.expandedView and round(self.expander.rotation, 2) != 0.0:
                uicore.animations.Tr2DRotateTo(self.expander, -pi * 0.5, 0.0, duration=0.15)
            elif self.sr.node.expandedView and round(self.expander.rotation, 2) != round(-pi * 0.5, 2):
                uicore.animations.Tr2DRotateTo(self.expander, 0.0, -pi * 0.5, duration=0.15)
        if node.corpView:
            expireTime = node.advert.expiryDateTime - blue.os.GetWallclockTime()
            if expireTime > 0:
                expirationString = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AdExpiresIn', adDuration=expireTime)
            else:
                expirationString = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AdExpired')
            expiryLabel = self.expiryLabel
            expiryLabel.text = expirationString
            if expireTime < DAY:
                expiryLabel.color = util.Color.RED
            self.SetRightContWidth(isCorpView=True)
        else:
            if node.grade is not None:
                self.gradeLabel.text = localization.GetByLabel('UI/Common/Formatting/Percentage', percentage=node.grade)
            if len(getattr(node, 'warOpponents', set())) > 0:
                allWarsTextList = []
                for corpAtWar in node.warOpponents:
                    allWarsTextList.append(cfg.eveowners.Get(corpAtWar).name)

                allWarsText = '<br>'.join(allWarsTextList)
                warText = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/CorpAtWarWith', warTargets=allWarsText)
                self.warIcon.hint = warText
                self.warIcon.display = True
                self.warIcon.left = self.gradeLabel.textwidth + self.gradeLabel.left + 6
            else:
                self.warIcon.display = False
            self.SetRightContWidth(isCorpView=False)
        if node.expandedView:
            self.expandedParent.display = True
            self.descriptionLabel.text = node.advert.description.strip()
            leftText = listentry.RecruitmentEntry.GetLeftColumnText(node)
            self.expandedTextLabelLeft.text = leftText
            rightText = listentry.RecruitmentEntry.GetRightColumnText(node)
            self.expandedTextLabelRight.text = rightText
            self.detailsContainer.height = max(self.expandedTextLabelLeft.textheight, self.expandedTextLabelRight.textheight)
            self.LoadRecruiters()
        else:
            self.expandedParent.display = False

    def LoadRecruiters(self):
        node = self.sr.node
        if node.recruiters:
            if not len(self.recruitersContainer.children):
                self.recruitersContainer.Flush()
                self.recruitersContainer.display = True
                recruitersLabel = self.RECRUITERSCLASS(parent=self.recruitersContainer, name='recruitersLabel', align=uiconst.TOTOP, bold=True, padding=self.RECRUITERSPAD, text=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AdRecruiters'))
                numRecruiters = len(node.recruiters)
                lines = numRecruiters / 3
                if numRecruiters % 3:
                    lines += 1
                if numRecruiters < 3:
                    columns = numRecruiters
                else:
                    columns = 3
                top = recruitersLabel.textheight + recruitersLabel.padTop + recruitersLabel.padBottom
                self.recruitersContainer.height = top + self.RECRCUITERSCONTAINERHEIGHT
                self.recuitersGrid = uicls.GridContainer(parent=self.recruitersContainer, align=uiconst.TOTOP, lines=lines, columns=columns, height=lines * 32 + 4)
                for recruiterID in node.recruiters:
                    recruiterTypeID = cfg.eveowners.Get(recruiterID).typeID
                    container = uicls.Container(parent=self.recuitersGrid, clipChildren=True, padding=(const.defaultPadding,
                     2,
                     const.defaultPadding,
                     2))
                    uiutil.GetOwnerLogo(container, recruiterID, size=32, orderIfMissing=True)
                    startInfoTag = '<url=showinfo:%d//%d>' % (recruiterTypeID, recruiterID)
                    recruiterLink = localization.GetByLabel('UI/Agents/InfoLink', startInfoTag=startInfoTag, startColorTag='<color=-2039584>', objectName=cfg.eveowners.Get(recruiterID).name, endColorTag='</color>', endnfoTag='</url>')
                    nameLabel = uicls.EveLabelMedium(parent=container, name='nameLabel', text=recruiterLink, state=uiconst.UI_NORMAL, align=uiconst.CENTERLEFT, left=36)
                    isRecruiting = (util.KeyVal(recruiterID=recruiterID, corporationID=node.corporationID, adID=node.advert.adID),)
                    m = []
                    m += sm.GetService('menu').GetMenuFormItemIDTypeID(recruiterID, recruiterTypeID, **{'isRecruiting': isRecruiting})
                    m += sm.GetService('menu').GetGMTypeMenu(recruiterTypeID, divs=True)
                    nameLabel.GetMenu = lambda : m

    def GetLeftColumnText(node):
        text = ''
        playStyles = []
        advertMask = node.advert.typeMask
        showSearchMatch = node.searchMask is not None
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
        adGroups = sm.GetService('corp').GetCorpAdvertGroups()
        if showSearchMatch:
            memberText = localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/CorporationMemberCount', memberCount=node.memberCount)
            minMembers = settings.char.ui.Get('corporation_recruitment_minmembers', 0)
            maxMembers = settings.char.ui.Get('corporation_recruitment_maxmembers', 1000)
            text += MATCHED_COLOR + memberText + '<br><br>'
        for combinedGroupID in PLAYSTYLE_GROUPS:
            if combinedGroupID not in COMBINED_GROUPS:
                continue
            adTypeIDs = COMBINED_GROUPS[combinedGroupID].playstyleTypeIDs
            for adTypeID in adTypeIDs:
                adType = adTypesByTypeID[adTypeID][0]
                if advertMask & adType.typeMask:
                    playStyles.append(adType)

        if playStyles:
            playStyles = ', '.join([ listentry.RecruitmentEntry.ColorIfSearchMatch(adType, node.searchMask) for adType in playStyles ])
            text += '<b>%s%s</b><br>%s' % (WHITE_COLOR, adGroups[PLAYSTYLE_GROUPID].groupName, playStyles)
        return text

    def ColorIfSearchMatch(adType, searchMask):
        showSearchMatch = searchMask is not None
        if showSearchMatch:
            if adType.typeMask & searchMask:
                typeName = adType.typeName
                return MATCHED_COLOR + typeName
            else:
                return UNMATCHED_COLOR + adType.typeName
        return MATCHED_COLOR + adType.typeName

    def GetRightColumnText(node):
        text = ''
        advertMask = node.advert.typeMask
        langMask = node.advert.langMask
        showSearchMatch = node.searchMask is not None
        hint = []
        adTypesByGroupID = sm.GetService('corp').GetCorpAdvertTypesByGroupID()
        adTypesByTypeID = sm.GetService('corp').GetCorpAdvertTypesByTypeID()
        adGroups = sm.GetService('corp').GetCorpAdvertGroups()
        typeIDs = [ each.typeID for each in sm.GetService('corp').GetCorpAdvertTypesByGroupID()[AREA_OF_OPERATIONS_GROUPID] ]
        for adTypeID in typeIDs:
            adType = adTypesByTypeID[adTypeID][0]
            if adType.typeMask & advertMask:
                hint.append(listentry.RecruitmentEntry.ColorIfSearchMatch(adType, node.searchMask))

        if hint:
            hint = ', '.join(hint)
            text += '<b>%s%s</b><br>%s<br><br>' % (WHITE_COLOR, adGroups[AREA_OF_OPERATIONS_GROUPID].groupName, hint)
        typeList = []
        for adType in adTypesByGroupID[corputil.RECRUITMENT_GROUP_PRIMARY_LANGUAGE]:
            if langMask & adType.typeMask:
                typeList.append((adType.typeName.lower(), adType))

        if typeList:
            typeList = uiutil.SortListOfTuples(typeList)
            typeList = ', '.join((listentry.RecruitmentEntry.ColorIfSearchMatch(adType, node.searchLangMask) for adType in typeList))
            text += '<b>%s%s</b><br>%s<br><br>' % (WHITE_COLOR, adGroups[corputil.RECRUITMENT_GROUP_PRIMARY_LANGUAGE].groupName, typeList)
        fromProportion, toProportion = settings.char.ui.Get('corp_recruitment_searchTimeZoneRange', (0.0, 1.0))
        if node.timeZoneMask1 is None:
            f1, t1 = (0, 24)
        else:
            f1, t1 = GetTimeZoneFromMask(node.timeZoneMask1)
        if node.timeZoneMask2 is None:
            f2, t2 = (0, 24)
        else:
            f2, t2 = GetTimeZoneFromMask(node.timeZoneMask2)
        fromHour = int(fromProportion * 24)
        toHour = int(toProportion * 24)
        color = MATCHED_COLOR
        if showSearchMatch:
            if (fromHour <= f1 and toHour >= t1 or f1 < fromHour < t1 or f1 < toHour < t1) and SHOWSEARCHMATCH and node.searchMask is not None:
                color = MATCHED_COLOR
            else:
                color = UNMATCHED_COLOR
        text += color + localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/TimeZoneToAndFrom2', startTime=f1 * HOUR, endTime=t1 * HOUR, timeZoneText=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/TimeZone1'))
        if f2 is not None and t2 is not None:
            color = MATCHED_COLOR
            text += '<br>'
            if showSearchMatch:
                if (fromHour <= f2 and toHour >= t2 or f2 < fromHour < t2 or f2 < toHour < t2) and SHOWSEARCHMATCH and node.searchMask is not None:
                    color = MATCHED_COLOR
                else:
                    color = UNMATCHED_COLOR
            text += color + localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/TimeZoneToAndFrom2', startTime=long(f2 * HOUR), endTime=long(t2 * HOUR), timeZoneText=localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/TimeZone2'))
            text += '<br>'
        if node.channelID:
            channel = sm.GetService('LSC').GetChannelInfoForAnyChannel(node.channelID)
            if channel:
                channelName = channel.get('displayName', None)
                if channelName:
                    text += '<br><b>'
                    text += localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/RecruitmentChannelHeader')
                    text += '</b><br>'
                    text += '<a href="joinChannel:%s//%s//%s">%s</a>' % (node.channelID,
                     node.corporationID,
                     node.advert.adID,
                     channelName)
                    text += '<br>'
        return text

    def OpenWarTab(self, *args):
        uthread.new(self.OpenWarTabThread)

    def OpenWarTabThread(self, *args):
        node = self.sr.node
        if node.allianceID:
            typeID = const.typeAlliance
            itemID = node.allianceID
        else:
            typeID = const.typeCorporation
            itemID = node.corporationID
        infoWnd = sm.GetService('info').ShowInfo(typeID, itemID)
        if infoWnd:
            counter = 0
            while infoWnd.sr.maintabs is None and counter < 5:
                blue.pyos.synchro.SleepWallclock(100)
                counter += 1

            if infoWnd.sr.maintabs:
                infoWnd.sr.maintabs.ShowPanelByName(localization.GetByLabel('UI/InfoWindow/TabNames/WarHistory'))

    def GetDynamicHeight(node, width):
        cls = listentry.RecruitmentEntry
        corpAndAllianceNameAndTitle = listentry.RecruitmentEntry.GetHeaderText(node.corporationID, node.adTitle)
        pl, pt, pr, pb = cls.CORPNAMEPAD
        corpNameWidth, corpNameHeight = cls.CORPNAMECLASS.MeasureTextSize(corpAndAllianceNameAndTitle)
        corpNameHeight += pt + pb
        baseHeight = max(cls.HEADERCONTAINER_HEIGHT, corpNameHeight)
        if not node.expandedView:
            return baseHeight
        pl, pt, pr, pb = cls.DESCPAD
        descWidth, descHeight = cls.DESCCLASS.MeasureTextSize(node.advert.description, width=width - pl - pr)
        descHeight += pt + pb
        pl, pt, pr, pb = cls.DETAILSPAD
        leftText = listentry.RecruitmentEntry.GetLeftColumnText(node)
        leftWidth, leftHeight = cls.DETAILSCLASS.MeasureTextSize(leftText, width=(width - pl - pr) / 2 - cls.COLUMNMARGIN)
        leftHeight += pt + pb
        rightText = listentry.RecruitmentEntry.GetRightColumnText(node)
        rightWidth, rightHeight = cls.DETAILSCLASS.MeasureTextSize(rightText, width=(width - pl - pr) / 2 - cls.COLUMNMARGIN)
        rightHeight += pt + pb
        recruitersHeight = 0
        if node.recruiters:
            pl, pt, pr, pb = cls.RECRUITERSPAD
            recruitHeaderWidth, recruitHeaderHeight = cls.RECRUITERSCLASS.MeasureTextSize(localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/AdRecruiters'), width=width - pl - pr, bold=1)
            recruitersHeight = cls.RECRCUITERSCONTAINERHEIGHT + recruitHeaderHeight + pt + pb
        return baseHeight + descHeight + max(leftHeight, rightHeight) + recruitersHeight + 8

    def GetHeaderText(corpID, adTitle):
        headerText = '<b>%s</b>' % cfg.eveowners.Get(corpID).ownerName
        headerText += '<br>%s' % adTitle
        return headerText

    def GetMenu(self):
        node = self.sr.node
        m = []
        if node.corpView:
            if HasAccess(self.sr.node.corporationID):
                m.append((uiutil.MenuLabel('UI/Corporations/CorporationWindow/Recruitment/AdEdit'), self.EditRecruitmentAd))
                m.append((uiutil.MenuLabel('UI/Corporations/CorporationWindow/Recruitment/AdRemove'), self.DeleteRecruitmentAd))
        elif self.sr.node.corporationID != session.corpid:
            m.append((uiutil.MenuLabel('UI/Corporations/CorporationWindow/Recruitment/ApplyToJoinCorporation'), self.Apply))
        if node.channelID and not self.lscSvc.IsJoined(node.channelID):
            m.append((uiutil.MenuLabel('UI/Corporations/CorporationWindow/Recruitment/JoinCorporationRecruitmentChannel'), self.JoinChannel))
        if not self.sr.node.standaloneMode:
            m.append((uiutil.MenuLabel('UI/Corporations/CorporationWindow/Recruitment/OpenAdInNewWindow'), sm.GetService('corp').OpenCorpAdInNewWindow, (node.advert.corporationID, node.advert.adID)))
        m.append(None)
        if node.advert:
            if util.IsCorporation(node.corporationID):
                m += [(uiutil.MenuLabel('UI/Common/Corporation'), sm.GetService('menu').GetMenuFormItemIDTypeID(node.corporationID, const.typeCorporation))]
            if util.IsAlliance(node.allianceID):
                m += [(uiutil.MenuLabel('UI/Common/Alliance'), sm.GetService('menu').GetMenuFormItemIDTypeID(node.allianceID, const.typeAlliance))]
            if m:
                m += [None]
        if node.Get('GetMenu', None):
            m += node.GetMenu(self)
        return m

    def ToggleExpanded(self):
        reloadNodes = [self.sr.node]
        if self.sr.node.expandedView:
            uicore.animations.Tr2DRotateTo(self.expander, -pi * 0.5, 0.0, duration=0.15)
            self.sr.node.expandedView = False
            current = settings.char.ui.Get('corporation_recruitmentad_expanded', {})
            current[self.sr.node.corpView] = None
            settings.char.ui.Set('corporation_recruitmentad_expanded', current)
        else:
            for each in self.sr.node.scroll.sr.nodes:
                if each.expandedView:
                    reloadNodes.append(each)
                    each.expandedView = False

            uicore.animations.Tr2DRotateTo(self.expander, 0.0, -pi * 0.5, duration=0.15)
            current = settings.char.ui.Get('corporation_recruitmentad_expanded', {})
            current[self.sr.node.corpView] = self.sr.node.advert.adID
            settings.char.ui.Set('corporation_recruitmentad_expanded', current)
            if self.sr.node.recruiters is None:
                self.sr.node.recruiters = self.corpSvc.GetRecruiters(self.sr.node.advert.adID)
            self.sr.node.expandedView = True
            self.sr.node.fadeSize = (listentry.RecruitmentEntry.GetDynamicHeight(self.sr.node, self.width), self.height)
        self.sr.node.scroll.ReloadNodes(reloadNodes, updateHeight=True)

    def Apply(self, *args):
        applicationID = self.corpSvc.ApplyForMembership(self.sr.node.corporationID)
        with util.ExceptionEater('eventLog'):
            self.corpSvc.LogCorpRecruitmentEvent('ApplyToJoin', session.corpid, session.allianceid, self.sr.node.corporationID, self.sr.node.advert.adID, applicationID)

    def DeleteRecruitmentAd(self, *args):
        if eve.Message('CorpAdsAreYouSureYouWantToDelete', None, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            self.corpSvc.DeleteRecruitmentAd(self.sr.node.advert.adID)

    def EditRecruitmentAd(self, *args):
        self.sr.node.editFunc(self.sr.node.advert)

    def JoinChannel(self, *args):
        self.lscSvc.JoinOrLeaveChannel(self.sr.node.channelID)
        self.Load(self.sr.node)

    def OnHeaderMouseEnter(self, *args):
        if self.sr.node.standaloneMode:
            return
        uicore.animations.FadeIn(self.hilite, 0.05, duration=0.1)
        self.ShowButtons()
        self.hiliteTimer = base.AutoTimer(1, self._CheckIfStillHilited)

    def OnMouseEnter(self, *args):
        if self.sr.node.standaloneMode:
            return
        self.ShowButtons()
        self.hiliteTimer = base.AutoTimer(1, self._CheckIfStillHilited)

    def _CheckIfStillHilited(self):
        if self.sr.node.standaloneMode:
            return
        if uiutil.IsUnder(uicore.uilib.mouseOver, self) or uicore.uilib.mouseOver is self:
            return
        uicore.animations.FadeOut(self.hilite, duration=0.3)
        self.hiliteTimer = None
        for each in (self.applyButton, self.editButton, self.removeButton):
            if each.display:
                uicore.animations.FadeTo(each, each.opacity, 0.0, duration=0.1, callback=self.HideButtons)

    def SetRightContWidth(self, isCorpView = False):
        if isCorpView:
            width = self.expiryLabel.textwidth + self.expiryLabel.left
            if self.removeButton.display:
                width = max(width, self.removeButton.left + self.removeButton.width)
        else:
            width = self.gradeLabel.textwidth + 10
            if self.warIcon.display:
                width += self.warIcon.width
            if self.applyButton.display:
                width = max(width, self.applyButton.width + self.applyButton.left)
        self.rightCont.width = width

    def HideButtons(self):
        for each in (self.applyButton, self.editButton, self.removeButton):
            each.display = False

        self.UpdateTextFade()

    def ShowButtons(self):
        if self.sr.node.corpView:
            self.applyButton.display = False
            if HasAccess(self.sr.node.corporationID):
                self.editButton.display = True
                uicore.animations.FadeTo(self.editButton, self.editButton.opacity, 1.0, duration=0.3)
                self.removeButton.display = True
                uicore.animations.FadeTo(self.removeButton, self.removeButton.opacity, 1.0, duration=0.3)
        else:
            if self.sr.node.corporationID != session.corpid:
                self.applyButton.display = True
            uicore.animations.FadeTo(self.applyButton, self.applyButton.opacity, 1.0, duration=0.3)
            self.editButton.display = False
            self.removeButton.display = False
        self.UpdateTextFade()

    def UpdateTextFade(self, duration = 0.3):
        self.SetRightContWidth(isCorpView=self.sr.node.corpView)
        if self.sr.node.corpView:
            rightPad = self.rightCont.width
        elif self.applyButton.display:
            rightPad = self.rightCont.width
        else:
            rightPad = self.rightCont.width
        fadeEnd = self.width - rightPad - self.corpNameLabel.padLeft - 10
        self.corpNameLabel.SetRightAlphaFade(fadeEnd=fadeEnd, maxFadeWidth=20)

    def GetDragData(self, *args):
        return [self.sr.node]


def RemoveBitFromMask(bit, mask):
    if mask & bit:
        newMask = mask ^ bit
    return newMask


def AddBitToMask(bit, mask):
    newMask = bit | mask
    return newMask


def BuildMask(from1, to1):
    mask = 0

    def TwoToThePowerOf(power):
        return 1 << power

    if from1 > to1:
        for i in xrange(24):
            if i < to1:
                mask = AddBitToMask(bit=TwoToThePowerOf(i), mask=mask)
            if i >= from1:
                mask = AddBitToMask(bit=TwoToThePowerOf(i), mask=mask)

    else:
        for i in xrange(24):
            if i >= from1 and i < to1:
                mask = AddBitToMask(bit=TwoToThePowerOf(i), mask=mask)

    return mask


def GetTimeZoneFromMask(timeMaskInt):
    if timeMaskInt <= 0:
        return (0, 24)
    toHour = 24
    fromHour = None
    counter = 0
    while timeMaskInt != 0:
        timeMaskInt, bitSet = divmod(timeMaskInt, 2)
        if bitSet == 1:
            if fromHour is None:
                fromHour = counter
            elif fromHour is not None and toHour < 24:
                fromHour = counter
                break
        elif fromHour is not None and toHour == 24:
            toHour = counter
        counter += 1

    if toHour == 24:
        toHour = counter
    return (fromHour, toHour)


class CorpRecruitmentAdStandaloneWindow(uicls.Window):
    __guid__ = 'uicls.CorpRecruitmentAdStandaloneWindow'
    default_width = 500
    default_height = 400

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.SetTopparentHeight(0)
        data = attributes.data
        if data.corporationID != session.corpid:
            buttons = [[localization.GetByLabel('UI/Corporations/CorporationWindow/Recruitment/ApplyToJoinCorporation'),
              self.ApplyToCorp,
              (data.corporationID,),
              81]]
            btns = uicls.ButtonGroup(btns=buttons, parent=self.sr.main, idx=0)
        self.scroll = uicls.Scroll(parent=self.sr.main, name='scroll')
        self.scroll.RemoveActiveFrame()
        self.scroll.HideBackground()
        self.SetCaption('%s - %s' % (cfg.eveowners.Get(data.corporationID).name, data.adTitle))
        self.ModifyDataForThisWindow(data)
        entry = listentry.Get('RecruitmentEntry', data=data)
        self.scroll.Load(contentList=[entry])

    def ModifyDataForThisWindow(self, data):
        data.corpView = False
        data.standaloneMode = True
        data.searchMask = None
        data.searchLangMask = None
        data.grade = None
        data.expandedView = True
        if getattr(data, 'recruiters', None) is None:
            data.recruiters = sm.GetService('corp').GetRecruiters(data.advert.adID)

    def ApplyToCorp(self, corpID):
        sm.GetService('corp').ApplyForMembership(corpID)


class WelcomeMailWindow(uicls.Window):
    __guid__ = 'uicls.WelcomeMailWindow'
    __notifyevents__ = ['OnCorporationWelcomeMailChanged']
    default_width = 500
    default_height = 400

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.EditWelcomeMail()
        self.SetTopparentHeight(0)
        self.SetCaption(localization.GetByLabel('UI/Corporations/Applications/CorpWelcomeMail'))

    def EditWelcomeMail(self, *args):
        welcomeMail = sm.GetService('corp').GetCorpWelcomeMail()
        self.confirmButtonGroup = uicls.ButtonGroup(btns=[(localization.GetByLabel('UI/Generic/Apply'),
          self.SaveWelcomeMail,
          (),
          84)], parent=self.sr.main)
        lastEditBy = ''
        self.welcomeMailEditLabel = uicls.EveLabelSmall(parent=self.sr.main, text=lastEditBy, align=uiconst.TOBOTTOM, height=12, padding=const.defaultPadding)
        if welcomeMail.characterID is not None:
            lastEditBy = localization.GetByLabel('UI/Corporations/Applications/WelcomeMailLastEdit', characterName=cfg.eveowners.Get(welcomeMail.characterID).name, changeDate=welcomeMail.changeDate)
            self.welcomeMailEditLabel.text = lastEditBy
            self.welcomeMailEditLabel.display = True
        else:
            self.welcomeMailEditLabel.display = False
        self.welcomeMailContentContainer = uicls.EditPlainText(parent=self.sr.main, align=uiconst.TOALL, showattributepanel=1, padding=const.defaultPadding)
        self.welcomeMailContentContainer.SetValue(welcomeMail.welcomeMail)

    def SaveWelcomeMail(self, *args):
        welcomeMail = sm.GetService('corp').GetCorpWelcomeMail()
        newWelcomeMail = self.welcomeMailContentContainer.GetValue()
        if newWelcomeMail != welcomeMail.welcomeMail:
            sm.GetService('corp').SetCorpWelcomeMail(newWelcomeMail)

    def OnCorporationWelcomeMailChanged(self, characterID, changeDate):
        self.UpdateWelcomeMail(characterID, changeDate)

    def UpdateWelcomeMail(self, characterID, changeDate):
        if getattr(self, 'welcomeMailEditLabel', None) is not None:
            if self.welcomeMailEditLabel.display == False:
                self.welcomeMailEditLabel.display = True
                uicore.animations.MorphScalar(self.welcomeMailEditLabel, 'height', startVal=0, endVal=12, duration=1.0)
            uicore.animations.FadeOut(self.welcomeMailEditLabel, duration=1.0, sleep=True)
            self.welcomeMailEditLabel.text = localization.GetByLabel('UI/Corporations/Applications/WelcomeMailLastEdit', characterName=cfg.eveowners.Get(characterID).name, changeDate=changeDate)
            if characterID == session.charid:
                color = util.Color(0.0, 1.0, 0.0, 0.0).GetRGBA()
            else:
                color = util.Color(1.0, 0.0, 0.0, 0.0).GetRGBA()
            self.welcomeMailEditLabel.color = color
            uicore.animations.FadeIn(self.welcomeMailEditLabel, endVal=1.0, duration=1.0)