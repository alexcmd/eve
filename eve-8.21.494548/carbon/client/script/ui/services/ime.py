#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/services/ime.py
import service
import uthread
import trinity
import lg
import uicls
import uiconst
import uiutil
import browser
import localization
import blue
INDICATOR_NON_IME = 'En'
INDICATOR_CHS = unichr(31616)
INDICATOR_CHT = unichr(32321)
INDICATOR_KOREAN = unichr(44032)
INDICATOR_HIRAGANA = unichr(12354)
INDICATOR_KATAKANA = unichr(12459)
IMEID_CHT_VER42 = 67240964
IMEID_CHT_VER43 = 67306500
IMEID_CHT_VER44 = 67372036
IMEID_CHT_VER50 = 83887108
IMEID_CHT_VER51 = 83952644
IMEID_CHT_VER52 = 84018180
IMEID_CHT_VER60 = 100664324
IMEID_CHS_VER41 = 67176452
IMEID_CHS_VER42 = 67241988
IMEID_CHS_VER53 = 84084740
IMN_CHANGECANDIDATE = 3
IMN_CLOSECANDIDATE = 4
IMN_CLOSESTATUSWINDOW = 1
IMN_GUIDELINE = 13
IMN_OPENCANDIDATE = 5
IMN_OPENSTATUSWINDOW = 2
IMN_SETCANDIDATEPOS = 9
IMN_SETCOMPOSITIONFONT = 10
IMN_SETCOMPOSITIONWINDOW = 11
IMN_SETCONVERSIONMODE = 6
IMN_SETOPENSTATUS = 8
IMN_SETSENTENCEMODE = 7
IMN_SETSTATUSWINDOWPOS = 12
IMN_PRIVATE = 14
GCS_COMPATTR = 16
GCS_COMPCLAUSE = 32
GCS_COMPREADSTR = 1
GCS_COMPREADATTR = 2
GCS_COMPREADCLAUSE = 4
GCS_COMPSTR = 8
GCS_CURSORPOS = 128
GCS_DELTASTART = 256
GCS_RESULTCLAUSE = 4096
GCS_RESULTREADCLAUSE = 1024
GCS_RESULTREADSTR = 512
GCS_RESULTSTR = 2048
CS_INSERTCHAR = 8192
CS_NOMOVECARET = 16384
SCS_SETSTR = GCS_COMPREADSTR | GCS_COMPSTR
SCS_CHANGEATTR = GCS_COMPREADATTR | GCS_COMPATTR
SCS_CHANGECLAUSE = GCS_COMPREADCLAUSE | GCS_COMPCLAUSE
SCS_SETRECONVERTSTRING = 65536
SCS_QUERYRECONVERTSTRING = 131072
IME_CMODE_ALPHANUMERIC = 0
IME_CMODE_NATIVE = 1
IME_CMODE_KATAKANA = 2
IME_CMODE_LANGUAGE = 3
IME_CMODE_FULLSHAPE = 8
IME_CMODE_ROMAN = 16
IME_CMODE_CHARCODE = 32
IME_CMODE_HANJACONVERT = 64
IME_CMODE_SOFTKBD = 128
IME_CMODE_NOCONVERSION = 256
IME_CMODE_EUDC = 512
IME_CMODE_SYMBOL = 1024
IME_CMODE_FIXED = 2048
IME_SMODE_NONE = 0
IME_SMODE_PLAURALCLAUSE = 1
IME_SMODE_SINGLECONVERT = 2
IME_SMODE_AUTOMATIC = 4
IME_SMODE_PHRASEPREDICT = 8
IME_SMODE_CONVERSATION = 16
IME_SMODE_RESERVED = 61440
NI_OPENCANDIDATE = 16
NI_CLOSECANDIDATE = 17
NI_SELECTCANDIDATESTR = 18
NI_CHANGECANDIDATELIST = 19
NI_FINALIZECONVERSIONRESULT = 20
NI_COMPOSITIONSTR = 21
NI_SETCANDIDATE_PAGESTART = 22
NI_SETCANDIDATE_PAGESIZE = 23
NI_IMEMENUSELECTED = 24
CPS_COMPLETE = 1
CPS_CONVERT = 2
CPS_REVERT = 3
CPS_CANCEL = 4
IME_CHOTKEY_IME_NONIME_TOGGLE = 16
IME_CHOTKEY_SHAPE_TOGGLE = 17
IME_CHOTKEY_SYMBOL_TOGGLE = 18
IME_JHOTKEY_CLOSE_OPEN = 48
IME_KHOTKEY_SHAPE_TOGGLE = 80
IME_KHOTKEY_HANJACONVERT = 81
IME_KHOTKEY_ENGLISH = 82
IME_THOTKEY_IME_NONIME_TOGGLE = 112
IME_THOTKEY_SHAPE_TOGGLE = 113
IME_THOTKEY_SYMBOL_TOGGLE = 114
SUBLANG_CHINESE_TRADITIONAL = 1
SUBLANG_CHINESE_SIMPLIFIED = 2
LANG_CHINESE = 4
LANG_JAPANESE = 17
LANG_KOREAN = 18
LANG_CHS = 2052
IMM_ERROR_NODATA = -1
IMM_ERROR_GENERAL = -2

class IME(service.Service):
    __update_on_reload__ = 0
    __guid__ = 'svc.ime'
    __exportedcalls__ = {'GetIndicator': [],
     'SetFocus': [],
     'KillFocus': [],
     'SetDebug': [],
     'SimulateHotKey': [],
     'GetMenuDelegate': [],
     'GetKeyboardLanguageID': []}
    __notifyevents__ = ['OnSessionChanged']
    __startupdependencies__ = ['settings']
    localeIndicator = {'INDICATOR_NON_IME': INDICATOR_NON_IME,
     'INDICATOR_CHS': INDICATOR_CHS,
     'INDICATOR_CHT': INDICATOR_CHT,
     'INDICATOR_KOREAN': INDICATOR_KOREAN,
     'INDICATOR_HIRAGANA': INDICATOR_HIRAGANA,
     'INDICATOR_KATAKANA': INDICATOR_KATAKANA}
    primaryLanguages = {0: 'Aa',
     1: 'Ar',
     2: 'Bg',
     3: 'Ct',
     4: 'Ch',
     5: 'Cz',
     6: 'Da',
     7: 'De',
     8: 'El',
     9: 'En',
     10: 'Es',
     11: 'Fi',
     12: 'Fr',
     13: 'Hr',
     14: 'Hu',
     15: 'Is',
     16: 'It',
     17: 'Jp',
     18: 'Ko',
     19: 'Nl',
     20: 'No',
     21: 'Pl',
     22: 'Pt',
     24: 'Ro',
     25: 'Ru',
     26: 'Sh',
     27: 'Sk',
     28: 'Sp',
     29: 'Sv',
     30: 'Th',
     31: 'Tr'}
    notifyEvents = {'IMN_CHANGECANDIDATE': IMN_CHANGECANDIDATE,
     'IMN_CLOSECANDIDATE': IMN_CLOSECANDIDATE,
     'IMN_GUIDELINE': IMN_GUIDELINE,
     'IMN_OPENCANDIDATE': IMN_OPENCANDIDATE,
     'IMN_SETCANDIDATEPOS': IMN_SETCANDIDATEPOS,
     'IMN_SETCOMPOSITIONFONT': IMN_SETCOMPOSITIONFONT,
     'IMN_SETCOMPOSITIONWINDOW': IMN_SETCOMPOSITIONWINDOW,
     'IMN_SETCONVERSIONMODE': IMN_SETCONVERSIONMODE,
     'IMN_SETOPENSTATUS': IMN_SETOPENSTATUS,
     'IMN_SETSENTENCEMODE': IMN_SETSENTENCEMODE,
     'IMN_SETSTATUSWINDOWPOS': IMN_SETSTATUSWINDOWPOS,
     'IMN_PRIVATE': IMN_PRIVATE}
    compositionEvents = {'GCS_COMPATTR': GCS_COMPATTR,
     'GCS_COMPCLAUSE': GCS_COMPCLAUSE,
     'GCS_COMPREADSTR': GCS_COMPREADSTR,
     'GCS_COMPREADATTR': GCS_COMPREADATTR,
     'GCS_COMPREADCLAUSE': GCS_COMPREADCLAUSE,
     'GCS_COMPSTR': GCS_COMPSTR,
     'GCS_CURSORPOS': GCS_CURSORPOS,
     'GCS_DELTASTART': GCS_DELTASTART,
     'GCS_RESULTCLAUSE': GCS_RESULTCLAUSE,
     'GCS_RESULTREADCLAUSE': GCS_RESULTREADCLAUSE,
     'GCS_RESULTREADSTR': GCS_RESULTREADSTR,
     'GCS_RESULTSTR': GCS_RESULTSTR,
     'CS_INSERTCHAR': CS_INSERTCHAR,
     'CS_NOMOVECARET': CS_NOMOVECARET}
    cModes = {'IME_CMODE_ALPHANUMERIC': IME_CMODE_ALPHANUMERIC,
     'IME_CMODE_NATIVE': IME_CMODE_NATIVE,
     'IME_CMODE_KATAKANA': IME_CMODE_KATAKANA,
     'IME_CMODE_LANGUAGE': IME_CMODE_LANGUAGE,
     'IME_CMODE_FULLSHAPE': IME_CMODE_FULLSHAPE,
     'IME_CMODE_ROMAN': IME_CMODE_ROMAN,
     'IME_CMODE_CHARCODE': IME_CMODE_CHARCODE,
     'IME_CMODE_HANJACONVERT': IME_CMODE_HANJACONVERT,
     'IME_CMODE_SOFTKBD': IME_CMODE_SOFTKBD,
     'IME_CMODE_NOCONVERSION': IME_CMODE_NOCONVERSION,
     'IME_CMODE_EUDC': IME_CMODE_EUDC,
     'IME_CMODE_SYMBOL': IME_CMODE_SYMBOL,
     'IME_CMODE_FIXED': IME_CMODE_FIXED}
    cSent = {'IME_SMODE_NONE': IME_SMODE_NONE,
     'IME_SMODE_PLAURALCLAUSE': IME_SMODE_PLAURALCLAUSE,
     'IME_SMODE_SINGLECONVERT': IME_SMODE_SINGLECONVERT,
     'IME_SMODE_AUTOMATIC': IME_SMODE_AUTOMATIC,
     'IME_SMODE_PHRASEPREDICT': IME_SMODE_PHRASEPREDICT,
     'IME_SMODE_CONVERSATION': IME_SMODE_CONVERSATION,
     'IME_SMODE_RESERVED': IME_SMODE_RESERVED}
    dwAction = {'NI_OPENCANDIDATE': NI_OPENCANDIDATE,
     'NI_CLOSECANDIDATE': NI_CLOSECANDIDATE,
     'NI_SELECTCANDIDATESTR': NI_SELECTCANDIDATESTR,
     'NI_CHANGECANDIDATELIST': NI_CHANGECANDIDATELIST,
     'NI_FINALIZECONVERSIONRESULT': NI_FINALIZECONVERSIONRESULT,
     'NI_COMPOSITIONSTR': NI_COMPOSITIONSTR,
     'NI_SETCANDIDATE_PAGESTART': NI_SETCANDIDATE_PAGESTART,
     'NI_SETCANDIDATE_PAGESIZE': NI_SETCANDIDATE_PAGESIZE,
     'NI_IMEMENUSELECTED': NI_IMEMENUSELECTED}
    dwIndex = {'CPS_COMPLETE': CPS_COMPLETE,
     'CPS_CONVERT': CPS_CONVERT,
     'CPS_REVERT': CPS_REVERT,
     'CPS_CANCEL': CPS_CANCEL}

    def __init__(self):
        service.Service.__init__(self)
        self.imeFileName = ''
        self.maxCompositionStringLength = None
        self.doesNotHonorPageStart = False

    def LogInfo(self, *k, **v):
        lg.Info('ime', *k, **v)

    def LogWarn(self, *k, **v):
        lg.Warn('ime', *k, **v)

    def LogError(self, *k, **v):
        lg.Error('ime', *k, **v)

    def SetDebug(self, on = 1):
        self.debug = on

    def Run(self, *etc):
        self.debug = 0
        self.primaryLanguage = None
        self.subLanguage = None
        self.indicator = 'En'
        self.currentLanguage = 1033
        self.s_bInsertOnType = False
        self.compWindow = None
        self.readingWindow = None
        self.bShowReadingWindow = False
        self.bShowCandidateWindow = False
        self.s_CandList = {}
        self.compActive = False
        self.currentFocus = None
        self.allowed = (uicls.SinglelineEditCore, uicls.EditPlainTextCore, browser.BrowserPane)
        self.s_bVerticalCand = True
        triapp = trinity.app
        self.ime = trinity.TriIME()
        self.ime.DisableTextFrameService()
        self.ime.SetHWND(triapp.GetHwnd())
        uicore.uilib.inputLangChangeHandler = self.OnLanguageChange
        uicore.uilib.activateAppHandler = self.OnActivateApp
        uicore.uilib.imeSetContextHandler = self.OnSetContext
        uicore.uilib.imeStartCompositionHandler = self.OnStartComposition
        uicore.uilib.imeCompositionHandler = self.OnComposition
        uicore.uilib.imeEndCompositionHandler = self.OnEndComposition
        uicore.uilib.imeNotifyHandler = self.OnNotify
        self.ime.OnLanguageChanged()
        self.SetLanguage(self.ime.GetKeyboardLayout())
        self.indicator = self.GetLanguageIndicator()
        self.ResetCompositionString()
        self.state = service.SERVICE_RUNNING
        self.compWindowParent = None
        self.readingWindowParent = None
        uthread.new(self.PositionWindows)

    def Stop(self, stream):
        self.primaryLanguage = None
        self.subLanguage = None
        self.indicator = None
        self.currentLanguage = None
        self.s_bInsertOnType = None
        self.ime = None
        if getattr(uicore, 'uilib', None):
            uicore.uilib.inputLangChangeHandler = None
            uicore.uilib.activateAppHandler = None
            uicore.uilib.imeSetContextHandler = None
            uicore.uilib.imeStartCompositionHandler = None
            uicore.uilib.imeCompositionHandler = None
            uicore.uilib.imeEndCompositionHandler = None
            uicore.uilib.imeNotifyHandler = None
        self.HideCompWindow()
        self.HideReadingWindow()
        self.compWindow = None
        self.readingWindow = None
        if getattr(uicore, 'uilib', None) is None:
            return
        for each in uicore.desktop.children[:]:
            if each.name == 'IME':
                each.Close()

    def OnSessionChanged(self, isRemote, sess, change):
        if self.debug:
            self.LogInfo('OnSessionChanged isRemote:', isRemote, 'sess:', sess, 'change:', change)
        triapp = trinity.app
        self.ime.SetHWND(triapp.GetHwnd())
        self.ime.OnLanguageChanged()

    def GetKeyboardLanguageID(self):
        current = self.ime.GetKeyboardLayout()
        return self._SplitLangIdentifier(current)[0]

    def IsVisible(self):
        if self.debug:
            self.LogInfo('IsVisible')
        if self.compWindow and self.compWindow.state != uiconst.UI_HIDDEN:
            return 1
        if self.readingWindow and self.readingWindow.state != uiconst.UI_HIDDEN:
            return 1
        return 0

    def IsImeWidget(self, widget):
        return isinstance(widget, self.allowed)

    def OnLanguageChange(self, wp, lp):
        if self.debug:
            self.LogInfo('OnLanguageChange wp:', wp, 'lp:', lp)
        triapp = trinity.app
        self.ime.SetHWND(triapp.GetHwnd())
        self.ime.OnLanguageChanged()
        self.SetLanguage(lp)
        self.indicator = self.GetLanguageIndicator()
        if self.debug:
            self.LogInfo('    primary lang:', self.primaryLanguage)
            self.LogInfo('    sub lang:    ', self.subLanguage)
        self.UpdateLanguageIndicator()
        if self.debug:
            self.LogInfo('<OnLanguageChange: 1')
        return 1

    def OnActivateApp(self, wp, lp):
        if self.debug:
            self.LogInfo('OnAcivateApp wp:', wp, 'lp:', lp)
        self.SetImeState(wp)
        if self.debug:
            self.LogInfo('<OnAcivateApp: None')

    def SetImeState(self, enable = True):
        if enable and self.currentFocus:
            self.ime.AssociateContext(True)
        else:
            self.ime.AssociateContext(False)

    def OnSetContext(self, wp, lp):
        if self.debug:
            self.LogInfo('OnSetContext wp:', wp, 'lp:', lp, ' Returns:', not self.IsHandlingIme())
        return not self.IsHandlingIme()

    def OnStartComposition(self, wp, lp):
        if self.debug:
            self.LogInfo('OnStartComposition wp:', wp, 'lp:', lp)
            if uicore.registry.GetFocus() != self.currentFocus:
                self.LogError('self.currentFocus not the currently focused item!')
        self.compActive = True
        self.ResetCompositionString()
        if self.debug:
            self.LogInfo('<OnStartComposition:', self.IsHandlingIme() or None)
        return self.IsHandlingIme() or None

    def IsImmError(self, value):
        if value == IMM_ERROR_NODATA:
            return True
        if value == IMM_ERROR_GENERAL:
            return True
        return False

    def OnComposition(self, wp, lp):
        if self.debug:
            self.LogInfo('OnComposition wp:', wp, 'lp:', lp)
            if lp:
                for key, val in self.compositionEvents.iteritems():
                    if val == val & lp:
                        self.LogInfo('  lParam |= ', key)

        if not self.IsHandlingIme():
            if self.debug:
                self.LogInfo('<OnComposition: None (Not handling IME)')
            return None
        events = self.ImmGetCompositionString(lp)
        if GCS_CURSORPOS in events:
            pos = events[GCS_CURSORPOS]
            if not self.IsImmError(pos):
                self.s_nCompCaret = max(0, int(pos))
        if GCS_RESULTSTR in events:
            result = events[GCS_RESULTSTR]
            if not self.IsImmError(result):
                self.TruncateCompString(len(result))
                self.s_CompString = result
                self.SendCompString()
                self.ResetCompositionString()
                self.ShowCompWindow()
        if GCS_COMPSTR in events:
            result = events[GCS_COMPSTR]
            if result and not self.IsImmError(result):
                self.TruncateCompString(len(result))
                if self.HandleMaxCompositionString(result):
                    if self.debug:
                        self.LogInfo('<OnComposition: 1 (HandleMaxComposition)')
                    return 1
                self.s_CompString = result
                if self.s_bInsertOnType:
                    self.SendCompString()
                    nCount = len(self.s_CompString) - self.s_nCompCaret
                    for i in xrange(nCount):
                        self.currentFocus.OnKeyDown(uiconst.VK_LEFT, 0)

            self.ResetCaretBlink()
            self.ShowCompWindow()
        if self.debug:
            self.LogInfo('<OnComposition: 1')
        return 1

    def HandleMaxCompositionString(self, compositionString):
        if self.debug:
            self.LogInfo('HandleMaxCompositionString compositionString:', compositionString)
        if self.maxCompositionStringLength is not None:
            lenResult = 0
            for char in compositionString:
                val = ord(char)
                if val > 255:
                    lenResult += 2
                else:
                    lenResult += 1

            if lenResult > self.maxCompositionStringLength:
                if self.debug:
                    self.LogInfo('SetCompositionString result[:', self.maxCompositionStringLength, ']:', compositionString[:self.maxCompositionStringLength], 'compositionString:', compositionString)
                count = lenResult - self.maxCompositionStringLength
                if self.debug:
                    self.LogInfo('Backspacing:', count)
                self.ime.Backspace(count)
                if self.debug:
                    self.LogInfo('Backspacing:', count, 'done')
                return 1

    def OnEndComposition(self, wp, lp):
        if uicore.uilib.Key(uiconst.VK_RETURN):
            uicore.registry.BlockConfirm()
        if self.debug:
            self.LogInfo('OnEndComposition wp:', wp, 'lp:', lp)
        if not self.IsHandlingIme():
            if self.debug:
                self.LogInfo('<OnEndComposition: None (Not handling IME)')
            return None
        self.TruncateCompString()
        self.ResetCompositionString()
        self.bShowReadingWindow = False
        self.HideCompWindow()
        self.compActive = False
        if self.debug:
            self.LogInfo('<OnEndComposition: True')
        return True

    def OnNotify(self, wp, lp):
        if self.debug:
            self.LogInfo('OnNotify wp:', wp, 'lp:', lp)
            if wp:
                for key, val in self.notifyEvents.iteritems():
                    if val == wp:
                        self.LogInfo('  wParam = ', key)

        if not self.IsHandlingIme():
            if self.debug:
                self.LogInfo('<OnNotify: None')
            return None
        if wp in (IMN_SETCONVERSIONMODE, IMN_SETOPENSTATUS):
            self.UpdateLanguageIndicator()
        elif wp in (IMN_OPENCANDIDATE, IMN_CHANGECANDIDATE):
            self.bShowCandidateWindow = True
            self.bShowReadingWindow = False
            cList = self.ImmGetCandidateList()
            if self.debug:
                self.LogInfo('  Candidates:', cList)
            if cList:
                self.ShowReadingWindow(cList)
        elif wp == IMN_CLOSECANDIDATE:
            self.bShowCandidateWindow = False
            self.s_CandList = {}
            self.HideReadingWindow()
        elif wp == IMN_PRIVATE:
            if not self.bShowCandidateWindow:
                cList = self.ime.GetReadingString()
                if self.debug:
                    self.LogInfo('  ReadingStrings:', cList)
                self.s_CandList.update(cList)
                if cList.has_key('Strings') and cList['Strings']:
                    self.bShowReadingWindow = True
                    self.ShowReadingWindow(cList)
                else:
                    self.bShowReadingWindow = False
                    self.HideReadingWindow()
            imeID = self.GetImeId()
            trap = False
            if imeID in (IMEID_CHT_VER42,
             IMEID_CHT_VER43,
             IMEID_CHT_VER44,
             IMEID_CHS_VER41,
             IMEID_CHS_VER42):
                if lp == 1 or lp == 2:
                    trap = True
            elif imeID in (IMEID_CHT_VER50,
             IMEID_CHT_VER51,
             IMEID_CHT_VER52,
             IMEID_CHT_VER60,
             IMEID_CHS_VER53):
                if lp in (16, 17, 26, 27, 28):
                    trap = True
            if trap:
                if self.debug:
                    self.LogInfo('<OnNotify: 1 (Trapping IMN_PRIVATE)')
                return 1
        if self.debug:
            self.LogInfo('<OnNotify: 0')
        return 0

    def _SplitLangIdentifier(self, code):
        code = code & 4026531839L
        if code & 1073676288:
            code = (code & 1073676288) >> 16
        primaryLanguage = code & 1023
        subLanguage = (code & 64512) >> 10
        return (primaryLanguage, subLanguage)

    def SetLanguage(self, code):
        if self.debug:
            self.LogInfo('    SetLanguage code:', code)
        self.primaryLanguage, self.subLanguage = self._SplitLangIdentifier(code)
        self.currentLanguage = code
        self.s_bInsertOnType = self.primaryLanguage == LANG_KOREAN
        if self.primaryLanguage in [LANG_CHINESE, LANG_KOREAN]:
            self.s_bVerticalCand = False
        else:
            self.s_bVerticalCand = True

    def GetLanguageIndicator(self, code = None, conv = None):
        if self.debug:
            self.LogInfo('    GetLanguageIndicator code:', code, 'conv:', conv)
        primLang, subLang = self._SplitLangIdentifier(code or self.currentLanguage)
        indicator = None
        if primLang == LANG_CHINESE:
            if subLang == SUBLANG_CHINESE_SIMPLIFIED:
                indicator = INDICATOR_CHS
            elif subLang == SUBLANG_CHINESE_TRADITIONAL:
                indicator = INDICATOR_CHT
            else:
                indicator = INDICATOR_NON_IME
        elif primLang == LANG_KOREAN:
            indicator = INDICATOR_KOREAN
        elif primLang == LANG_JAPANESE:
            indicator = INDICATOR_HIRAGANA
        else:
            indicator = self.primaryLanguages.get(primLang, 'En')
        return indicator

    def GetIndicator(self):
        if self.debug:
            self.LogInfo('    GetIndicator')
        return self.indicator

    def UpdateLanguageIndicator(self):
        if self.debug:
            self.LogInfo('    UpdateLanguageIndicator')
        if self.currentFocus:
            if hasattr(self.currentFocus, 'SetLangIndicator'):
                self.currentFocus.SetLangIndicator(self.indicator)

    def ResetCompositionString(self):
        if self.debug:
            self.LogInfo('    ResetCompositionString')
        self.s_nCompCaret = 0
        self.s_CompString = ''

    def TruncateCompString(self, iNewStrLen = 0):
        if self.debug:
            self.LogInfo('    TruncateCompositionString iNewStrLen:', iNewStrLen)
        if not self.s_bInsertOnType:
            return
        cc = len(self.s_CompString)
        if not (iNewStrLen == 0 or iNewStrLen >= cc):
            if self.debug:
                self.LogInfo('    TruncateCompositionString iNewStrLen:', iNewStrLen, 'cc:', cc)
            return
        for i in xrange(cc - self.s_nCompCaret):
            if self.debug:
                self.LogInfo('    TruncateCompositionString VK_RIGHT')
            if hasattr(self.currentFocus, 'OnKeyDown'):
                self.currentFocus.OnKeyDown(uiconst.VK_RIGHT, 0)

        iNewStrLen = 0
        if iNewStrLen < cc:
            if self.debug:
                self.LogInfo('    TruncateCompositionString iNewStrLen < cc')
            for i in xrange(cc - iNewStrLen):
                if self.debug:
                    self.LogInfo('    TruncateCompositionString VK_BACK')
                if hasattr(self.currentFocus, 'OnChar'):
                    self.currentFocus.OnChar(uiconst.VK_BACK, 0)

        else:
            if self.debug:
                self.LogInfo('    TruncateCompositionString iNewStrLen = cc')
            iNewStrLen = cc
        for i in xrange(iNewStrLen):
            if self.debug:
                self.LogInfo('    TruncateCompositionString VK_LEFT')
            if hasattr(self.currentFocus, 'OnKeyDown'):
                self.currentFocus.OnKeyDown(uiconst.VK_LEFT, 0)

    def FinalizeString(self, bSend = False):
        if self.debug:
            self.LogInfo('    FinalizeString bSend:', bSend)
        if not self.s_bInsertOnType and bSend:
            self.SendCompString()
        self.ResetCompositionString()
        self.ImmNotifyIME(NI_COMPOSITIONSTR, CPS_CANCEL, 0)
        self.ImmNotifyIME(NI_CLOSECANDIDATE, 0, 0)

    def SendCompString(self):
        if self.debug:
            self.LogInfo('    SendCompString')
        for char in self.s_CompString:
            self.currentFocus.OnChar(ord(char), 0)

    def ResetCaretBlink(self):
        if self.debug:
            self.LogInfo('    ResetCaretBlink')
        self.m_bCaretOn = True

    def ShowCompWindow(self):
        if self.debug:
            self.LogInfo('    ShowCompWindow')
        edit = self.currentFocus
        if not edit or edit.destroyed:
            self.HideCompWindow()
            if self.debug:
                self.LogInfo('    <<ShowCompWindow (HideCompWindow) edit:', edit)
            return
        fontsize = 14
        if hasattr(edit, 'GetFontParams'):
            fontsize = max(fontsize, edit.GetFontParams().fontsize)
        elif isinstance(edit, (browser.BrowserPane,)):
            fontsize = 24
        if not self.compWindow:
            self.compWindow = uicls.Container(name='IME', parent=uicore.desktop, align=uiconst.TOPLEFT, idx=0)
            self.compCursor = uicls.Fill(parent=self.compWindow, align=uiconst.TOPLEFT, width=1, top=2, color=(1.0, 1.0, 1.0, 0.75))
            self.compText = uicls.Label(parent=self.compWindow, fontsize=fontsize, state=uiconst.UI_DISABLED, left=3, top=1)
            uicls.Frame(parent=self.compWindow)
            uicls.Fill(parent=self.compWindow, color=(0.0, 0.0, 0.0, 1.0))
        if self.s_bInsertOnType:
            self.compWindow.state = uiconst.UI_HIDDEN
        else:
            self.compWindow.state = uiconst.UI_DISABLED
        if self.debug:
            self.LogInfo('    ShowCompWindow self.s_CompString:', [ ord(char) for char in self.s_CompString ])
        self.compText.fontsize = fontsize
        self.compText.text = self.s_CompString
        self.compWindow.width = self.compText.textwidth + self.compText.left * 2
        self.compWindow.height = self.compText.textheight + self.compText.top * 2
        self.compCursor.height = self.compWindow.height - self.compCursor.top * 2
        self.compWindowParent = edit
        self.compCursor.left = self.compText.left + self.GetCompCursorPos(self.s_nCompCaret)
        self.PositionCompositionWindow()

    def PositionCompositionWindow(self):
        edit = self.compWindowParent
        if not edit or edit.destroyed:
            if self.debug:
                self.LogInfo('    PositionCompositionWindow: Invalid edit widget')
            return
        if isinstance(edit, (uicls.EditPlainTextCore,)):
            entry = edit.GetActiveNode()
            if not entry.panel:
                if self.debug:
                    self.LogInfo('    PositionCompositionWindow: EditPlainTextCore panel not found')
                return
            panel = entry.panel
            y = panel.absoluteTop - self.compWindow.height + 2
            x = panel.absoluteLeft + panel.GetCursorOffset() - 1
        elif isinstance(edit, (uicls.SinglelineEditCore,)):
            y = edit.absoluteTop - self.compWindow.height + 2
            x = edit.absoluteLeft + edit.caretIndex[1] - 1
        elif isinstance(edit, (browser.BrowserPane,)):
            l, t, w, h = edit.GetAbsolute()
            panel = edit
            y = t + h / 2
            x = l + w / 2
        else:
            self.LogWarn('IME Composition Window displayed on top of unknown widget.')
            return
        self.compWindow.left = min(uicore.desktop.width - self.compWindow.width - 6, x)
        self.compWindow.top = y

    def PositionWindows(self):
        while self.state == service.SERVICE_RUNNING and getattr(uicore, 'uilib', None):
            sleeptime = 250
            if uicore.uilib.leftbtn:
                sleeptime = 5
            if self.compWindow and self.compWindow.state == uiconst.UI_DISABLED and self.compWindowParent:
                self.PositionCompositionWindow()
            if self.readingWindow and self.readingWindow.state == uiconst.UI_DISABLED:
                if self.primaryLanguage == LANG_CHINESE and not self.GetImeId():
                    nXComp = 0
                elif self.primaryLanguage == LANG_JAPANESE:
                    nXComp = self.GetCompCursorPos(self.s_nCompCaret)
                else:
                    nXComp = self.GetCompCursorPos(self.s_nCompCaret)
                x = self.compWindow.left + nXComp
                y = self.compWindow.top
                for xOffset, yOffset in [(0, self.compWindow.height + 6),
                 (0, -self.readingWindow.height - 6),
                 (6, 0),
                 (-self.readingWindow.width - 6, 0)]:
                    if 0 < x + xOffset < uicore.desktop.width - self.readingWindow.width and 0 < y + yOffset < uicore.desktop.height - self.readingWindow.height:
                        self.readingWindow.left = x + xOffset
                        self.readingWindow.top = y + yOffset
                        break

            blue.pyos.synchro.SleepWallclock(sleeptime)

    def HideCompWindow(self):
        if self.debug:
            self.LogInfo('    HideCompWindow')
        if self.compWindow:
            self.compWindow.state = uiconst.UI_HIDDEN

    def GetCompCursorPos(self, pos):
        if self.debug:
            self.LogInfo('    GetCompCursorPos')
        if not pos or not self.s_CompString:
            self.LogInfo('    GetCompCursorPos Escaped, pos, s_CompString', pos, self.s_CompString)
            return 0
        if getattr(self, 'compText', None):
            fontsize = self.compText.fontsize
            textWidth, textHeight = self.compText.MeasureTextSize(self.s_CompString[:pos], fontsize=fontsize)
        else:
            textWidth, textHeight = uicls.Label.MeasureTextSize(self.s_CompString[:pos])
        return textWidth

    def ShowReadingWindow(self, cList = None):
        if self.debug:
            self.LogInfo('    ShowReadingWindow')
        if not self.compWindow:
            if self.debug:
                self.LogInfo('    Not showing reading window as no self.compWindow')
            return
        edit = self.currentFocus
        if not edit or not cList:
            self.HideCompWindow()
            if self.debug:
                self.LogWarn('<< ShowReadingWindow: not edit or cList')
            return
        if isinstance(edit, (uicls.EditPlainTextCore,)):
            entry = edit.GetActiveNode()
            if not entry.panel:
                if self.debug:
                    self.LogInfo('    <<ShowCompWindow failed to get the panel')
                return
            panel = entry.panel
        else:
            panel = edit
        if self.debug:
            self.LogInfo('++++++++ %s' % self.imeFileName)
            for k, v in cList.iteritems():
                self.LogInfo('cList[%s] = %s' % (k, v))

            self.LogInfo('--------')
        pagestart = cList.get('PageStart', 0)
        if self.debug:
            self.LogInfo('    cList.keys:', cList.keys())
        if self.doesNotHonorPageStart:
            self.nPageTopIndex = cList['Selection'] / cList['PageSize'] * cList['PageSize']
        elif self.primaryLanguage == LANG_JAPANESE:
            self.nPageTopIndex = cList['Selection'] / cList['PageSize'] * cList['PageSize']
        else:
            self.nPageTopIndex = pagestart
        cList['Selection'] = [cList['Selection'] - self.nPageTopIndex, -1][self.currentLanguage == LANG_CHS and not self.GetImeId()]
        i = self.nPageTopIndex
        j = 0
        displayString = u''
        if self.debug:
            for key, val in cList.iteritems():
                self.LogInfo('    ShowReadingWindow - ', key, ' = ', val)

        s_nFirstTargetConv = -1
        bVerticalCand = self.s_bVerticalCand
        if self.bShowReadingWindow:
            if self.debug:
                self.LogWarn('SHOW READING WINDOW')
            while i < len(cList['Strings']):
                if not bVerticalCand:
                    displayString += u'%s' % unichr(cList['Strings'][i])
                else:
                    displayString += u'%s<br>' % unichr(cList['Strings'][i])
                i += 1

            cList['display'] = displayString
            cList['Count'] = len(cList['Strings'])
        elif self.bShowCandidateWindow:
            if self.debug:
                self.LogWarn('SHOW CANDIDATE WINDOW')
            while i < len(cList['Strings']) and j < cList['PageSize']:
                if not bVerticalCand:
                    displayString += u' %d %s ' % ((1 + j) % 10, cList['Strings'][i])
                else:
                    displayString += u'%d %s<br>' % ((1 + j) % 10, cList['Strings'][i])
                i += 1
                j += 1

            cList['display'] = displayString
            cList['Count'] = len(cList['Strings']) - pagestart
            if cList['Count'] > cList['PageSize']:
                cList['Count'] = cList['PageSize']
        elif self.debug:
            self.LogWarn('NOT CANDIDATE OR READING WINDOW?')
        if panel:
            if self.primaryLanguage == LANG_CHINESE and not self.GetImeId():
                nXComp = 0
            elif self.primaryLanguage == LANG_JAPANESE:
                nXComp = self.GetCompCursorPos(self.s_nCompCaret)
            else:
                nXComp = self.GetCompCursorPos(self.s_nCompCaret)
            x = self.compWindow.left + nXComp
            y = self.compWindow.top
            if not self.readingWindow:
                self.readingWindow = uicls.Container(name='IME', parent=uicore.desktop, align=uiconst.TOPLEFT, idx=0)
                self.readingText = uicls.Label(text='', parent=self.readingWindow, fontsize=14, state=uiconst.UI_DISABLED, left=5, top=3)
                uicls.Frame(parent=self.readingWindow)
                uicls.Fill(parent=self.readingWindow, color=(0.0, 0.0, 0.0, 1.0))
            if cList['display']:
                self.readingWindow.display = True
                self.readingText.text = cList['display']
                self.readingWindow.width = self.readingText.textwidth + 10
                self.readingWindow.height = self.readingText.textheight + 6
            else:
                self.readingWindow.display = False
            if self.debug:
                self.LogInfo('cList["display"]:', cList['display'])
                self.LogInfo('panel.height:', panel.height)
                self.LogInfo('not bVerticalCand:', not bVerticalCand)
                self.LogInfo('cList["Count"]:', cList['Count'])
                self.LogInfo('panel.height * [cList["Count"],1][not bVerticalCand]:', panel.height * [cList['Count'], 1][not bVerticalCand])
            for xOffset, yOffset in [(0, self.compWindow.height + 6),
             (0, -self.readingWindow.height - 6),
             (6, 0),
             (-self.readingWindow.width - 6, 0)]:
                if 0 < x + xOffset < uicore.desktop.width - self.readingWindow.width and 0 < y + yOffset < uicore.desktop.height - self.readingWindow.height:
                    self.readingWindow.left = x + xOffset
                    self.readingWindow.top = y + yOffset
                    break

            self.readingWindow.state = uiconst.UI_DISABLED

    def HideReadingWindow(self):
        if self.debug:
            self.LogInfo('    HideReadingWindow')
        if self.readingWindow:
            self.readingWindow.state = uiconst.UI_HIDDEN

    def SetFocus(self, widget):
        if self.debug:
            self.LogInfo('    SetFocus')
        if self.IsImeWidget(widget):
            self.currentFocus = widget
        else:
            self.currentFocus = None
        self.SetImeState()

    def KillFocus(self, widget):
        if self.debug:
            self.LogInfo('    KillFocus widget:', widget)
        self.FinalizeString(True)
        self.HideCompWindow()
        self.HideReadingWindow()
        self.currentFocus = None
        self.SetImeState()

    def GetMenuDelegate(self, widget, node, m):
        if self.debug:
            self.LogInfo('    GetMenuDelegate widget:', widget, 'node:', node, 'm:', m)
            self.LogInfo('    PRIMARY LANG:', self.primaryLanguage, 'SECONDARY:', self.subLanguage)
        if self.primaryLanguage == LANG_CHINESE and self.subLanguage == SUBLANG_CHINESE_SIMPLIFIED:
            if self.GetOpenStatus():
                m.append((uiutil.MenuLabel('/Carbon/UI/Commands/CloseIme'), self.SetOpenStatus, (0,)))
            else:
                m.append((uiutil.MenuLabel('/Carbon/UI/Commands/OpenIME'), self.SetOpenStatus, (1,)))
            m.append((uiutil.MenuLabel('/Carbon/UI/Commands/CmdShape'), self.SimulateHotKey, (IME_CHOTKEY_SHAPE_TOGGLE,)))
            m.append((uiutil.MenuLabel('/Carbon/UI/Commands/CmdSymbol'), self.SimulateHotKey, (IME_CHOTKEY_SYMBOL_TOGGLE,)))
        elif self.primaryLanguage == LANG_CHINESE and self.subLanguage == SUBLANG_CHINESE_TRADITIONAL:
            if self.GetOpenStatus():
                m.append((uiutil.MenuLabel('/Carbon/UI/Commands/CloseIme'), self.SetOpenStatus, (0,)))
            else:
                m.append((uiutil.MenuLabel('/Carbon/UI/Commands/OpenIME'), self.SetOpenStatus, (1,)))
            m.append((uiutil.MenuLabel('/Carbon/UI/Commands/CmdShape'), self.SimulateHotKey, (IME_THOTKEY_SHAPE_TOGGLE,)))
            m.append((uiutil.MenuLabel('/Carbon/UI/Commands/CmdSymbol'), self.SimulateHotKey, (IME_THOTKEY_SYMBOL_TOGGLE,)))
        elif self.primaryLanguage == LANG_JAPANESE:
            if self.GetOpenStatus():
                m.append((uiutil.MenuLabel('/Carbon/UI/Commands/CloseIme'), self.SetOpenStatus, (0,)))
            else:
                m.append((uiutil.MenuLabel('/Carbon/UI/Commands/OpenIME'), self.SetOpenStatus, (1,)))
        elif self.primaryLanguage == LANG_KOREAN:
            m.append((uiutil.MenuLabel('/Carbon/UI/Commands/CloseIme'), self.SimulateHotKey, (IME_KHOTKEY_ENGLISH,)))
            m.append((uiutil.MenuLabel('/Carbon/UI/Commands/OpenIME'), self.SimulateHotKey, (IME_KHOTKEY_ENGLISH,)))
            m.append((uiutil.MenuLabel('/Carbon/UI/Commands/CmdShape'), self.SimulateHotKey, (IME_KHOTKEY_SHAPE_TOGGLE,)))
            m.append((uiutil.MenuLabel('/Carbon/UI/Commands/CmdHanja'), self.SimulateHotKey, (IME_KHOTKEY_HANJACONVERT,)))

    def IsHandlingIme(self):
        return settings.user.ui.Get('nativeIME', True)

    def GetImeId(self, index = 0):
        return self.ime.GetImeId()

    def ImmNotifyIME(self, action, index, value):
        if self.debug:
            self.LogInfo('    ImmNotifyIME action:', action, 'index:', index, 'value:', value)
        self.ime.NotifyIME(action, index, value)

    def ImmGetConversionStatus(self):
        if self.debug:
            self.LogInfo('    ImmGetConversionStatus')
        conv, sent = self.ime.GetConversionStatus()
        if self.debug:
            for key, val in self.cModes.iteritems():
                if val == conv & val:
                    self.LogInfo('    > conv |= ', key)

            for key, val in self.cSent.iteritems():
                if val == sent & val:
                    self.LogInfo('    > sent |= ', key)

        return (conv, sent)

    def ImmGetCompositionString(self, event):
        if self.debug:
            self.LogInfo('    >ImmGetCompositionString event:', event)
        ret = self.ime.GetCompositionString(event)
        if self.debug:
            self.LogInfo('    <ImmGetCompositionString returning:', ret)
            for key, val in self.compositionEvents.iteritems():
                if ret.has_key(val):
                    value = ret[val]
                    self.LogInfo('      ', key, '(', val, ') = ', type(ret[val]), `value`)

        return ret

    def ImmGetCandidateList(self):
        if self.debug:
            self.LogInfo('    ImmGetCandidateList')
        return self.ime.GetCandidateList()

    def ImmIsIME(self, lang):
        if self.debug:
            self.LogInfo('    ImmIsIME lang:', lang)
        return self.ime.IsIME(lang)

    def ActivateKeyboard(self, lang):
        if self.debug:
            self.LogInfo('    ActivateKeyboard lang:', lang)
        self.ime.ActivateKeyboardLayout(lang, 0)

    def SimulateHotKey(self, hotKey):
        if self.debug:
            self.LogInfo('    SimulateHotKey hotKey:', hotKey)
        return self.ime.SimulateHotKey(hotKey)

    def GetOpenStatus(self):
        if self.debug:
            self.LogInfo('    GetOpenStatus')
        return self.ime.GetOpenStatus()

    def SetOpenStatus(self, bOpen):
        if self.debug:
            self.LogInfo('    SetOpenStatus:', bOpen)
        return self.ime.SetOpenStatus(bOpen)