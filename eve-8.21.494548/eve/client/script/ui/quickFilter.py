#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/quickFilter.py
import blue
import localization
import uicls
import uiconst
import uthread

class QuickFilterEdit(uicls.SinglelineEdit):
    __guid__ = 'uicls.QuickFilterEdit'
    default_width = 100
    default_left = 0
    default_top = 0

    def ApplyAttributes(self, attributes):
        attributes.hinttext = attributes.hinttext or localization.GetByLabel('UI/Inventory/Filter')
        attributes.maxLength = attributes.maxLength or 37
        uicls.SinglelineEdit.ApplyAttributes(self, attributes)
        self.ShowClearButton(hint=localization.GetByLabel('UI/Calendar/Hints/Clear'))
        self.RefreshTextClipper()
        self.filterThread = None
        self.lastStrFilter = None
        self.quickFilterInput = None
        self.OnChange = self.SetQuickFilterInput
        self.OnReturn = self.RegisterInput
        self.OnFocusLost = self.RegisterInput
        self.OnClearFilter = attributes.OnClearFilter
        self.SetQuickFilterInput()

    def OnClearButtonClick(self, *args, **kwds):
        uicls.SinglelineEdit.OnClearButtonClick(self, *args, **kwds)
        if self.OnClearFilter:
            self.OnClearFilter()

    def GetValue(self, *args, **kwds):
        return uicls.SinglelineEdit.GetValue(self, registerHistory=False)

    def ClearInput(self, *args, **kwds):
        uicls.SinglelineEdit.ClearInput(self, *args, **kwds)
        self.ReloadFunction()

    def RegisterInput(self, *args, **kwds):
        self.RegisterHistory()
        self.DoReload()

    def SetQuickFilterInput(self, *args):
        if self.filterThread is not None:
            self.filterThread.kill()
        self.filterThread = uthread.new(self._SetQuickFilterInput)

    def _SetQuickFilterInput(self):
        try:
            blue.pyos.synchro.Sleep(400)
        finally:
            self.filterThread = None

        self.DoReload()

    def DoReload(self):
        strFilter = self.GetValue()
        if self.lastStrFilter == strFilter:
            return
        self.lastStrFilter = strFilter
        if len(strFilter) > 0:
            self.quickFilterInput = strFilter.lower()
            self.ReloadFunction()
        else:
            prefilter = self.quickFilterInput
            self.quickFilterInput = None
            if prefilter != None:
                self.ReloadFunction()

    def ReloadFunction(self, *args):
        pass

    def QuickFilter(self, rec):
        if not self.quickFilterInput:
            return False
        name = ''
        if hasattr(rec, 'name'):
            name = rec.name.lower()
        elif hasattr(rec, 'contactID'):
            name = cfg.eveowners.Get(rec.contactID).name
            name = name.lower()
        elif hasattr(rec, 'invtype'):
            name = rec.invtype.typeName.lower()
        input = self.quickFilterInput.lower()
        return name.find(input) + 1