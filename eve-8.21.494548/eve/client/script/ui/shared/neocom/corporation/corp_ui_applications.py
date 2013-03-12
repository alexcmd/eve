#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/neocom/corporation/corp_ui_applications.py
import blue
import uthread
import util
import xtriui
import uix
import form
import dbg
import log
import listentry
import uicls
import uiconst
import uiutil
import localization
import base
from math import pi

class ApplicationsWindow(uicls.Container):
    __guid__ = 'uicls.ApplicationsTab'
    __nonpersistvars__ = []
    statusLabelDict = {const.crpApplicationAppliedByCharacter: 'UI/Corporations/CorpApplications/ApplicationUnprocessed',
     const.crpApplicationAcceptedByCorporation: 'UI/Corporations/CorpApplications/ApplicationStatusInvited',
     const.crpApplicationRejectedByCorporation: 'UI/Corporations/CorpApplications/ApplicationStatusRejected',
     const.crpApplicationAcceptedByCharacter: 'UI/Corporations/CorpApplications/ApplicationStatusAccepted',
     const.crpApplicationRejectedByCharacter: 'UI/Corporations/CorpApplications/ApplicationStatusInvitationRejected',
     const.crpApplicationWithdrawnByCharacter: 'UI/Corporations/CorpApplications/ApplicationStatusWithdrawn'}
    statusSetting = 'applicationStatus_%d'

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.ownerID = attributes.ownerID
        if self.ownerID == session.charid:
            self.myView = True
        else:
            self.myView = False
        self.quickFilterSetting = 'applicationsQuickFilter_OwnerID%s' % self.ownerID
        self.filteringBy = settings.char.ui.Get(self.quickFilterSetting, '')
        self.showingOld = settings.char.ui.Get('applicationsShowOld_%s' % self.ownerID, False)
        self.InitViewingStatus()
        self.topContainer = uicls.Container(parent=self, name='topContainer', align=uiconst.TOTOP, height=20)
        self.quickFilter = uicls.QuickFilterEdit(parent=self.topContainer, align=uiconst.TOPRIGHT, padding=(1, 1, 1, 1), setvalue=self.filteringBy)
        self.quickFilter.ReloadFunction = self.OnSearchFieldChanged
        self.quickFilter.OnReturn = self.SearchByCharacterName
        self.statusFilter = uicls.UtilMenu(parent=self.topContainer, align=uiconst.TOPRIGHT, padding=(1, 1, 1, 1), left=100, GetUtilMenu=self.StatusFilterMenu, texturePath='res:/ui/texture/icons/38_16_205.png', hint=localization.GetByLabel('UI/Corporations/CorpApplications/FilterByStatus'))
        if self.myView:
            self.topContainer.display = False
        self.applicationContainer = uicls.Container(name='applications', parent=self, align=uiconst.TOALL)
        self.applicationScroll = uicls.BasicDynamicScroll(name='applicationsScroll', parent=self.applicationContainer, align=uiconst.TOALL)
        self.applicationScroll.noContentHint = localization.GetByLabel('UI/Corporations/CorpApplications/NoApplicationsFound')
        self.applicationScroll.multiSelect = 0

    def GetApplications(self, statusList = None):
        if statusList is None:
            statusList = self.sr.viewingStatus
        filteredApplications = []
        if self.ownerID == session.corpid:
            if const.corpRolePersonnelManager & session.corprole != const.corpRolePersonnelManager:
                return []
            if self.showingOld:
                applications = sm.GetService('corp').GetOldApplicationsWithStatus(statusList)
            else:
                applications = sm.GetService('corp').GetApplicationsWithStatus(statusList)
            if len(self.filteringBy):
                ownersToPrime = set()
                for application in applications:
                    ownersToPrime.add(application.characterID)

                if len(ownersToPrime) > 0:
                    cfg.eveowners.Prime(ownersToPrime)
                for application in applications:
                    if cfg.eveowners.Get(application.characterID).name.find(self.filteringBy) > -1:
                        filteredApplications.append(application)

            else:
                filteredApplications = applications
        elif self.showingOld:
            filteredApplications = sm.GetService('corp').GetMyOldApplicationsWithStatus(None)
        else:
            filteredApplications = sm.GetService('corp').GetMyApplicationsWithStatus(None)
        return filteredApplications

    def GetCorpApplicationEntries(self, applications):
        ownersToPrime = set()
        scrolllist = []
        if self.myView:
            ownerKey = 'corporationID'
        else:
            ownerKey = 'characterID'
        expandedApp = settings.char.ui.Get('corporation_applications_expanded', {})
        for application in applications:
            ownerID = getattr(application, ownerKey, None)
            if ownerID is None:
                continue
            ownersToPrime.add(ownerID)
            if len(ownersToPrime):
                cfg.eveowners.Prime(ownersToPrime)
            data = {'myView': self.myView,
             'application': application,
             'sort_%s' % localization.GetByLabel('UI/Common/Date'): application.applicationDateTime,
             'charID': application.characterID,
             'isExpanded': expandedApp.get(self.myView, None) == application.applicationID}
            entry = listentry.Get('CorpApplicationEntry', data)
            scrolllist.append(entry)

        return scrolllist

    def OnSearchFieldChanged(self):
        myFilter = self.quickFilter.GetValue().strip()
        if myFilter == '':
            self.filteringBy = myFilter
            settings.char.ui.Set(self.quickFilterSetting, self.filteringBy)
            applications = self.GetApplications()
            scrolllist = self.GetCorpApplicationEntries(applications)
            self.RefreshApplicationScroll(addNodes=scrolllist, forceClear=True)

    def SearchByCharacterName(self, *args):
        myFilter = self.quickFilter.GetValue().strip()
        if len(myFilter) == 0:
            return
        self.filteringBy = myFilter
        applications = self.GetApplications()
        scrolllist = self.GetCorpApplicationEntries(applications)
        self.RefreshApplicationScroll(addNodes=scrolllist, forceClear=True)

    def StatusFilterMenu(self, menuParent):
        for statusConst, statusLabel in self.statusLabelDict.iteritems():
            if statusConst == const.crpApplicationRejectedByCharacter:
                continue
            isChecked = settings.char.ui.Get(self.statusSetting % statusConst, False)
            menuParent.AddCheckBox(localization.GetByLabel(statusLabel), checked=isChecked, callback=(self.ToggleStatusFilter, statusConst, isChecked))

        menuParent.AddDivider()
        menuParent.AddCheckBox(localization.GetByLabel('UI/Corporations/CorpApplications/ShowOldApplications'), checked=self.showingOld, callback=(self.SetShowOld, not self.showingOld))

    def SetShowOld(self, value):
        settings.char.ui.Set('applicationsShowOld_%s' % self.ownerID, value)
        self.showingOld = value
        applications = self.GetApplications()
        scrolllist = self.GetCorpApplicationEntries(applications)
        self.RefreshApplicationScroll(addNodes=scrolllist, forceClear=True)

    def ToggleStatusFilter(self, statusConst, isChecked):
        viewingStatus = []
        if isChecked:
            removeNodes = []
            settings.char.ui.Set(self.statusSetting % statusConst, False)
            for status in self.sr.viewingStatus:
                if status != statusConst:
                    viewingStatus.append(status)

            for applicationNode in self.applicationScroll.GetNodes():
                if applicationNode.application.status not in viewingStatus:
                    removeNodes.append(applicationNode)

            self.RefreshApplicationScroll(removeNodes=removeNodes)
        else:
            settings.char.ui.Set(self.statusSetting % statusConst, True)
            viewingStatus.append(statusConst)
            viewingStatus.extend(self.sr.viewingStatus)
            applications = self.GetApplications([statusConst])
            scrolllist = self.GetCorpApplicationEntries(applications)
            if len(scrolllist) > 0:
                self.RefreshApplicationScroll(addNodes=scrolllist)
        self.sr.viewingStatus = viewingStatus

    def InitViewingStatus(self):
        viewingStatus = []
        for statusConst in self.statusLabelDict.iterkeys():
            if self.ownerID == session.charid:
                viewingStatus.append(statusConst)
            elif settings.char.ui.Get(self.statusSetting % statusConst, False):
                viewingStatus.append(statusConst)

        if len(viewingStatus) == 0:
            viewingStatus = [const.crpApplicationAppliedByCharacter]
            settings.char.ui.Set(self.statusSetting % const.crpApplicationAppliedByCharacter, True)
        self.sr.viewingStatus = viewingStatus

    def LoadApplications(self):
        if self.destroyed:
            return
        try:
            myFilter = self.quickFilter.GetValue()
            if len(myFilter):
                self.filteringBy = myFilter
            sm.GetService('corpui').ShowLoad()
            applications = self.GetApplications()
            scrolllist = self.GetCorpApplicationEntries(applications)
            if len(scrolllist) > 0:
                self.RefreshApplicationScroll(addNodes=scrolllist)
        except:
            pass
        finally:
            sm.GetService('corpui').HideLoad()

    def RefreshApplicationScroll(self, addNodes = [], removeNodes = [], reloadNodes = [], forceClear = False):
        if forceClear:
            self.applicationScroll.Clear()
        elif len(removeNodes):
            self.applicationScroll.RemoveNodes(removeNodes, updateScroll=True)
        if len(reloadNodes):
            self.applicationScroll.ReloadNodes(reloadNodes)
        if len(addNodes):
            self.applicationScroll.AddNodes(0, addNodes, updateScroll=True)
        toSort = self.applicationScroll.GetNodes()
        if toSort:
            sortedNodes = sorted(toSort, key=lambda x: x.application.applicationDateTime, reverse=True)
            self.applicationScroll.SetOrderedNodes(sortedNodes)

    def OnCorporationApplicationChanged(self, corpID, applicantID, applicationID, newApplication):
        if self.destroyed:
            return
        for applicationNode in self.applicationScroll.GetNodes():
            if applicationNode.application.applicationID == applicationID:
                applicationNode.application = newApplication
                if newApplication.status in self.sr.viewingStatus:
                    self.RefreshApplicationScroll(reloadNodes=[applicationNode])
                else:
                    self.RefreshApplicationScroll(removeNodes=[applicationNode])
                break
        else:
            if newApplication.status in self.sr.viewingStatus:
                scrolllist = self.GetCorpApplicationEntries([newApplication])
                self.RefreshApplicationScroll(addNodes=scrolllist)


class ViewCorpApplicationWnd(uicls.Window):
    __guid__ = 'form.ViewCorpApplicationWnd'
    default_width = 400
    default_height = 255
    default_minSize = (default_width, default_height)

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.DefineButtons(uiconst.OKCANCEL, okFunc=self.Confirm, cancelFunc=self.Cancel)
        self.charID = attributes.get('characterID')
        self.appText = attributes.get('applicationText')
        self.status = attributes.get('status')
        wndCaption = localization.GetByLabel('UI/Corporations/CorpApplications/ViewApplicationDetailCaption')
        self.SetCaption(wndCaption)
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        self.ConstructLayout()

    def ConstructLayout(self):
        charInfoCont = uicls.Container(name='charInfo', parent=self.sr.main, align=uiconst.TOTOP, height=68, padding=const.defaultPadding)
        charLogoCont = uicls.Container(name='charLogo', parent=charInfoCont, align=uiconst.TOLEFT, width=68)
        charTextCont = uicls.Container(name='charName', parent=charInfoCont, align=uiconst.TOALL)
        applicationCont = uicls.Container(name='charInfo', parent=self.sr.main, align=uiconst.TOALL, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding))
        uiutil.GetOwnerLogo(charLogoCont, self.charID, size=64, noServerCall=True)
        charText = localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationSubjectLine', player=self.charID)
        charNameLabel = uicls.EveLabelLarge(parent=charTextCont, text=charText, top=12, align=uiconst.TOPLEFT, width=270)
        editText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/CorporationApplicationText')
        editLabel = uicls.EveLabelSmall(parent=applicationCont, text=editText, align=uiconst.TOTOP)
        self.rejectRb = uicls.Checkbox(text=localization.GetByLabel('UI/Corporations/CorpApplications/RejectApplication'), parent=applicationCont, configName='reject', retval=1, checked=False, groupname='state', align=uiconst.TOBOTTOM)
        self.acceptRb = uicls.Checkbox(text=localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationInviteApplicant'), parent=applicationCont, configName='accept', retval=0, checked=True, groupname='state', align=uiconst.TOBOTTOM)
        if self.status not in (const.crpApplicationAppliedByCharacter, const.crpApplicationAcceptedByCorporation):
            self.rejectRb.state = uiconst.UI_HIDDEN
            self.acceptRb.state = uiconst.UI_HIDDEN
        self.applicationText = uicls.EditPlainText(setvalue=self.appText, parent=applicationCont, maxLength=1000, readonly=True)

    def Confirm(self, *args):
        if self.status not in (const.crpApplicationAppliedByCharacter, const.crpApplicationAcceptedByCorporation):
            self.Cancel()
        applicationText = self.applicationText.GetValue()
        if len(applicationText) > 1000:
            error = localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationTextTooLong', length=len(applicationText))
            eve.Message('CustomInfo', {'info': error})
        else:
            if self.rejectRb.checked:
                rejected = const.crpApplicationRejectedByCorporation
            else:
                rejected = const.crpApplicationAcceptedByCorporation
            self.result = rejected
            self.SetModalResult(1)

    def Cancel(self, *args):
        self.result = None
        self.SetModalResult(0)


class MyCorpApplicationWnd(uicls.Window):
    __guid__ = 'form.MyCorpApplicationWnd'
    default_width = 400
    default_height = 300
    default_minSize = (default_width, default_height)

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.corpid = attributes.get('corpid')
        self.application = attributes.get('application')
        self.status = attributes.get('status')
        self.windowID = 'viewApplicationWindow'
        if self.status in (const.crpApplicationAppliedByCharacter, const.crpApplicationAcceptedByCorporation):
            self.DefineButtons(uiconst.OKCANCEL, okFunc=self.Confirm, cancelFunc=self.Cancel)
        else:
            self.DefineButtons(uiconst.OK, okFunc=self.Cancel)
        wndCaption = localization.GetByLabel('UI/Corporations/CorpApplications/ViewApplicationDetailCaption')
        self.SetCaption(wndCaption)
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        self.ConstructLayout()

    def ConstructLayout(self):
        self.acceptRb = None
        self.withdrawRb = None
        corpName = cfg.eveowners.Get(self.corpid).name
        corpInfoCont = uicls.Container(name='corpInfo', parent=self.sr.main, align=uiconst.TOTOP, height=68, padding=const.defaultPadding)
        corpLogoCont = uicls.Container(name='corpLogo', parent=corpInfoCont, align=uiconst.TOLEFT, width=68)
        corpTextCont = uicls.Container(name='corpName', parent=corpInfoCont, align=uiconst.TOALL)
        controlCont = uicls.Container(name='buttons', parent=self.sr.main, align=uiconst.TOBOTTOM, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding))
        controlContHeight = 0
        applicationCont = uicls.Container(name='applicationCont', parent=self.sr.main, align=uiconst.TOALL, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding))
        uiutil.GetOwnerLogo(corpLogoCont, self.corpid, size=64, noServerCall=True)
        corpText = localization.GetByLabel('UI/Corporations/CorpApplications/YourApplicationToJoin', corpName=corpName)
        corpNameLabel = uicls.EveLabelLarge(parent=corpTextCont, text=corpText, top=12, align=uiconst.TOPLEFT, width=270)
        if self.status == const.crpApplicationAppliedByCharacter:
            statusText = localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationNotProcessed')
            statusLabel = uicls.EveLabelSmall(parent=applicationCont, text=statusText, align=uiconst.TOTOP, padBottom=const.defaultPadding)
        else:
            statusText = statusLabel = ''
        editText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/CorporationApplicationText')
        editLabel = uicls.EveLabelSmall(parent=applicationCont, text=editText, align=uiconst.TOTOP)
        if self.application.applicationText is not None:
            appText = self.application.applicationText
        else:
            appText = ''
        self.applicationText = uicls.EditPlainText(setvalue=appText, parent=applicationCont, maxLength=1000, readonly=True)
        if self.status in (const.crpApplicationAppliedByCharacter, const.crpApplicationAcceptedByCorporation):
            isWithdrawChecked = True
            if self.status == const.crpApplicationAcceptedByCorporation:
                isWithdrawChecked = False
                self.acceptRb = uicls.Checkbox(text=localization.GetByLabel('UI/Corporations/CorpApplications/AcceptApplication'), parent=controlCont, configName='accept', retval=1, checked=True, groupname='stateGroup', align=uiconst.TOBOTTOM)
                controlContHeight += 40
            self.withdrawRb = uicls.Checkbox(text=localization.GetByLabel('UI/Corporations/CorpApplications/WithdrawApplication'), parent=controlCont, configName='accept', retval=3, checked=isWithdrawChecked, groupname='stateGroup', align=uiconst.TOBOTTOM)
            controlContHeight += 20
        controlCont.height = controlContHeight

    def Confirm(self, *args):
        self.result = None
        if self.withdrawRb.checked:
            self.result = const.crpApplicationWithdrawnByCharacter
        elif self.acceptRb.checked:
            self.result = const.crpApplicationAcceptedByCharacter
        self.SetModalResult(1)

    def Cancel(self, *args):
        self.result = None
        self.SetModalResult(0)

    def WithdrawApplication(self, *args):
        try:
            sm.GetService('corpui').ShowLoad()
            application = self.application
            sm.GetService('corpui').ShowLoad()
            sm.GetService('corp').UpdateApplicationOffer(application.applicationID, application.characterID, application.corporationID, application.applicationText, const.crpApplicationWithdrawnByCharacter)
        finally:
            sm.GetService('corpui').HideLoad()
            uicls.Window.CloseIfOpen(windowID='viewApplicationWindow')


class ApplyToCorpWnd(uicls.Window):
    __guid__ = 'form.ApplyToCorpWnd'
    default_width = 400
    default_height = 245
    default_minSize = (default_width, default_height)

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.DefineButtons(uiconst.OKCANCEL, okFunc=self.Confirm, cancelFunc=self.Cancel)
        self.corpid = attributes.get('corpid')
        self.corporation = attributes.get('corporation')
        wndCaption = localization.GetByLabel('UI/Corporations/BaseCorporationUI/JoinCorporation')
        self.SetCaption(wndCaption)
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        self.ConstructLayout()

    def ConstructLayout(self):
        corpName = cfg.eveowners.Get(self.corpid).name
        corpInfoCont = uicls.Container(name='corpInfo', parent=self.sr.main, align=uiconst.TOTOP, height=68, padding=const.defaultPadding)
        corpLogoCont = uicls.Container(name='corpLogo', parent=corpInfoCont, align=uiconst.TOLEFT, width=68)
        corpTextCont = uicls.Container(name='corpName', parent=corpInfoCont, align=uiconst.TOALL)
        applicationCont = uicls.Container(name='corpInfo', parent=self.sr.main, align=uiconst.TOALL, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding))
        uiutil.GetOwnerLogo(corpLogoCont, self.corpid, size=64, noServerCall=True)
        corpText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/ApplyForMembership', corporation=corpName)
        corpNameLabel = uicls.EveLabelLarge(parent=corpTextCont, text=corpText, top=12, align=uiconst.TOPLEFT, width=270)
        editText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/CorporationApplicationText')
        editLabel = uicls.EveLabelSmall(parent=applicationCont, text=editText, align=uiconst.TOTOP)
        tax = self.corporation.taxRate * 100
        taxText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/CurrentTaxRateForCorporation', corporation=corpName, taxRate=tax)
        taxLabel = uicls.EveLabelSmall(parent=applicationCont, text=taxText, align=uiconst.TOBOTTOM)
        if self.corporation and not self.corporation.isRecruiting:
            notRecruitingText = localization.GetByLabel('UI/Corporations/BaseCorporationUI/RecruitmentMayBeClosed')
            notRecruiting = uicls.EveLabelSmall(parent=applicationCont, text=notRecruitingText, align=uiconst.TOBOTTOM, idx=0)
            self.SetMinSize((self.default_width, self.default_height + notRecruiting.textheight), refresh=True)
        self.applicationText = uicls.EditPlainText(setvalue='', parent=applicationCont, align=uiconst.TOALL, maxLength=1000)

    def Confirm(self, *args):
        applicationText = self.applicationText.GetValue()
        if len(applicationText) > const.crpApplicationMaxSize:
            error = localization.GetByLabel('UI/Corporations/BaseCorporationUI/ApplicationTextTooLong', length=len(applicationText))
            eve.Message('CustomInfo', {'info': error})
        else:
            self.result = applicationText
            self.SetModalResult(1)

    def Cancel(self, *args):
        self.result = None
        self.SetModalResult(0)


class CorpApplicationEntry(uicls.SE_BaseClassCore):
    __guid__ = 'listentry.CorpApplicationEntry'
    __notifyevents__ = []
    LOGOPADDING = 70
    TEXTPADDING = 18
    CORPNAMEPAD = (LOGOPADDING,
     0,
     0,
     0)
    EXTENDEDPAD = (LOGOPADDING,
     const.defaultPadding,
     const.defaultPadding,
     const.defaultPadding)
    CORPNAMECLASS = uicls.EveLabelLarge
    EXTENDEDCLASS = uicls.EveLabelMedium
    APPHEADERHEIGHT = 53

    def PreLoad(node):
        application = node.application

    def Startup(self, *args):
        node = self.sr.node
        self.corpSvc = sm.GetService('corp')
        self.lscSvc = sm.GetService('LSC')
        self.viewButton = None
        self.removeButton = None
        self.rejectButton = None
        self.acceptButton = None
        self.ownerID = None
        self.statusLabelDict = {const.crpApplicationAppliedByCharacter: localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationUnprocessed'),
         const.crpApplicationAcceptedByCorporation: localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationStatusInvited'),
         const.crpApplicationRejectedByCorporation: localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationStatusRejected'),
         const.crpApplicationAcceptedByCharacter: localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationStatusAccepted'),
         const.crpApplicationRejectedByCharacter: localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationStatusInvitationRejected'),
         const.crpApplicationWithdrawnByCharacter: localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationStatusWithdrawn')}
        underline = uicls.Line(parent=self, align=uiconst.TOBOTTOM, color=(1, 1, 1, 0.05))
        if node.myView:
            self.ownerID = node.application.corporationID
        else:
            self.ownerID = node.application.characterID
        self.entryContainer = uicls.Container(parent=self)
        self.headerContainer = uicls.Container(parent=self.entryContainer, align=uiconst.TOTOP, name='applicationHeaderContainer', height=self.APPHEADERHEIGHT)
        self.expander = uicls.Sprite(parent=self.headerContainer, state=uiconst.UI_DISABLED, name='expander', pos=(0, 0, 16, 16), texturePath='res:/UI/Texture/Shared/getMenuIcon.png', align=uiconst.CENTERLEFT)
        if node.isExpanded:
            self.expander.rotation = -pi * 0.5
        logoParent = uicls.Container(parent=self.headerContainer, align=uiconst.TOPLEFT, pos=(16, 2, 48, 48))
        uiutil.GetOwnerLogo(logoParent, self.ownerID, size=48, noServerCall=True)
        logoParent.children[0].OnMouseEnter = self.OnMouseEnter
        logoParent.children[0].OnClick = self.ShowOwnerInfo
        self.nameLabel = self.CORPNAMECLASS(parent=self.headerContainer, name='nameLabel', state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, padding=self.CORPNAMEPAD)
        self.expandedParent = uicls.Container(parent=self.entryContainer, name='expandedParent', height=0)
        self.expandedLabel = self.EXTENDEDCLASS(parent=self.expandedParent, name='applicationText', text=node.application.applicationText, padding=self.EXTENDEDPAD, align=uiconst.TOALL)
        self.hilite = uicls.Fill(bgParent=self.headerContainer, color=(1, 1, 1, 0))
        uicls.Fill(bgParent=self.expandedParent, color=(0, 0, 0, 0.2))

    def Load(self, node):
        ownerName = cfg.eveowners.Get(self.ownerID).ownerName
        applicationDate = localization.GetByLabel('UI/Corporations/Applications/ApplicationDate', applicationDateTime=node.application.applicationDateTime)
        statusText = '<fontsize=12>%s</fontsize>' % self.statusLabelDict[node.application.status]
        nameStatusAndDate = '<b>%s - %s</b><br>%s' % (ownerName, statusText, applicationDate)
        self.nameLabel.text = nameStatusAndDate
        addPadding = const.defaultPadding
        if node.myView:
            if node.application.status not in const.crpApplicationEndStatuses:
                if self.removeButton is not None and not self.removeButton.destroyed:
                    self.removeButton.left = addPadding
                else:
                    self.removeButton = uicls.Button(name='removeButton', parent=self.headerContainer, label=localization.GetByLabel('UI/Corporations/CorpApplications/WithdrawApplication'), align=uiconst.BOTTOMRIGHT, left=addPadding, top=const.defaultPadding, func=self.WithdrawMyApplication, state=uiconst.UI_HIDDEN)
                addPadding += self.removeButton.width + const.defaultPadding
            elif self.removeButton is not None:
                self.removeButton.Close()
                self.removeButton = None
            if node.myView and node.application.status == const.crpApplicationAcceptedByCorporation:
                if self.acceptButton is not None and not self.acceptButton.destroyed:
                    self.acceptButton.left = addPadding
                else:
                    self.acceptButton = uicls.Button(name='acceptButton', parent=self.headerContainer, label=localization.GetByLabel('UI/Corporations/CorpApplications/AcceptApplication'), align=uiconst.BOTTOMRIGHT, left=addPadding, top=const.defaultPadding, state=uiconst.UI_HIDDEN, func=self.AcceptInvitation)
            elif self.acceptButton is not None:
                self.acceptButton.Close()
                self.acceptButton = None
        else:
            if node.application.status == const.crpApplicationAppliedByCharacter:
                if self.acceptButton is not None and not self.acceptButton.destroyed:
                    self.acceptButton.left = addPadding
                else:
                    self.acceptButton = uicls.Button(name='acceptButton', parent=self.headerContainer, label=localization.GetByLabel('UI/Corporations/CorpApplications/ApplicationInviteApplicant'), align=uiconst.BOTTOMRIGHT, left=addPadding, top=const.defaultPadding, state=uiconst.UI_HIDDEN, func=self.AcceptCorpApplication)
                addPadding += self.acceptButton.width + const.defaultPadding
            elif self.acceptButton is not None:
                self.acceptButton.Close()
                self.acceptButton = None
            if node.application.status not in const.crpApplicationEndStatuses:
                if self.rejectButton is not None and not self.rejectButton.destroyed:
                    self.rejectButton.left = addPadding
                else:
                    self.rejectButton = uicls.Button(name='rejectButton', parent=self.headerContainer, label=localization.GetByLabel('UI/Corporations/CorpApplications/RejectApplication'), align=uiconst.BOTTOMRIGHT, left=addPadding, top=const.defaultPadding, state=uiconst.UI_HIDDEN, func=self.RejectCorpApplication)
            elif self.rejectButton is not None:
                self.rejectButton.Close()
                self.rejectButton = None
        if node.fadeSize is not None:
            toHeight, fromHeight = node.fadeSize
            self.expandedParent.opacity = 0.0
            uicore.animations.MorphScalar(self, 'height', startVal=fromHeight, endVal=toHeight, duration=0.3)
            uicore.animations.FadeIn(self.expandedParent, duration=0.3)
        node.fadeSize = None
        if node.isExpanded:
            self.expandedParent.display = True
            self.expandedLabel.text = node.application.applicationText.strip()
            rotValue = -pi * 0.5
        else:
            rotValue = 0.0
            self.expandedParent.display = False
        uicore.animations.MorphScalar(self.expander, 'rotation', self.expander.rotation, rotValue, duration=0.15)

    def OnClick(self):
        node = self.sr.node
        reloadNodes = [node]
        if node.isExpanded:
            uicore.animations.Tr2DRotateTo(self.expander, -pi * 0.5, 0.0, duration=0.15)
            node.isExpanded = False
            allNodes = settings.char.ui.Get('corporation_applications_expanded', {})
            allNodes[node.myView] = None
            settings.char.ui.Set('corporation_applications_expanded', allNodes)
        else:
            for otherNode in node.scroll.sr.nodes:
                if otherNode.isExpanded and otherNode != node:
                    otherNode.isExpanded = False
                    reloadNodes.append(otherNode)

            uicore.animations.Tr2DRotateTo(self.expander, 0.0, -pi * 0.5, duration=0.15)
            node.isExpanded = True
            node.fadeSize = (listentry.CorpApplicationEntry.GetDynamicHeight(node, self.width), self.height)
            allNodes = settings.char.ui.Get('corporation_applications_expanded', {})
            allNodes[node.myView] = node.application.applicationID
            settings.char.ui.Set('corporation_applications_expanded', allNodes)
        self.sr.node.scroll.ReloadNodes(reloadNodes, updateHeight=True)

    def GetMenu(self):
        node = self.sr.node
        menu = [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowOwnerInfo)]
        if node.myView:
            if node.application.status not in const.crpApplicationEndStatuses:
                menu.append((uiutil.MenuLabel('UI/Corporations/CorpApplications/WithdrawApplication'), self.WithdrawMyApplication))
            if node.application.status == const.crpApplicationAcceptedByCorporation:
                menu.append((uiutil.MenuLabel('UI/Corporations/CorpApplications/AcceptApplication'), self.AcceptInvitation))
        elif const.corpRolePersonnelManager & session.corprole == const.corpRolePersonnelManager:
            if node.application.status == const.crpApplicationAppliedByCharacter:
                menu.append((uiutil.MenuLabel('UI/Corporations/CorpApplications/ApplicationInviteApplicant'), self.AcceptCorpApplication))
            if node.application.status not in const.crpApplicationEndStatuses:
                menu.append((uiutil.MenuLabel('UI/Corporations/CorpApplications/RejectApplication'), self.RejectCorpApplication))
        return menu

    def GetDynamicHeight(node, width):
        entryClass = listentry.CorpApplicationEntry
        if node.isExpanded:
            lp, tp, rp, bp = entryClass.EXTENDEDPAD
            textWidth, textHeight = entryClass.EXTENDEDCLASS.MeasureTextSize(node.application.applicationText, width=width - (lp + rp))
            textHeight = textHeight + entryClass.APPHEADERHEIGHT + tp + bp
            return textHeight
        else:
            return entryClass.APPHEADERHEIGHT

    def ShowOwnerInfo(self):
        owner = cfg.eveowners.Get(self.ownerID)
        sm.GetService('info').ShowInfo(owner.typeID, owner.ownerID)

    def OnMouseEnter(self, *args):
        uicore.animations.FadeIn(self.hilite, 0.05, duration=0.1)
        self.ShowButtons()
        self.hiliteTimer = base.AutoTimer(1, self._CheckIfStillHilited)

    def _CheckIfStillHilited(self):
        if uiutil.IsUnder(uicore.uilib.mouseOver, self) or uicore.uilib.mouseOver is self:
            return
        uicore.animations.FadeOut(self.hilite, duration=0.3)
        self.hiliteTimer = None
        for each in (self.removeButton, self.acceptButton, self.rejectButton):
            if each is not None and each.display:
                uicore.animations.FadeTo(each, each.opacity, 0.0, duration=0.1, callback=self.HideButtons)

    def HideButtons(self):
        for each in (self.removeButton, self.acceptButton, self.rejectButton):
            if each is not None:
                each.display = False

    def ShowButtons(self):
        for each in (self.removeButton, self.acceptButton, self.rejectButton):
            if each is not None:
                each.display = True
                uicore.animations.FadeTo(each, each.opacity, 1.0, duration=0.3)

    def AcceptInvitation(self, *args):
        try:
            sm.GetService('corpui').ShowLoad()
            application = self.sr.node.application
            sm.GetService('corp').UpdateApplicationOffer(application.applicationID, application.characterID, application.corporationID, application.applicationText, const.crpApplicationAcceptedByCharacter)
        finally:
            sm.GetService('corpui').HideLoad()
            uicls.Window.CloseIfOpen(windowID='viewApplicationWindow')

    def WithdrawMyApplication(self, *args):
        try:
            sm.GetService('corpui').ShowLoad()
            application = self.sr.node.application
            sm.GetService('corp').UpdateApplicationOffer(application.applicationID, application.characterID, application.corporationID, application.applicationText, const.crpApplicationWithdrawnByCharacter)
        finally:
            sm.GetService('corpui').HideLoad()
            uicls.Window.CloseIfOpen(windowID='viewApplicationWindow')

    def AcceptCorpApplication(self, *args):
        try:
            sm.GetService('corpui').ShowLoad()
            application = self.sr.node.application
            sm.GetService('corp').UpdateApplicationOffer(application.applicationID, application.characterID, application.corporationID, application.applicationText, const.crpApplicationAcceptedByCorporation)
        finally:
            sm.GetService('corpui').HideLoad()
            uicls.Window.CloseIfOpen(windowID='viewApplicationWindow')

    def RejectCorpApplication(self, *args):
        try:
            sm.GetService('corpui').ShowLoad()
            application = self.sr.node.application
            sm.GetService('corp').UpdateApplicationOffer(application.applicationID, application.characterID, application.corporationID, application.applicationText, const.crpApplicationRejectedByCorporation)
        finally:
            sm.GetService('corpui').HideLoad()
            uicls.Window.CloseIfOpen(windowID='viewApplicationWindow')