#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/killRights.py
import listentry
import uiconst
import const
import uicls
import localization
import uix
import localizationUtil
import log
import blue
import uthread
import uiutil
import moniker
import form
import searchUtil
import util
from service import ROLE_PROGRAMMER

class KillRightsEntry(listentry.Generic):
    __guid__ = 'listentry.KillRightsEntry'
    __notifyevents__ = ['OnContactLoggedOn',
     'OnContactLoggedOff',
     'OnContactNoLongerContact',
     'OnContactChange',
     'OnBlockContacts',
     'OnUnblockContacts']

    def Startup(self, *args):
        listentry.Generic.Startup(self, *args)
        sm.RegisterNotify(self)
        self.sr.line.display = False
        self.portraitCont = uicls.Container(name='portraitCont', parent=self, align=uiconst.TOLEFT, width=64)
        self.utilMenuCont = uicls.Container(name='utilMenuCont', parent=self, align=uiconst.TORIGHT, width=28)
        self.utilMenuCont.display = False
        myTextCont = uicls.Container(name='myTextCont', parent=self, align=uiconst.TOALL, padLeft=2 * const.defaultPadding, clipChildren=True)
        self.textCont = uicls.ContainerAutoSize(name='textCont', parent=myTextCont, align=uiconst.CENTERLEFT)
        self.nameLabel = uicls.EveLabelMedium(text='', parent=self.textCont, maxLines=1, align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        self.saleLabel = uicls.EveLabelSmall(text='', parent=self.textCont, maxLines=1, align=uiconst.TOPLEFT, top=19, state=uiconst.UI_NORMAL)
        self.availableLabel = uicls.EveLabelSmall(text='', parent=self.textCont, maxLines=1, align=uiconst.TOPLEFT, top=32, state=uiconst.UI_NORMAL)

    def Load(self, node):
        listentry.Generic.Load(self, node)
        self.portraitCont.Flush()
        self.utilMenuCont.Flush()
        data = self.data = node
        charID = self.charID = data.charID
        killRight = data.killRight
        self.killRightID = killRight.killRightID
        self.price = killRight.price
        self.restrictedTo = killRight.restrictedTo
        isMine = data.isMine
        self.inWatchlist = sm.GetService('addressbook').IsInWatchlist(charID)
        charName = cfg.eveowners.Get(charID).name
        self.nameText = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=charName, info=('showinfo', const.typeCharacterAmarr, charID))
        portrait = uicls.Sprite(parent=self.portraitCont, align=uiconst.TOPRIGHT, pos=(0, 2, 64, 64), state=uiconst.UI_PICKCHILDREN)
        sm.GetService('photo').GetPortrait(charID, 64, portrait)
        self.SetRelationship(data)
        self.statusIcon = uicls.Sprite(parent=self.portraitCont, name='statusIcon', pos=(2, 3, 10, 10), state=uiconst.UI_NORMAL, texturePath='res:/UI/Texture/classes/Chat/Status.png', idx=0)
        if not self.inWatchlist:
            self.statusIcon.display = False
        else:
            self.statusIcon.display = False
            online = sm.GetService('onlineStatus').GetOnlineStatus(charID, fetch=False)
            self.SetOnline(online)
        uthread.new(self.SetTimeRemaining)
        if self.price is not None:
            self.saleLabel.display = True
            self.availableLabel.display = True
            saleText, availableText = self.GetForSaleText()
            if self.price > 0:
                self.saleLabel.text = saleText
            else:
                self.availableLabel.top = 19
            self.availableLabel.text = availableText
        else:
            self.saleLabel.display = False
            self.availableLabel.display = False
        if isMine:
            self.utilMenuCont.display = True
            utilMenu = uicls.UtilMenu(menuAlign=uiconst.TOPRIGHT, parent=self.utilMenuCont, align=uiconst.CENTERRIGHT, GetUtilMenu=self.SellKillRight, texturePath='res:/UI/Texture/Icons/73_16_50.png', left=2)

    def SellKillRight(self, menuParent):
        if self.price is None:
            menuParent.AddIconEntry(icon='res:/UI/Texture/Icons/KillRightsIcon.png', text=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SellToPublic'), callback=(self.OpenSellKillRightWindow, 'open'))
            menuParent.AddIconEntry(icon='res:/UI/Texture/Icons/KillRightsIcon.png', text=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SellToMyCorporation'), callback=(self.OpenSellKillRightWindow, session.corpid))
            if session.allianceid:
                menuParent.AddIconEntry(icon='res:/UI/Texture/Icons/KillRightsIcon.png', text=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SellToMyAlliance'), callback=(self.OpenSellKillRightWindow, session.allianceid))
            menuParent.AddIconEntry(icon='res:/UI/Texture/Icons/KillRightsIcon.png', text=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SellToSpecific'), callback=(self.OpenSellKillRightWindow, None))
        else:
            menuParent.AddIconEntry(icon='res:/UI/Texture/Icons/KillRightsIcon.png', text=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/MakeUnavailable'), callback=self.MakeUnavailable)

    def MakeUnavailable(self, *args):
        if self.restrictedTo is None:
            questionLabel = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/MakeUnavailableQuestionAll')
        else:
            entityName = cfg.eveowners.Get(self.restrictedTo).name
            questionLabel = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/MakeUnavailableQuestion', entityName=entityName)
        ret = eve.Message('CustomQuestion', {'header': localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/MakeUnavailable'),
         'question': questionLabel}, uiconst.YESNO)
        if ret != uiconst.ID_YES:
            return
        sm.GetService('bountySvc').CancelSellKillRight(self.killRightID, self.charID)

    def OpenSellKillRightWindow(self, sellToID):
        form.SellKillRightWnd.CloseIfOpen()
        form.SellKillRightWnd.Open(sellToID=sellToID, killRightID=self.killRightID)

    def SetTimeRemaining(self):
        while self and not self.destroyed:
            timeEnd = self.data.expiryTime
            timeLeft = timeEnd - blue.os.GetWallclockTime()
            if timeLeft < 0:
                timeLeftText = ''
                sm.ScatterEvent('OnKillRightExpired', self.killRightID)
            else:
                timeLeftText = localizationUtil.FormatTimeIntervalShortWritten(long(timeLeft), showFrom='day', showTo='minute')
            self.nameLabel.text = self.nameText + ' ' + localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/TimeRemaining', timeRemaining=timeLeftText)
            blue.pyos.synchro.SleepWallclock(60000)

    def GetForSaleText(self):
        amount = util.FmtISK(self.price, 0)
        saleText = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/ForSale', amount=amount)
        if self.restrictedTo is None:
            availableText = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/AvailableToAll')
        else:
            entityName = cfg.eveowners.Get(self.restrictedTo).name
            entityType = cfg.eveowners.Get(self.restrictedTo).typeID
            entityText = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=entityName, info=('showinfo', entityType, self.restrictedTo))
            if util.IsCorporation(self.restrictedTo) and not util.IsNPC(self.restrictedTo):
                corpInfo = sm.RemoteSvc('corpmgr').GetPublicInfo(self.restrictedTo)
                allianceID = corpInfo.allianceID
                if allianceID:
                    allianceName = cfg.allianceshortnames.Get(allianceID).shortName
                    allianceType = const.typeAlliance
                    allianceText = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=allianceName, info=('showinfo', allianceType, allianceID))
                    entityText += ' [%s]' % allianceText
            availableText = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/AvailableToSpecific', entityName=entityText)
        return (saleText, availableText)

    def SetOnline(self, online):
        if online is None or not self.inWatchlist:
            self.statusIcon.display = False
        else:
            self.statusIcon.SetRGB(float(not online) * 0.75, float(online) * 0.75, 0.0)
            if online:
                self.statusIcon.hint = localization.GetByLabel('UI/Common/Online')
            else:
                self.statusIcon.hint = localization.GetByLabel('UI/Common/Offline')
            self.statusIcon.display = True

    def SetRelationship(self, data):
        uix.SetStateFlag(self.portraitCont, data, top=54, left=52)

    def SetBlocked(self, blocked):
        isBlocked = sm.GetService('addressbook').IsBlocked(self.charID)
        if blocked and isBlocked:
            self.statusIcon.SetTexturePath('res:/UI/Texture/classes/Chat/Blocked.png')
            self.statusIcon.display = True
        elif self.inWatchlist:
            self.statusIcon.SetTexturePath('res:/UI/Texture/classes/Chat/Status.png')
            self.statusIcon.display = True
        else:
            self.statusIcon.display = False

    def OnContactLoggedOn(self, charID):
        if charID == self.charID:
            self.SetOnline(1)

    def OnContactLoggedOff(self, charID):
        if charID == self.charID:
            self.SetOnline(0)

    def OnContactNoLongerContact(self, charID):
        if charID == self.charID:
            self.SetOnline(None)

    def OnContactChange(self, contactIDs, contactType = None):
        if self.destroyed:
            return
        self.SetRelationship(self.data)
        if self.charID in contactIDs:
            self.inWatchlist = sm.GetService('addressbook').IsInWatchlist(self.charID)
            if not self.inWatchlist:
                isBlocked = sm.GetService('addressbook').IsBlocked(self.charID)
                if isBlocked:
                    self.statusIcon.display = True
                    self.statusIcon.SetRGB(1.0, 1.0, 1.0)
                else:
                    self.statusIcon.display = False
            else:
                self.statusIcon.display = True

    def OnBlockContacts(self, contactIDs):
        if self.charID in contactIDs:
            self.SetBlocked(1)

    def OnUnblockContacts(self, contactIDs):
        if self.charID in contactIDs:
            self.SetBlocked(0)

    def GetHeight(self, *args):
        node, width = args
        node.height = 68
        return node.height

    def GetMenu(self):
        m = []
        m = sm.GetService('menu').GetMenuFormItemIDTypeID(self.charID, const.typeCharacterAmarr)
        if m is not None and session.role & ROLE_PROGRAMMER == ROLE_PROGRAMMER:
            m.append(('PROG: Activate KillRight', self.ActivateKillRight))
        return m

    def OnDblClick(self, *args):
        sm.GetService('info').ShowInfo(const.typeCharacterAmarr, self.charID)

    def OnMouseEnter(self, *args):
        pass

    def OnMouseExit(self, *args):
        pass

    def OnClick(self, *args):
        pass

    def ActivateKillRight(self):
        sm.RemoteSvc('killRightMgr').ActivateKillRight(self.killRightID)


class SellKillRightWnd(uicls.Window):
    __guid__ = 'form.SellKillRightWnd'
    __notifyevents__ = []
    default_windowID = 'SellKillRightWnd'
    default_fixedWidth = 300
    default_fixedHeight = 106
    default_minSize = (default_fixedWidth, default_fixedHeight)

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.sellToID = attributes.get('sellToID', None)
        self.killRightID = attributes.get('killRightID', None)
        self.ownerID = None
        self.searchingKillRights = False
        self.SetTopparentHeight(0)
        self.SetCaption(localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SellKillRight'))
        self.ConstructLayout()

    def ConstructLayout(self):
        mainCont = uicls.Container(name='mainCont', parent=self.sr.main, padding=const.defaultPadding)
        headerText = uicls.EveLabelMedium(text=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Availability'), parent=mainCont, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, bold=True, padBottom=const.defaultPadding)
        self.searchCont = uicls.Container(name='searchCont', parent=mainCont, align=uiconst.TOTOP, height=30)
        self.verifiedCont = uicls.Container(name='verifiedCont', parent=mainCont, align=uiconst.TOTOP, height=30)
        self.verifiedCont.display = False
        imgCont = uicls.Container(name='imgCont', parent=self.searchCont, width=30, align=uiconst.TOLEFT)
        killerLogo = uicls.Sprite(parent=imgCont, align=uiconst.TOALL, idx=0, texturePath='res:/UI/Texture/silhouette_64.png')
        self.searchEdit = uicls.SinglelineEdit(name='searchEdit', parent=self.searchCont, maxLength=32, align=uiconst.TOALL, hinttext=localization.GetByLabel('UI/Station/BountyOffice/SearchForUser'), pos=(0, 0, 0, 0))
        self.searchEdit.OnReturn = self.SearchKillRights
        self.imgCont = uicls.Container(name='imgCont', parent=self.verifiedCont, width=30, align=uiconst.TOLEFT)
        clearCont = uicls.Container(name='clearCont', parent=self.verifiedCont, width=24, align=uiconst.TORIGHT)
        textCont = uicls.Container(name='textCont', parent=self.verifiedCont, align=uiconst.TOALL, padLeft=const.defaultPadding)
        self.killRightOwner = uicls.Sprite(parent=self.imgCont, align=uiconst.TOALL, idx=0, texturePath='res:/UI/Texture/silhouette_64.png')
        self.clearBtn = uicls.ButtonIcon(name='surrenderBtn', parent=clearCont, align=uiconst.CENTER, width=16, iconSize=16, texturePath='res:/UI/Texture/Icons/73_16_210.png', hint=localization.GetByLabel('UI/Inventory/Clear'), func=self.ClearKillRight)
        self.nameLabel = uicls.EveLabelMedium(name='bountyName', parent=textCont, align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL, maxLines=1)
        amountCont = uicls.Container(parent=mainCont, align=uiconst.TOBOTTOM, height=20)
        self.sellKillRightBtn = uicls.Button(parent=amountCont, label=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/SellKillRightBtn'), align=uiconst.TORIGHT, func=self.SellKillRight)
        self.killRightAmount = uicls.SinglelineEdit(name='sellEdit', parent=amountCont, align=uiconst.TOALL, width=0, floats=[0, const.MAX_BOUNTY_AMOUNT, 0], hinttext=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/EnterAmount'), padRight=const.defaultPadding, top=0)
        self.killRightAmount.OnReturn = self.SellKillRight
        if self.sellToID == 'open':
            self.searchCont.display = False
            openForPublicText = uicls.EveCaptionSmall(text=localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Everyone'), parent=mainCont, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, top=const.defaultPadding)
        elif self.sellToID is not None:
            self.ownerID = self.sellToID
            self.ShowResult(self.ownerID)

    def SellKillRight(self, *args):
        if not self.killRightID:
            return
        amount = self.killRightAmount.GetValue()
        try:
            sm.GetService('bountySvc').SellKillRight(self.killRightID, amount, self.ownerID)
        finally:
            sm.ScatterEvent('OnKillRightSold', self.killRightID)
            self.CloseByUser()

    def SearchKillRights(self, *args):
        if self.searchEdit.GetValue() == '':
            return
        if self.searchingKillRights:
            return
        if self.verifiedCont.display == True:
            return
        self.searchingKillRights = True
        self.ownerID = self.Search(self.searchEdit)
        self.searchingKillRights = False
        if self.ownerID:
            self.ShowResult(self.ownerID)

    def Search(self, edit):
        searchString = edit.GetValue()
        if not searchString or searchString == '':
            return None
        groupIDList = [const.searchResultCharacter, const.searchResultCorporation, const.searchResultAlliance]
        searchResult = searchUtil.QuickSearch(searchString.strip(), groupIDList, hideNPC=False)
        if not len(searchResult):
            edit.SetValue('')
            edit.SetHintText(localization.GetByLabel('UI/Station/BountyOffice/NoOneFound'))
        else:
            if len(searchResult) == 1:
                ownerID = searchResult[0]
                return ownerID
            dlg = form.BountyPicker.Open(resultList=searchResult)
            dlg.ShowModal()
            if dlg.ownerID:
                return dlg.ownerID
            edit.SetValue('')
            return None

    def ShowResult(self, ownerID):
        if ownerID:
            self.imgCont.Flush()
            self.verifiedCont.display = True
            self.sellKillRightBtn.Enable()
            self.searchCont.display = False
            ownerType = cfg.eveowners.Get(ownerID).typeID
            if util.IsCharacter(ownerID):
                ownerPortrait = uicls.Sprite(parent=self.imgCont, align=uiconst.TOALL, idx=0, texturePath='res:/UI/Texture/silhouette_64.png')
                sm.GetService('photo').GetPortrait(ownerID, 30, ownerPortrait)
            else:
                ownerPortrait = uiutil.GetLogoIcon(itemID=ownerID, parent=self.imgCont, acceptNone=False, align=uiconst.TOPRIGHT, height=30, width=30, state=uiconst.UI_NORMAL)
                ownerPortrait.SetSize(30, 30)
            ownerPortrait.OnClick = (self.ShowInfo, ownerID, ownerType)
            ownerName = cfg.eveowners.Get(ownerID).name
            self.killRightOwner.hint = ownerName
            self.nameLabel.text = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=ownerName, info=('showinfo', ownerType, ownerID))
            uicore.registry.SetFocus(self.killRightAmount)

    def ClearKillRight(self, *args):
        self.ownerID = None
        self.searchEdit.SetValue('')
        self.searchCont.display = True
        self.verifiedCont.display = False
        self.killRightAmount.SetValue('')
        self.killRightAmount.SetHintText(localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/EnterAmount'))
        self.sellKillRightBtn.Disable()

    def ShowInfo(self, ownerID, typeID, *args):
        sm.GetService('info').ShowInfo(typeID, ownerID)


class KillRightsUtilMenu(uicls.UtilMenu):
    __guid__ = 'uicls.KillRightsUtilMenu'
    default_menuAlign = uiconst.TOPRIGHT
    default_align = uiconst.BOTTOMRIGHT
    default_texturePath = 'res:/UI/Texture/Icons/KillRightsIcon.png'

    def ApplyAttributes(self, attributes):
        attributes.GetUtilMenu = self.ActivateKillRightMenu
        uicls.UtilMenu.ApplyAttributes(self, attributes)
        self.killRightID = attributes.get('killRightID', None)

    def ActivateKillRightMenu(self, menuParent):
        cont = menuParent.AddContainer(align=uiconst.TOTOP, padding=const.defaultPadding)
        cont.GetEntryWidth = lambda mc = cont: 230
        charName = cfg.eveowners.Get(self.charID).name
        charNamelabel = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=charName, info=('showinfo', const.typeCharacterAmarr, self.charID))
        if self.price is not None:
            headerText = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/BuyKillRight')
            explainText = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/PurchaseLabel', charName=charNamelabel)
            priceText = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/AcativationCost', costAmount=util.FmtISK(self.price, 0))
        else:
            headerText = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/ActivateKillRight')
            explainText = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/ActivateLabel', charName=charNamelabel)
            priceText = ''
        headerLabel = uicls.EveLabelLarge(text=headerText, parent=cont, align=uiconst.TOTOP, state=uiconst.UI_NORMAL, bold=True)
        helpTextCont = uicls.Container(name='helpTextCont', parent=cont, align=uiconst.TOTOP, height=40, padTop=const.defaultPadding)
        helpText = uicls.EveLabelMedium(text=explainText, parent=helpTextCont, state=uiconst.UI_NORMAL, align=uiconst.TOTOP, color=(1.0, 0.0, 0.0, 0.8))
        buttonCont = uicls.Container(name='buttonCont', parent=cont, align=uiconst.TOTOP, height=20)
        priceLabel = uicls.EveLabelMedium(text=priceText, parent=buttonCont)
        buttonLabel = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/Activate')
        if self.price is None:
            self.func = 'ActivateKillRight'
            self.params = (self.killRightID, self.charID, self.shipID)
        else:
            self.func = 'BuyKillRight'
            self.params = (self.killRightID,
             self.charID,
             self.shipID,
             self.price)
        self.activateBtn = uicls.Button(parent=buttonCont, label=buttonLabel, align=uiconst.TORIGHT, func=self.ActivateKillRight)

    def ActivateKillRight(self, *args):
        try:
            getattr(sm.GetService('bountySvc'), self.func)(*self.params)
        finally:
            self.CloseMenu()

    def UpdateKillRightInfo(self, killRightID, price, charID, shipID):
        self.killRightID = killRightID
        self.price = price
        self.charID = charID
        self.shipID = shipID
        if price is None:
            self.hint = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/ActivateKillRight')
        else:
            self.hint = localization.GetByLabel('UI/CharacterSheet/CharacterSheetWindow/BuyKillRight')