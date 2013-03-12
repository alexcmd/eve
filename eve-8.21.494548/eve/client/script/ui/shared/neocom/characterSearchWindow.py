#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/neocom/characterSearchWindow.py
import uicls
import uiconst
import localization
import uix
import uiutil
import copy
import util
import types

class CharacterSearchWindow(uicls.Window):
    __guid__ = 'form.CharacterSearchWindow'
    __notifyevents__ = ['OnContactChange',
     'OnContactNoLongerContact',
     'OnSearcedUserRemoved',
     'OnSearcedUserAdded']
    default_windowID = 'characterSearchWindow'

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        actionBtns = attributes.actionBtns or []
        caption = attributes.caption or ''
        inpt = attributes.input or ''
        showContactList = attributes.get('showContactList', False)
        extraIconHintFlag = attributes.extraIconHintFlag or None
        configname = attributes.configname or ''
        self.contactsLoaded = 0
        self.selecting = 0
        self.result = None
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.MakeUnMinimizable()
        self.SetMinSize([200, 240])
        self.width = 200
        self.height = 240
        self.SetCaption(caption)
        self.showContactList = showContactList
        self.extraIconHintFlag = extraIconHintFlag
        self.configname = configname
        self.sr.hintCont = uicls.Container(name='hintCont', parent=self.sr.main, align=uiconst.TOTOP, pos=(0, 0, 0, 16), state=uiconst.UI_HIDDEN)
        searchParent = self.sr.main
        if showContactList:
            self.sr.searchCont = uicls.Container(name='searchCont', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0))
            self.sr.scroll = uicls.Scroll(name='searchScroll', parent=self.sr.searchCont, padding=(const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding))
            self.sr.scroll.OnSelectionChange = self.RefreshSelection
            self.sr.contactsScroll = uicls.Scroll(name='contactsScroll', parent=self.sr.main, padding=(const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding))
            self.sr.contactsScroll.OnSelectionChange = self.RefreshSelection
            self.sr.tabs = uicls.TabGroup(name='tabs', parent=self.sr.main, tabs=[[localization.GetByLabel('UI/Mail/Search'),
              self.sr.searchCont,
              self,
              'search'], [localization.GetByLabel('UI/Mail/AllContacts'),
              self.sr.contactsScroll,
              self,
              'contacts']], groupID='calenderEvent_tabs', autoselecttab=1, idx=0)
            searchParent = self.sr.searchCont
        else:
            self.sr.scroll = uicls.Scroll(parent=self.sr.main, padding=(const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding))
            self.sr.scroll.OnSelectionChange = self.RefreshSelection
        self.currentScroll = self.sr.scroll
        searchCont = uicls.Container(name='searchCont', parent=searchParent, align=uiconst.TOTOP, pos=(0, 0, 0, 28), idx=0)
        searchByCont = uicls.Container(name='searchByCont', parent=searchParent, align=uiconst.TOTOP, pos=(0, 0, 0, 25), idx=0)
        searchBtnCont = uicls.Container(name='searchBtnCont', parent=searchCont, align=uiconst.TORIGHT, pos=(0, 0, 40, 0))
        inputCont = uicls.Container(name='inputCont', parent=searchCont, align=uiconst.TOALL, padLeft=5)
        searchByChoices = [[localization.GetByLabel('UI/Search/UniversalSearch/PartialTerms'), const.searchByPartialTerms],
         [localization.GetByLabel('UI/Search/UniversalSearch/ExactTerms'), const.searchByExactTerms],
         [localization.GetByLabel('UI/Search/UniversalSearch/ExactPhrase'), const.searchByExactPhrase],
         [localization.GetByLabel('UI/Search/UniversalSearch/OnlyExactPhrase'), const.searchByOnlyExactPhrase]]
        self.sr.searchBy = uicls.Combo(label=localization.GetByLabel('UI/Common/SearchBy'), parent=searchByCont, options=searchByChoices, name='ownerSearchSearchBy', select=settings.user.ui.Get('ownersSearchBy', const.searchByPartialTerms), width=170, left=10, top=5, labelleft=65, callback=self.ChangeSearchBy)
        self.sr.inpt = inpt = uicls.SinglelineEdit(name='input', parent=inputCont, maxLength=50, pos=(10, 5, 86, 0), label='', setvalue=inpt, align=uiconst.TOTOP)
        self.sr.searchBtn = uicls.Button(parent=searchBtnCont, label=localization.GetByLabel('UI/Mail/Search'), pos=(4,
         inpt.top,
         0,
         0), func=self.Search, btn_default=1)
        searchBtnCont.width = self.sr.searchBtn.width + 8
        btns = []
        self.dblClickFunc = None
        for each in actionBtns:
            text, func, dblClickFunc = each
            btns.append([text,
             func,
             lambda : self.GetSelectedInCurrentScroll(),
             None])
            if dblClickFunc:
                self.dblClickFunc = func

        self.sr.btns = uicls.ButtonGroup(btns=btns, parent=self.sr.main, idx=0)
        self.sr.btns.state = uiconst.UI_HIDDEN
        self.sr.scroll.Load(contentList=[], headers=[], noContentHint=localization.GetByLabel('UI/Common/TypeInSearch'))

    def ChangeSearchBy(self, entry, header, value, *args):
        settings.user.ui.Set('ownersSearchBy', value)

    def GetSelectedInCurrentScroll(self, *args):
        return self.currentScroll.GetSelected()

    def Load(self, key, *args):
        if not self or self.destroyed:
            return
        if key == 'contacts':
            if not self.contactsLoaded:
                self.LoadContacts()
                self.contactsLoaded = 1
            self.currentScroll = self.sr.contactsScroll
        elif key == 'search':
            self.currentScroll = self.sr.scroll
        self.RefreshSelection()

    def RefreshSelection(self, *args):
        sel = self.currentScroll.GetSelected()
        if len(sel) < 1:
            self.sr.btns.state = uiconst.UI_HIDDEN
            return
        self.sr.btns.state = uiconst.UI_PICKCHILDREN

    def DblClickEntry(self, entry, ignoreConfirm = False, *args):
        if ignoreConfirm or entry.confirmOnDblClick:
            self.currentScroll.SelectNode(entry.sr.node)
            if self.dblClickFunc is not None:
                apply(self.dblClickFunc, (self.currentScroll.GetSelected,))

    def ClickEntry(self, *args):
        self.RefreshSelection()

    def ExtraMenuFunction(self, *args):
        return []

    def Search(self, *args):
        inpt = self.sr.inpt.GetValue()
        if inpt.strip() == '':
            self.sr.scroll.Load(contentList=[], headers=[], noContentHint=localization.GetByLabel('UI/Common/TypeInSearch'))
            return
        hint = ''
        searchBy = settings.user.ui.Get('ownersSearchBy', const.searchByPartialTerms)
        lst = uix.Search(inpt, const.groupCharacter, getWindow=0, hideNPC=1, notifyOneMatch=1, modal=0, getError=1, exact=searchBy)
        if type(lst) != list:
            lst = [lst]
        if len(lst) >= 500:
            hint = localization.GetByLabel('UI/Mail/25OrMoreFound', name=inpt)
        try:
            scrolllist = self.GetUserEntries(lst)
            extraEntries = self.GetExtraSearchEntries(inpt, searchBy)
            scrolllist = extraEntries + scrolllist
            noContentHint = localization.GetByLabel('UI/Market/NothingFoundWithSearch', search=inpt)
            self.sr.scroll.Load(contentList=scrolllist, headers=[], noContentHint=noContentHint)
            self.SetHint(hint)
            self.RefreshSelection()
        except:
            if not self or self.destroyed:
                return
            raise 

    def GetExtraSearchEntries(self, searchString, searchBy):
        return []

    def GetUserEntries(self, lst):
        scrolllist = []
        for info in lst:
            if type(info) in [types.StringType, types.UnicodeType]:
                continue
            entryTuple = self.GetUserEntryTuple(info[1])
            scrolllist.append(entryTuple)

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        return scrolllist

    def SetHint(self, hint):
        hp = self.sr.hintCont
        uix.Flush(hp)
        if hint:
            t = uicls.EveLabelMedium(text=hint, parent=hp, top=-3, align=uiconst.CENTER, width=self.minsize[0] - 32, state=uiconst.UI_DISABLED)
            hp.state = uiconst.UI_DISABLED
            hp.height = t.height + 4
        else:
            hp.state = uiconst.UI_HIDDEN

    def LoadContacts(self, *args):
        allContacts = sm.GetService('addressbook').GetContacts()
        contacts = allContacts.contacts.values()
        scrolllist = []
        for contact in contacts:
            if util.IsNPC(contact.contactID) or not util.IsCharacter(contact.contactID):
                continue
            entryTuple = self.GetUserEntryTuple(contact.contactID, contact)
            scrolllist.append(entryTuple)

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        self.sr.contactsScroll.Load(contentList=scrolllist, headers=[], noContentHint=localization.GetByLabel('UI/AddressBook/NoContacts'))

    def GetUserEntryTuple(self, charID, contact = None, *args):
        if contact is None:
            contact = util.KeyVal(contactID=charID)
        extraIconHintFlag = copy.copy(self.extraIconHintFlag)
        if extraIconHintFlag and self.IsAdded(charID):
            extraIconHintFlag[-1] = True
        extraInfo = util.KeyVal(extraIconHintFlag=extraIconHintFlag, wndConfigname=self.configname)
        entryTuple = sm.GetService('addressbook').GetContactEntry(None, contact, dblClick=self.DblClickContact, menuFunction=self.ExtraMenuFunction, extraInfo=extraInfo, listentryType='SearchedUser')
        return entryTuple

    def IsAdded(self, contactID, *args):
        return False

    def DblClickContact(self, entry, *args):
        self.DblClickEntry(entry, ignoreConfirm=True)

    def OnContactChange(self, contactIDs, contactType):
        if contactType == 'contact':
            self.ReloadContactList()

    def OnContactNoLongerContact(self, charID):
        self.ReloadContactList()

    def ReloadContactList(self, *args):
        if self.showContactList and self.contactsLoaded:
            self.LoadContacts()

    def OnSearcedUserAdded(self, charID, configname, *args):
        self.MarkEntriesAddedOrRemoved(configname, [charID], isAdded=1)

    def OnSearcedUserRemoved(self, charIDs, configname, *args):
        self.MarkEntriesAddedOrRemoved(configname, charIDs, isAdded=0)

    def MarkEntriesAddedOrRemoved(self, configname, charIDs, isAdded = 0, *args):
        if self.configname != configname:
            return
        if len(charIDs) < 1:
            return
        scrolls = []
        for scrollName in ['scroll', 'contactsScroll']:
            scroll = self.sr.Get(scrollName, None)
            if scroll is not None:
                scrolls.append(scroll)

        for scroll in scrolls:
            ids = charIDs[:]
            for entry in scroll.GetNodes():
                if entry.charID in ids:
                    ids.remove(entry.charID)
                    entry.isAdded = isAdded
                    if entry.panel:
                        entry.panel.SearcedUserAddedOrRemoved(entry.isAdded)
                    if len(ids) < 1:
                        break