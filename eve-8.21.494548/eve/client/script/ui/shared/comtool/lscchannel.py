#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/comtool/lscchannel.py
import uix
import uiutil
import xtriui
import form
import uthread
import blue
import re
import util
import listentry
import chat
import sys
import types
import service
import log
import uiconst
import uicls
import base
import vivoxConstants
from itertools import izip, imap
import localization
import fontConst
import telemetry
import unicodedata
import trinity
import math
seemsURL = re.compile('\\b\n        (\n            (\n                (https?://|www\\d{0,3}[.])           # Starts with http(s) or www with optional number\n                [a-zA-Z0-9\\-\\.]+\\.[a-zA-Z]{2,6}     # Followed by *. and .* with 2 to 6 characters\n            )\n            |                                       # or \n            (\n                https?://                           # Starts with http(s)\n                \\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}  # Followed by ip number\n            )\n        )\n        (:\\d{1,6})?                                 # Optional port number\n        (\n            (/([^\\s]+)?)                            # Must continue with / before we eat up optional non-space\n            |\n            /?                                      # or may end with single /\n        )\n        ', re.X)
alreadyURLOrTag = re.compile('(<a .*?/a>|<url.*?/url>|<.*?>)')
showInfoComplete = re.compile("(?P<pretext>.*?<loc><url=showinfo:) # Non-greedy consomption of all text up to shoinfo tag\n                                 (?P<typeID>\\d*)                # typeID, always present\n                                 (?P<seperator>/*)              # Optional seperator, only present when itemID is\n                                 (?P<itemID>\\d*)                # optional itemID\n                                 >                              # close bracket for show info anchor\n                                 (?P<itemName>.*?)              # Supplied item name\n                                 (?P<posttext></url>)           # Close anchor. Only here to ensure the link isn't mangled.\n                                 </loc>", re.X)
ROLE_SLASH = service.ROLE_GML | service.ROLE_LEGIONEER
ROLE_TRANSAM = service.ROLE_TRANSLATION | service.ROLE_TRANSLATIONADMIN | service.ROLE_TRANSLATIONEDITOR
MAXMSGS = 100
USERLISTLOCK_MOUSEIDLE_TIME = 5000
MESSAGEMODE_TEXTONLY = 0
MESSAGEMODE_SMALLPORTRAIT = 1
MESSAGEMODE_BIGPORTRAIT = 2
MESSAGEMODETEXTS = {MESSAGEMODE_TEXTONLY: 'UI/Chat/ShowTextOnly',
 MESSAGEMODE_SMALLPORTRAIT: 'UI/Chat/ShowTextWithSmallPortrait',
 MESSAGEMODE_BIGPORTRAIT: 'UI/Chat/ShowTextWithBigPortrait'}
ACTION_ICON = 'res:/UI/Texture/classes/UtilMenu/BulletIcon.png'
_tfrom = u'1370,-_*+=^~@\u263b\u3002\u03bc\u03bf\u043c\u043e\u0441'
_tto = u'leto...........momoc'
_spamTrans = dict(izip(imap(ord, _tfrom), _tto))
for ordinal in [u' ',
 u'\\',
 u'|',
 u'/',
 u'!',
 u'(',
 u')',
 u'[',
 u']',
 u'{',
 u'}',
 u'<',
 u'>',
 u'"',
 u"'",
 u'`',
 u'\xb4']:
    _spamTrans[ord(ordinal)] = None

_dotsubst = re.compile('\\.{2,}')

def NormalizeForSpam(s):
    return _dotsubst.sub('.', unicode(s).lower().translate(_spamTrans).replace('dot', '.'))


@util.Memoized
def GetTaboos():
    bannedPhrasesInChat = sm.GetService('sites').GetBannedInChatList()
    return map(NormalizeForSpam, bannedPhrasesInChat)


def IsSpam(text):
    normtext = NormalizeForSpam(text)
    for taboo in GetTaboos():
        if taboo in normtext:
            foundSpam = True
            idx = text.find(taboo)
            if idx > 0:
                foundSpam = False
                while idx > 0:
                    if text[idx - 1].isalnum():
                        idx = text.find(taboo, idx + 1)
                    else:
                        foundSpam = True
                        break

                return foundSpam
            return True
    else:
        return False


class LSCStack(uicls.WindowStack):
    __guid__ = 'form.LSCStack'
    default_left = 16
    default_width = 317
    default_height = 200

    @staticmethod
    def default_top(*args):
        return uicore.desktop.height - form.LSCStack.default_height - 16


class Channel(uicls.Window):
    __guid__ = 'form.LSCChannel'
    __notifyevents__ = ['OnSpeakingEvent', 'OnPortraitCreated']
    default_stackID = 'LSCStack'
    default_windowID = 'chatchannel'
    default_left = 16
    default_width = 317
    default_height = 200
    default_open = True
    _userlistDirty = False
    _userlistCleanupTimer = None
    _userlistLockIdleData = None
    _userlistSortingLocked = False
    _mouseUpCookie = None

    @staticmethod
    def default_top(*args):
        return uicore.desktop.height - form.LSCChannel.default_height - 16

    @classmethod
    def Reload(cls, instance):
        pass

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        channelID = attributes.channelID
        otherID = attributes.otherID
        self.memberCount = 0
        self.eveMemberCount = None
        self.dustMemberCount = None
        self.channelID = None
        self.output = None
        self.userlist = None
        self.voiceOnlyMembers = []
        self.waiting = None
        self.uss_w = None
        self.uss_x = None
        self.input = None
        self.messageMode = None
        self.scaling = 0
        self.messages = []
        self.closing = 0
        self.inputs = ['']
        self.inputIndex = None
        self.channelInitialized = 0
        self.loadingmessages = 0
        self.changingfont = 0
        self.waitingForReturn = 0
        self.loadQueue = 0
        self.pendingUserNodes = {}
        self.Startup(channelID, otherID)

    def Startup(self, channelID, otherID = None):
        if channelID == -1:
            return
        self.attributesBunch.channelID = channelID
        self.attributesBunch.otherID = otherID
        self.channelID = channelID
        chatlog = '\r\n\r\n\n        \n---------------------------------------------------------------\n\n  Channel ID:      %s\n  Channel Name:    %s\n  Listener:        %s\n  Session started: %s\n---------------------------------------------------------------\n\n' % (channelID,
         chat.GetDisplayName(channelID),
         cfg.eveowners.Get(eve.session.charid).name,
         util.FmtDate(blue.os.GetWallclockTime()))
        self.SetUserEntryType()
        self.scope = 'all'
        self.windowCaption = chat.GetDisplayName(channelID).split('\\')[-1]
        try:
            self.messageMode = int(settings.user.ui.Get('%s_mode' % self.name, MESSAGEMODE_SMALLPORTRAIT))
            self.showUserList = bool(settings.user.ui.Get('%s_usermode' % self.name, True))
        except:
            log.LogTraceback('Settings corrupt, default mode engaged')
            self.messageMode = MESSAGEMODE_TEXTONLY
            self.showUserList = True
            sys.exc_clear()

        self.logfile = None
        if settings.user.ui.Get('logchat', 1):
            try:
                year, month, weekday, day, hour, minute, second, msec = blue.os.GetTimeParts(blue.os.GetWallclockTime())
                timeStamp = '%d%.2d%.2d_%.2d%.2d%.2d' % (year,
                 month,
                 day,
                 hour,
                 minute,
                 second)
                displayName = uiutil.StripTags(chat.GetDisplayName(channelID, otherID=otherID))
                filename = '%s_%s' % (displayName, timeStamp)
                filename = filename.replace('\\', '_').replace('?', '_').replace('*', '_').replace(':', '').replace('.', '').replace(' ', '_')
                filename = filename.replace('/', '_').replace('"', '_').replace('-', '_').replace('|', '_').replace('<', '_').replace('>', '_')
                filename = blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL) + '/EVE/logs/Chatlogs/%s.txt' % filename
                self.logfile = blue.classes.CreateInstance('blue.ResFile')
                if not self.logfile.Open(filename, 0):
                    self.logfile.Create(filename)
                self.logfile.Write(chatlog.encode('utf-16'))
            except:
                self.logfile = None
                log.LogTraceback('Failed to instantiate log file')
                sys.exc_clear()

        self.SetWndIcon('ui_9_64_2')
        self.HideMainIcon()
        self.SetMinSize([250, 150])
        if type(channelID) != types.IntType and not eve.session.role & (service.ROLE_CHTADMINISTRATOR | service.ROLE_GMH):
            if channelID[0][0] not in ('global', 'regionid', 'constellationid'):
                self.MakeUnKillable()
                if self.sr.stack:
                    self.sr.stack.Check()
        btnparent = uicls.Container(parent=self.sr.topParent, idx=0, pos=(0, 0, 0, 20), name='btnparent', state=uiconst.UI_PICKCHILDREN, align=uiconst.TOTOP)
        self.sr.topParent.align = uiconst.TOALL
        self.sr.topParent.padLeft = const.defaultPadding
        self.sr.topParent.padRight = const.defaultPadding
        self.sr.topParent.padTop = 0
        self.sr.topParent.padBottom = const.defaultPadding
        self.SetTopparentHeight(0)
        iconClipper = uiutil.FindChild(self, 'iconclipper')
        if iconClipper:
            iconClipper.top = -1
        self.userlist = uicls.BasicDynamicScroll(parent=self.sr.topParent, name='userlist', align=uiconst.TORIGHT)
        self.userlist.width = settings.user.ui.Get('%s_userlistwidth' % self.name, 128)
        self.userlist.GetContentContainer().OnDropData = self.OnDropCharacter
        self.sortLockFrame = uicls.Frame(parent=self.userlist.sr.clipper, texturePath='res:/UI/Texture/classes/Scroll/scrollLockHilite.png', cornerSize=23, opacity=0.0, idx=0, blendMode=trinity.TR2_SBM_ADDX2)
        div = uicls.Container(name='userlistdiv', parent=self.sr.topParent, width=const.defaultPadding, state=uiconst.UI_NORMAL, align=uiconst.TORIGHT)
        div.OnMouseDown = self.UserlistStartScale
        div.OnMouseUp = self.UserlistEndScale
        div.OnMouseMove = self.UserlistScaling
        div.cursor = 18
        self.sr.userlistdiv = div
        self.output = uicls.BasicDynamicScroll(parent=self.sr.topParent, name='chatoutput_%s' % channelID)
        self.output.stickToBottom = 1
        self.output.OnContentResize = self.OnOutputResize
        self.output.sr.content.GetMenu = self.GetOutputMenu
        self.input = uicls.EditPlainText(parent=self.sr.topParent, align=uiconst.TOBOTTOM, name='input%s' % self.name, height=settings.user.ui.Get('chatinputsize_%s' % self.name, 64), maxLength=const.CHT_MAX_STRIPPED_INPUT, idx=0)
        self.input.ValidatePaste = self.ValidatePaste
        divider = xtriui.Divider(name='divider', align=uiconst.TOTOP, idx=1, height=const.defaultPadding, parent=self.input, state=uiconst.UI_NORMAL)
        divider.Startup(self.input, 'height', 'y', 48, 96)
        divider.OnSizeChanged = self.OnInputSizeChanged
        self.input.OnReturn = self.InputKeyUp
        self.input.CtrlUp = self.CtrlUp
        self.input.CtrlDown = self.CtrlDown
        self.input.RegisterFocus = self.RegisterFocus
        uiutil.SetOrder(divider, 0)
        hint = localization.GetByLabel('UI/Chat/DustMercCounterHint')
        self.dustMercCont = uicls.Container(name='dustMercCont', parent=btnparent, width=50, left=0, state=uiconst.UI_NORMAL, align=uiconst.TORIGHT)
        dustMercIcon = uicls.Sprite(parent=self.dustMercCont, name='dustMercIcon', texturePath='res:/UI/Texture/classes/Chat/InfantryIcon.png', pos=(0, 0, 11, 12), align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL, hint=hint, color=(1, 1, 1, 0.7))
        self.dustMercIconText = uicls.EveLabelSmall(text='', parent=self.dustMercCont, name='dustMercIconText', left=16, state=uiconst.UI_NORMAL, hint=hint, align=uiconst.CENTERLEFT)
        hint = localization.GetByLabel('UI/Chat/CapsuleerCounterHint')
        self.capsuleerCont = uicls.Container(name='eveMemberCountCont', parent=btnparent, width=50, state=uiconst.UI_NORMAL, align=uiconst.TORIGHT)
        capsuleerIcon = uicls.Sprite(parent=self.capsuleerCont, name='capsuleerIcon', texturePath='res:/UI/Texture/Icons/38_16_11.png', pos=(0, 0, 16, 16), align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL, hint=hint, color=(1, 1, 1, 0.7))
        self.capsuleerIconText = uicls.EveLabelSmall(text='', parent=self.capsuleerCont, name='capsuleerIconText', left=16, state=uiconst.UI_NORMAL, hint=hint, align=uiconst.CENTERLEFT)
        hint = localization.GetByLabel('UI/Chat/CombinedCounterHint')
        self.combinedCont = uicls.Container(name='combinedCont', parent=btnparent, width=50, state=uiconst.UI_NORMAL, align=uiconst.TORIGHT)
        combinedIcon = uicls.Sprite(parent=self.combinedCont, name='combinedIcon', texturePath='res:/UI/Texture/classes/Chat/EstimatedChars.png', pos=(0, 0, 16, 16), align=uiconst.CENTERLEFT, state=uiconst.UI_NORMAL, hint=hint, color=(1, 1, 1, 0.7))
        self.combinedIconText = uicls.EveLabelSmall(text='', parent=self.combinedCont, name='combinedIconText', left=16, state=uiconst.UI_NORMAL, hint=hint, align=uiconst.CENTERLEFT)
        self.sr.smaller = uicls.EveLabelSmall(text=localization.GetByLabel('UI/Chat/DecreaseFontSizeIcon'), parent=self.sr.topParent, left=4, state=uiconst.UI_NORMAL)
        self.sr.smaller.OnClick = (self.ChangeFont, -1)
        self.sr.smaller.hint = localization.GetByLabel('UI/Chat/DecreaseFontSize')
        self.sr.smaller.top = -self.sr.smaller.textheight + 17
        self.sr.bigger = uicls.EveLabelMedium(text=localization.GetByLabel('UI/Chat/IncreaseFontSizeIcon'), parent=self.sr.topParent, left=20, state=uiconst.UI_NORMAL)
        self.sr.bigger.OnClick = (self.ChangeFont, 1)
        self.sr.bigger.hint = localization.GetByLabel('UI/Chat/IncreaseFontSize')
        self.sr.bigger.top = -self.sr.bigger.textheight + 18
        settingsMenu = uicls.UtilMenu(menuAlign=uiconst.TOPLEFT, parent=btnparent, align=uiconst.TOPLEFT, left=45, top=2, GetUtilMenu=self.SettingMenu, texturePath='res:/UI/Texture/SettingsCogwheel.png', hint=localization.GetByLabel('UI/Chat/SettingsButtonHint'), width=16, height=16, iconSize=18)
        userListMenu = uicls.UtilMenu(menuAlign=uiconst.TOPLEFT, parent=btnparent, align=uiconst.TOPLEFT, left=65, top=2, GetUtilMenu=self.UserListMenu, texturePath='res:/UI/Texture/classes/Chat/MemberList.png', hint=localization.GetByLabel('UI/Chat/UserlistSettingButtonHint'), width=16, height=16, iconSize=20)
        btn = uicls.ButtonIcon(name='channelWndIcon', texturePath='res:/ui/texture/icons/73_16_10.png', parent=btnparent, pos=(85, 2, 16, 16), align=uiconst.TOPLEFT, hint=localization.GetByLabel('UI/Chat/OpenChannelWindow'), func=self.OpenChannelWindow)
        self.ChangeFont()
        self.SetupUserlist(self.showUserList)
        self.channelInitialized = 1
        self.UpdateCaption(1)
        self.IsBrowser = 1
        try:
            self.SpeakMOTD()
        except:
            log.LogException()
            sys.exc_clear()

        focus = uicore.registry.GetFocus()
        if not (focus and (isinstance(focus, uicls.EditCore) or isinstance(focus, uicls.SinglelineEditCore))):
            uicore.registry.SetFocus(self.input)
        else:
            uicore.registry.RegisterFocusItem(self.input)

    def SettingMenu(self, menuParent):
        if isinstance(self.channelID, int) or self.channelID[0][0] in ('corpid', 'allianceid') or self.channelID[0][0] == 'fleetid':
            menuParent.AddIconEntry(icon=ACTION_ICON, text=localization.GetByLabel('UI/Chat/ReloadMOTD'), callback=self.ShowMotdFromMenu)
        self.AddSettingsOptionsToMenuParent(menuParent)
        self.AddVoiceOptionsToMenuParent(menuParent)
        menuParent.AddDivider()
        menuParent.AddRadioButton(text=localization.GetByLabel(MESSAGEMODETEXTS[MESSAGEMODE_TEXTONLY]), checked=settings.user.ui.Get('%s_mode' % self.name, 1) == MESSAGEMODE_TEXTONLY, callback=(self.SetPictureMode, MESSAGEMODE_TEXTONLY))
        menuParent.AddRadioButton(text=localization.GetByLabel(MESSAGEMODETEXTS[MESSAGEMODE_SMALLPORTRAIT]), checked=settings.user.ui.Get('%s_mode' % self.name, 1) == MESSAGEMODE_SMALLPORTRAIT, callback=(self.SetPictureMode, MESSAGEMODE_SMALLPORTRAIT))
        menuParent.AddRadioButton(text=localization.GetByLabel(MESSAGEMODETEXTS[MESSAGEMODE_BIGPORTRAIT]), checked=settings.user.ui.Get('%s_mode' % self.name, 1) == MESSAGEMODE_BIGPORTRAIT, callback=(self.SetPictureMode, MESSAGEMODE_BIGPORTRAIT))
        menuParent.AddDivider()
        prefsName = 'chatWindowBlink_%s' % self.name
        doBlink = settings.user.ui.Get(prefsName, 1)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Chat/HighlightMyMessages'), checked=bool(settings.user.ui.Get('%s_myMsgHighlighted' % self.name, 0)), callback=(self.ToggleHighlight, 'myMsgHighlighted'))
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Chat/HighlightDustMessages'), checked=bool(settings.user.ui.Get('%s_dustHighlighted' % self.name, True)), callback=(self.ToggleHighlight, 'dustHighlighted'))
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Chat/BlinkOn'), checked=bool(doBlink), callback=(settings.user.ui.Set, prefsName, not doBlink))
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Chat/ShowTimestamp'), checked=bool(settings.user.ui.Get('timestampchat', 0)), callback=self.ToggleTimestamp)
        menuParent.AddDivider()
        menuParent.AddIconEntry(icon=ACTION_ICON, text=localization.GetByLabel('UI/Chat/ClearAllContent'), callback=self.ClearContent)

    def UserListMenu(self, menuParent):
        alwaysUserRecent = self.ShouldOnlyUseRecentList()
        addRecentCheckbox = False
        hint = ''
        if alwaysUserRecent:
            memberText = localization.GetByLabel('UI/Chat/MemberListRecentText')
            hint = localization.GetByLabel('UI/Chat/MemberListRecentSpeakers')
        elif sm.GetService('LSC').IsMemberless(self.channelID):
            memberText = localization.GetByLabel('UI/Chat/MemberListDelayedText')
            hint = localization.GetByLabel('UI/Chat/MemberListDelayed')
            addRecentCheckbox = True
        else:
            memberText = localization.GetByLabel('UI/Chat/MemberListImmediateText')
            hint = localization.GetByLabel('UI/Chat/MemberListImmediate')
        memberlistMode = bool(settings.user.ui.Get('%s_usermode' % self.name, True))
        menuParent.AddCheckBox(text=memberText, checked=bool(memberlistMode), callback=self.SetMemberListVisibility, hint=hint)
        if addRecentCheckbox:
            text = localization.GetByLabel('UI/Chat/OnlyShowRecentSpeakersText')
            if memberlistMode:
                callback = self.SetRecentState
            else:
                callback = False
            checked = bool(settings.user.ui.Get('%s_usersOnlyRecent' % self.name, True))
            hint = localization.GetByLabel('UI/Chat/OnlyShowRecentSpeakersHint')
            menuParent.AddCheckBox(text=text, checked=checked, callback=callback, hint=hint)
        showDustCharacters = settings.user.ui.Get('%s_dustCharacters' % self.name, 1)
        if memberlistMode:
            callback = self.SetDustCharacterVisibility
        else:
            callback = None
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Chat/DisplayDustCharacters'), checked=bool(showDustCharacters), callback=callback)
        showCompact = settings.user.ui.Get('chatCondensedUserList_%s' % self.name, False)
        menuParent.AddCheckBox(text=localization.GetByLabel('UI/Chat/ShowCompactMemberList'), checked=bool(showCompact), callback=(self.DisplayUserList, not showCompact))

    def AddSettingsOptionsToMenuParent(self, mParent):
        showSettings = False
        if isinstance(self.channelID, int) and sm.GetService('LSC').IsOperator(self.channelID):
            showSettings = True
        elif isinstance(self.channelID, tuple):
            channelType = self.channelID[0][0]
            if channelType in ('corpid', 'allianceid'):
                if session.corprole & const.corpRoleChatManager == const.corpRoleChatManager:
                    showSettings = True
            elif channelType == 'fleetid':
                if sm.GetService('fleet').IsBoss():
                    showSettings = True
        if showSettings:
            mParent.AddIconEntry(icon=ACTION_ICON, text=localization.GetByLabel('UI/Chat/OpenChannelSettingsWnd'), callback=self.__Settings)

    def AddVoiceOptionsToMenuParent(self, mParent):
        if sm.GetService('vivox').Enabled() and sm.GetService('vivox').LoggedIn():
            fleetChannels = ['fleet', 'wing', 'squad']
            excludedFromVoiceChannels = ['regionid',
             'solarsystemid',
             'constellationid',
             'allianceid',
             'warfactionid',
             'incursion']
            excludedFromVoice = False
            isFleetChannel = False
            if type(self.channelID) == types.TupleType:
                if util.IsNPC(self.channelID[0][1]):
                    excludedFromVoice = True
                for excludedChannelName in excludedFromVoiceChannels:
                    if self.channelID[0][0].startswith(excludedChannelName):
                        excludedFromVoice = True
                        break

                for fleetChannelName in fleetChannels:
                    if self.channelID[0][0].startswith(fleetChannelName):
                        isFleetChannel = True
                        break

            elif type(self.channelID) == types.IntType:
                excludedFromVoice = self.channelID >= 0 and self.channelID <= 1000
            else:
                raise RuntimeError('LSC only supports channel IDs of tuple or int type.')
            if not excludedFromVoice:
                if sm.GetService('vivox').IsVoiceChannel(self.channelID):
                    mParent.AddIconEntry(icon=ACTION_ICON, text=localization.GetByLabel('UI/Chat/LeaveAudio'), callback=self.VivoxLeaveAudio)
                    currentSpeakingChannel = sm.GetService('vivox').GetSpeakingChannel()
                    if type(currentSpeakingChannel) is types.TupleType:
                        currentSpeakingChannel = (currentSpeakingChannel,)
                    if currentSpeakingChannel != self.channelID:
                        mParent.AddIconEntry(icon=ACTION_ICON, text=localization.GetByLabel('UI/Chat/MakeSpeakingChannel'), callback=self.VivoxSetAsSpeakingChannel)
                elif isFleetChannel:
                    if sm.GetService('fleet').GetOptions().isVoiceEnabled:
                        mParent.AddIconEntry(icon=ACTION_ICON, text=localization.GetByLabel('UI/Chat/JoinAudio'), callback=self.VivoxJoinAudio)
                else:
                    mParent.AddIconEntry(icon=ACTION_ICON, text=localization.GetByLabel('UI/Chat/JoinAudio'), callback=self.VivoxJoinAudio)

    def SetPictureMode(self, pictureMode, *args):
        if self.messageMode == pictureMode:
            return
        self.messageMode = pictureMode
        self.LoadMessages()
        settings.user.ui.Set('%s_mode' % self.name, pictureMode)
        uicore.registry.SetFocus(self)

    def SetMemberListVisibility(self, *args):
        memberListChecked = bool(settings.user.ui.Get('%s_usermode' % self.name, True))
        memberListChecked = not memberListChecked
        settings.user.ui.Set('%s_usermode' % self.name, memberListChecked)
        self.SetupUserlist(memberListChecked)

    def SetRecentState(self, *args):
        recentChecked = bool(settings.user.ui.Get('%s_usersOnlyRecent' % self.name, True))
        recentChecked = not recentChecked
        settings.user.ui.Set('%s_usersOnlyRecent' % self.name, recentChecked)
        self.SetupUserlist(self.showUserList)

    def SetDustCharacterVisibility(self, *args):
        showDustCharacters = settings.user.ui.Get('%s_dustCharacters' % self.name, True)
        settings.user.ui.Set('%s_dustCharacters' % self.name, not showDustCharacters)
        if self.showUserList:
            recent = self.ShouldDisplayRecent()
            self.InitUsers(onlyRecent=recent)

    def ToggleTimestamp(self, *args):
        c = settings.user.ui.Get('timestampchat', 0)
        settings.user.ui.Set('timestampchat', not c)
        channelWindow = sm.GetService('LSC').GetChannelWindow(self.channelID)
        if channelWindow:
            channelWindow.LoadMessages()

    def ToggleHighlight(self, configNamePart):
        c = settings.user.ui.Get('%s_%s' % (self.name, configNamePart), True)
        settings.user.ui.Set('%s_%s' % (self.name, configNamePart), not c)
        channelWindow = sm.GetService('LSC').GetChannelWindow(self.channelID)
        if channelWindow:
            channelWindow.LoadMessages()

    def OnOutputResize(self, clipperWidth, clipperHeight, *args, **kw):
        self.resizeTimer = base.AutoTimer(100, self.DelayedOutputResize, clipperWidth, clipperHeight)

    def DelayedOutputResize(self, width, height):
        self.resizeTimer = None
        uicls.BasicDynamicScroll.OnContentResize(self.output, width, height)

    def GetStackClass(self):
        return form.LSCStack

    def __GetMOTD(self):
        if isinstance(self.channelID, int) or self.channelID[0][0] in ('corpid', 'allianceid'):
            if sm.IsServiceRunning('LSC') and self.channelID in sm.services['LSC'].channels:
                return sm.services['LSC'].channels[self.channelID].info.motd or ''
        elif self.channelID[0][0] == 'fleetid':
            return sm.GetService('fleet').GetMotd()
        return ''

    def SpeakMOTD(self, whine = False):
        motd = self.__GetMOTD()
        if motd or whine:
            self.Speak(localization.GetByLabel('UI/Chat/ChannelMotd', motd=motd), const.ownerSystem)

    def Spam(self):
        while getattr(self, 'spam', 0) == 1:
            self.__Output('a b c d f g h i j k l m n o p r s t u v x y z asd\xe6lf akjdf\xe6laksjdf \xe6lasdfkj \xe6al kfj\xe6laksfj \xe6laskdfjal\xe6sk fja\xe6lskdfj a\xe6lsdfkja \xe6ldfkja\xe6dkj\xe6alsdfk jadfkja\xe6lfk\xe6aldfkja\xe6slfkd a\xe6ldfkja\xe6ldfkja\xe6ldfkjadfl\xe6k ', eve.session.charid, 1)
            blue.pyos.synchro.Yield()

    def Restart(self, channelID):
        self.channelID = channelID
        self.windowCaption = chat.GetDisplayName(channelID).split('\\')[-1]
        self.SetupUserlist(self.showUserList)
        if self.messages:
            self.messages = [ msg for msg in self.messages if msg[2] != const.ownerSystem or not msg[1].startswith(localization.GetByLabel('UI/Chat/ChannelWindow/ChannelChangedTo')) ]
            self.LoadMessages()
        try:
            if util.IsMemberlessLocal(channelID):
                self.Speak(localization.GetByLabel('UI/Chat/ChannelWindow/ChannelListUnavailable'), const.ownerSystem)
            elif type(self.channelID) != types.IntType and self.channelID[0][0] == 'constellationid' and util.IsWormholeSystem(eve.session.solarsystemid2):
                self.Speak(localization.GetByLabel('UI/Chat/NoChannelAccessWormhole'), const.ownerSystem)
            else:
                self.Speak(localization.GetByLabel('UI/Chat/ChannelWindow/ChannelChangedToChannelName', channelName=chat.GetDisplayName(channelID, systemOverride=1).split('\\')[-1]), const.ownerSystem)
            self.SpeakMOTD()
        except:
            log.LogException()
            sys.exc_clear()

    def RefreshVoiceStatus(self, statusData):
        if len(statusData) == 0:
            return
        for each in statusData:
            charID, status, uri = each
            entry = self.GetUserEntry(int(charID))
            if not entry:
                continue
            entry.voiceStatus = status
            if entry.panel:
                entry.panel.SetVoiceIcon(status, charID in self.voiceOnlyMembers)

    def VoiceIconChange(self, charID, status):
        if status == vivoxConstants.NOTJOINED and charID in self.voiceOnlyMembers:
            self.voiceOnlyMembers.remove(charID)
            self.DelMember(charID)
            return
        entry = self.GetUserEntry(int(charID))
        if not entry:
            if sm.GetService('LSC').IsMemberless(self.channelID) and status != vivoxConstants.TALKING:
                return
            if charID == session.charid:
                if status != vivoxConstants.TALKING:
                    return
            else:
                self.voiceOnlyMembers.append(charID)
            ownerInfo = cfg.eveowners.Get(charID)
            self.userlist.AddEntries(-1, [listentry.Get(self.userEntry, {'charID': charID,
              'info': ownerInfo,
              'color': None,
              'channelID': self.channelID,
              'voiceStatus': status,
              'voiceOnly': charID != session.charid,
              'charIndex': ownerInfo.name.lower()})])
            return
        entry.voiceStatus = status
        if entry.panel:
            entry.panel.SetVoiceIcon(status, charID in self.voiceOnlyMembers)

    def OnSpeakingEvent(self, charID, channelID, isSpeaking):
        if isSpeaking and channelID == self.channelID and settings.public.audio.Get('talkMoveToTopBtn', 0):
            self.MoveToTop(charID)

    def OnPortraitCreated(self, charID):
        if self.destroyed or self.state == uiconst.UI_HIDDEN or self.output is None:
            return
        UI_HIDDEN = uiconst.UI_HIDDEN
        for node in self.output.GetNodes():
            if not node.panel or node.panel.state == UI_HIDDEN:
                continue
            if charID == node.charid and not node.panel.picloaded:
                node.panel.LoadPortrait(orderIfMissing=False)

        if self.userlist.state != UI_HIDDEN:
            userNode = self.GetUserEntry(charID)
            if userNode and userNode.panel:
                if not userNode.panel.picloaded:
                    userNode.panel.LoadPortrait(orderIfMissing=False)

    def MoveToTop(self, charid):
        entry = self.GetUserEntry(int(charid))
        if entry is not None:
            self.userlist.ChangeNodeIndex(0, entry)

    def GetUserEntry(self, charID):
        for each in self.userlist.GetNodes():
            if each.charID == charID:
                return each

    def OpenChannelWindow(self, *args):
        form.Channels.Open()

    def ChangeFont(self, add = 0, *args):
        if self.changingfont:
            return
        fontsize = settings.user.ui.Get('chatfontsize_%s' % self.name, 12)
        if add <= -1 and min(fontsize + add, fontsize - add) < 9 or add >= 1 and max(fontsize + add, fontsize - add) > 28:
            return
        newsize = fontsize + add
        self.changingfont = 1
        self.fontsize = newsize
        self.letterSpace = 0
        if self.fontsize <= fontConst.EVE_SMALL_FONTSIZE:
            self.letterSpace = 1
        self.LoadMessages()
        self.input.SetDefaultFontSize(newsize)
        settings.user.ui.Set('chatfontsize_%s' % self.name, newsize)
        self.changingfont = 0

    def OnEndMinimize_(self, *args):
        self.OnTabDeselect()

    def OnEndMaximize_(self, *args):
        self.OnTabSelect()

    def OnInputSizeChanged(self):
        settings.user.ui.Set('chatinputsize_%s' % self.name, self.input.height)

    def __Settings(self, *args):
        uthread.new(sm.GetService('LSC').Settings, self.channelID)

    def GetMenu(self, *args):
        m = uicls.Window.GetMenu(self)
        prefsName = 'chatWindowBlink_%s' % self.name
        if settings.user.ui.Get(prefsName, 1):
            m.append((uiutil.MenuLabel('UI/Chat/BlinkOff'), settings.user.ui.Set, (prefsName, 0)))
        else:
            m.append((uiutil.MenuLabel('UI/Chat/BlinkOn'), settings.user.ui.Set, (prefsName, 1)))
        return m

    def DisplayUserList(self, condensed = False, *args):
        prefsName = 'chatCondensedUserList_%s' % self.name
        settings.user.ui.Set(prefsName, condensed)
        self.SetUserEntryType()
        if self.showUserList:
            recent = self.ShouldDisplayRecent()
            self.InitUsers(onlyRecent=recent)

    def VivoxJoinAudio(self, *args):
        sm.GetService('vivox').JoinChannel(self.channelID)
        sm.GetService('vivox').SetSpeakingChannel(self.channelID)

    def VivoxLeaveAudio(self, *args):
        sm.GetService('vivox').LeaveChannel(self.channelID)
        self.DelVoiceUsers(self.voiceOnlyMembers)

    def VivoxSetAsSpeakingChannel(self, *args):
        sm.GetService('vivox').SetSpeakingChannel(self.channelID)

    def VivoxMuteMe(self, *args):
        sm.GetService('vivox').Mute(1)

    def VivoxLeaderGag(self, *args):
        sm.GetService('fleet').SetVoiceMuteStatus(1, self.channelID)

    def VivoxLeaderUngag(self, *args):
        sm.GetService('fleet').SetVoiceMuteStatus(0, self.channelID)

    def OnDropData(self, dragObj, nodes):
        self.OnDropCharacter(dragObj, nodes)

    def OnDropCharacter(self, dragObj, nodes):
        if not isinstance(self.channelID, int):
            return
        for node in nodes[:5]:
            if node.Get('__guid__', None) not in uiutil.AllUserEntries():
                return
            charID = node.charID
            if util.IsCharacter(charID):
                sm.GetService('LSC').Invite(charID, self.channelID)

    def _OnClose(self, *args):
        if getattr(self, 'closing', 0):
            return
        self.closing = 1
        self.output = None
        self.input = None
        self.userlist = None
        self.messages = []
        self._userlistCleanupTimer = None
        if self._mouseUpCookie:
            uicore.event.UnregisterForTriuiEvents(self._mouseUpCookie)
        self._mouseUpCookie = None
        if self.logfile is not None:
            self.logfile.Close()
            self.logfile = None
        if sm.IsServiceRunning('LSC'):
            sm.GetService('LSC').LeaveChannel(self.channelID, destruct=0)
            sm.GetService('vivox').LeaveChannel(self.channelID)

    def RenameChannel(self, newName):
        self.windowCaption = newName.split('\\')[-1]
        self.UpdateCaption()

    def UpdateCaption(self, startingup = 0, localEcho = 0):
        if self.channelInitialized:
            label = chat.GetDisplayName(self.channelID).split('\\')[-1]
            label.replace('conversation', 'conv.')
            label.replace('channel', 'ch.')
            if type(self.channelID) == types.IntType or self.channelID[0] not in ('global', 'regionid', 'constellationid'):
                self.SetEveAndDustCounters(label)
            else:
                self.SetCaption(label)
                self.capsuleerCont.display = False
                self.dustMercCont.display = False
                self.combinedCont.display = False

    def SetEveAndDustCounters(self, channelLabel, *args):
        label = channelLabel
        showingCounters = False
        if sm.GetService('LSC').IsMemberless(self.channelID):
            memberCount = sm.GetService('LSC').GetMemberCount(self.channelID)
            if memberCount > 2:
                label += ' [%d]' % memberCount
                if self.memberCount != memberCount:
                    self.memberCount = memberCount
                    self.combinedIconText.text = memberCount
                    self.combinedCont.width = self.combinedIconText.left + self.combinedIconText.textwidth
                self.capsuleerCont.display = False
                self.dustMercCont.display = False
                self.combinedCont.display = True
                showingCounters = True
        else:
            eveMemberCount, dustMemberCount = sm.GetService('LSC').GetMemberCountForEVEAndDust(self.channelID)
            if eveMemberCount > 2 or dustMemberCount > 2:
                label += ' [%d]' % eveMemberCount
                if eveMemberCount != self.eveMemberCount:
                    self.eveMemberCount = eveMemberCount
                    self.capsuleerIconText.text = eveMemberCount
                    self.capsuleerCont.width = self.capsuleerIconText.left + self.capsuleerIconText.textwidth + 12
                if dustMemberCount != self.dustMemberCount:
                    self.dustMemberCount = dustMemberCount
                    self.dustMercIconText.text = dustMemberCount
                    self.dustMercCont.width = self.dustMercIconText.left + self.dustMercIconText.textwidth + 4
                self.capsuleerCont.display = True
                self.dustMercCont.display = True
                self.combinedCont.display = False
                showingCounters = True
        self.SetCaption(label)
        if not showingCounters:
            self.capsuleerCont.display = False
            self.dustMercCont.display = False
            self.combinedCont.display = False

    def SetupUserlist(self, showUserList):
        if self.destroyed:
            return
        self.showUserList = showUserList
        if not showUserList:
            self.userlist.Clear()
            self.userlist.state = self.sr.userlistdiv.state = uiconst.UI_HIDDEN
        else:
            minW = 50
            maxW = 200
            self.userlist.width = min(maxW, max(minW, self.userlist.width))
            self.userlist.state = uiconst.UI_PICKCHILDREN
            self.sr.userlistdiv.state = uiconst.UI_NORMAL
            recent = self.ShouldDisplayRecent()
            self.InitUsers(onlyRecent=recent)
        if self.channelInitialized and not self.destroyed:
            self.LoadMessages()

    def ShouldDisplayRecent(self, *args):
        if self.ShouldOnlyUseRecentList():
            return True
        if sm.GetService('LSC').IsMemberless(self.channelID):
            onlyDisplayRecent = bool(settings.user.ui.Get('%s_usersOnlyRecent' % self.name, True))
            return onlyDisplayRecent
        return False

    def ShouldOnlyUseRecentList(self, *args):
        if type(self.channelID) != types.IntType and self.channelID[0][0] in ('global', 'regionid', 'constellationid'):
            return True
        return False

    def RegisterFocus(self, edit, *args):
        sm.GetService('focus').SetFocusChannel(self)

    def SetCharFocus(self, char):
        uicore.registry.SetFocus(self.input)
        uix.Flush(uicore.layer.menu)
        if char is not None:
            self.input.OnChar(char, 0)

    def OnTabDeselect(self):
        if self.channelInitialized and not self.destroyed:
            self.UnloadMessages()
            if getattr(self, 'unloadUserlistScrollProportion', None) is None:
                self.unloadUserlistScrollProportion = self.userlist.GetScrollProportion()
            self.userlist.Clear()

    def OnTabSelect(self):
        if getattr(self, 'channelInitialized', False) and not self.destroyed:
            uicore.registry.SetFocus(self.input)
            if self.input is not None:
                self.input.DoSizeUpdate()
            self.LoadMessages()
            if self.showUserList:
                recent = self.ShouldDisplayRecent()
                self.InitUsers(onlyRecent=recent)

    def LoadMessages(self):
        if not self.output or self.state == uiconst.UI_HIDDEN:
            return
        self.loadQueue = 1
        if self.loadingmessages:
            return
        self.loadingmessages = 1
        uthread.new(self._LoadMessages)
        self.loadingmessages = 0

    def _LoadMessages(self):
        if self.destroyed:
            return
        try:
            spammers = getattr(sm.GetService('LSC'), 'spammerList', set())
            while not self.destroyed and self.loadQueue and self.state != uiconst.UI_HIDDEN:
                self.loadQueue = 0
                if self.destroyed:
                    break
                portion = self.output.GetScrollProportion() or getattr(self, 'unloadScrollProportion', 0.0)
                self.unloadScrollProportion = None
                scrollList = []
                for each in self.messages:
                    if each[2] not in spammers:
                        scrollList.append(self.GetChatEntry(each, each[2] == eve.session.charid))

                log.LogInfo('About to load', len(scrollList), 'entries to chat output of channel', self.channelID)
                self.output.Clear()
                self.output.AddNodes(0, scrollList)
                if portion:
                    self.output.ScrollToProportion(portion)

        finally:
            if not self.destroyed:
                self.loadingmessages = 0

    def UnloadMessages(self):
        if self.loadingmessages or not self.output:
            return
        if getattr(self, 'unloadScrollProportion', None) is None:
            self.unloadScrollProportion = self.output.GetScrollProportion()
        self.output.Clear()

    def GetChatEntry(self, msg, localEcho = False):
        who, txt, charid, time, colorkey = msg
        return listentry.Get('ChatEntry', {'text': chat.FormatTxt(msg, localEcho),
         'mode': self.messageMode,
         'fontsize': self.fontsize,
         'letterspace': self.letterSpace,
         'charid': charid,
         'channelid': self.channelID,
         'channelName': self.name,
         'msg': msg,
         'textbuff': None,
         'channelMenu': self.GetOutputMenu})

    def __LocalEcho(self, txt):
        self.__Output(txt, eve.session.charid, 1)

    def Speak(self, txt, charid, localEcho = 0):
        self.__Output(txt, charid, localEcho)

    def __Output(self, txt, charid, localEcho):
        blink = charid not in (eve.session.charid, const.ownerSystem)
        colorkey = 0
        if charid == eve.session.charid:
            if not localEcho:
                self.waitingForReturn = 0
                return
            colorkey = eve.session.role
        elif charid == const.ownerSystem:
            colorkey = service.ROLE_ADMIN
        elif type(charid) not in types.StringTypes:
            mi = sm.GetService('LSC').GetMemberInfo(self.channelID, charid)
            if mi:
                colorkey = mi.role
        if not localEcho and IsSpam(txt):
            return
        txt = self.CompleteAutoLinks(txt)
        self.UpdateCaption(localEcho=localEcho)
        if isinstance(charid, basestring):
            who = charid
        else:
            who = cfg.eveowners.Get(charid).name
        time = blue.os.GetWallclockTime()
        if self.destroyed:
            return
        if self.logfile is not None and self.logfile.size > 0:
            line = '[%20s ] %s > %s\r\n' % (util.FmtDate(time), who, uiutil.StripTags(txt).replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&'))
            try:
                self.logfile.Write(line.encode('utf-16'))
            except IOError:
                log.LogException(toAlertSvc=0)
                sys.exc_clear()

        msg = [who,
         txt,
         charid,
         time,
         colorkey]
        updateOutput = bool(self.state != uiconst.UI_HIDDEN)
        self.messages.append(msg)
        if len(self.messages) >= MAXMSGS:
            self.messages.pop(0)
            if self.output.GetNodes():
                self.output.RemoveNodes([self.output.GetNodes()[0]])
        if updateOutput:
            self.output.AddNodes(-1, [self.GetChatEntry(msg, localEcho)])
        if settings.user.ui.Get('chatWindowBlink_%s' % self.name, 1) and blink:
            self.Blink()
            if self.state == uiconst.UI_HIDDEN or self.IsMinimized():
                self.SetBlinking()

    def ValidatePaste(self, text):
        text = text.replace('<t>', '  ')
        text = uiutil.StripTags(text, ignoredTags=['b', 'i', 'u'])
        return text

    def CompleteAutoLinks(self, text):
        filledText = ''
        match = showInfoComplete.search(text)
        if match is None:
            return text
        while match is not None:
            pretext = match.group('pretext')
            typeID = match.group('typeID')
            seperator = match.group('seperator')
            itemID = match.group('itemID')
            itemName = match.group('itemName')
            posttext = match.group('posttext')
            groupID = cfg.invtypes.Get(typeID).groupID
            if itemID == '' and typeID != '':
                filledName = cfg.invtypes.Get(typeID).name
            elif groupID in [const.groupCharacter, const.groupCorporation]:
                filledName = cfg.eveowners.Get(itemID).name
            elif groupID == const.groupSolarSystem:
                filledName = cfg.evelocations.Get(itemID).name
            elif groupID == const.groupStation:
                orbitName = cfg.evelocations.Get(cfg.stations.Get(itemID).orbitID).name
                longMoon = localization.GetByLabel('UI/Locations/LocationMoonLong')
                shortMoon = localization.GetByLabel('UI/Locations/LocationMoonShort')
                orbitName = orbitName.replace(longMoon, shortMoon).replace(longMoon.lower(), shortMoon.lower())
                filledName = localization.GetByLabel('UI/Chat/StationAutoLink', orbitName=orbitName)
            else:
                filledName = match.group('itemName')
            filledText += '%s%s%s%s>%s%s' % (pretext,
             typeID,
             seperator,
             itemID,
             filledName,
             posttext)
            text = text[match.span()[1]:]
            match = showInfoComplete.search(text)

        filledText = filledText + text
        return filledText

    def InputKeyUp(self, *args):
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        if shift:
            return
        if self.waitingForReturn and blue.os.GetWallclockTime() - self.waitingForReturn < MIN:
            txt = self.input.GetValue(html=0)
            txt = txt.rstrip()
            cursorPos = -1
            self.input.SetValue(txt, cursorPos=cursorPos)
            eve.Message('uiwarning03')
            return
        NUM_SECONDS = 4
        if session.userType == 23 and (type(self.channelID) != types.IntType or self.channelID < 2100000000 and self.channelID > 0):
            lastMessageTime = long(getattr(self, 'lastMessageTime', blue.os.GetWallclockTime() - 1 * MIN))
            if blue.os.GetWallclockTime() - lastMessageTime < NUM_SECONDS * SEC:
                eve.Message('LSCTrialRestriction_SendMessage', {'sec': (NUM_SECONDS * SEC - (blue.os.GetWallclockTime() - lastMessageTime)) / SEC})
                return
            setattr(self, 'lastMessageTime', blue.os.GetWallclockTime())
        txt = self.input.GetValue(html=0)
        self.input.SetValue('')
        txt = txt.strip()
        while txt.endswith('<br>'):
            txt = txt[:-4]

        txt = txt.strip()
        while txt.startswith('<br>'):
            txt = txt[4:]

        txt = txt.strip()
        if not txt or len(txt) <= 0:
            return
        if sm.GetService('LSC').IsLanguageRestricted(self.channelID):
            try:
                if unicode(txt) != unicode(txt).encode('ascii', 'replace'):
                    uicore.registry.BlockConfirm()
                    eve.Message('LscLanguageRestrictionViolation')
                    return
            except:
                log.LogTraceback('Gurgle?')
                sys.exc_clear()
                eve.Message('uiwarning03')
                return

        if boot.region == 'optic':
            try:
                bw = str(localization.GetByLabel('UI/Chat/ChannelWindow/ChinaServerBannedWords')).decode('utf-7')
                banned = [ word for word in bw.split() if word ]
                for bword in banned:
                    if txt.startswith('/') and not (txt.startswith('/emote') or txt.startswith('/me')):
                        txt = txt
                    else:
                        txt = txt.replace(bword, '*')

            except Exception:
                log.LogTraceback('Borgle?')
                sys.exc_clear()

        if not sm.GetService('LSC').IsSpeaker(self.channelID):
            access = sm.GetService('LSC').GetMyAccessInfo(self.channelID)
            if access[1]:
                if access[1].reason:
                    reason = access[1].reason
                else:
                    reason = localization.GetByLabel('UI/Chat/NotSpecified')
                if access[1].admin:
                    admin = access[1].admin
                else:
                    admin = localization.GetByLabel('UI/Chat/NotSpecified')
                if access[1].untilWhen:
                    borki = localization.GetByLabel('UI/Chat/CannotSpeakOnChannelUntil', reason=reason, untilWhen=access[1].untilWhen, admin=admin)
                else:
                    borki = localization.GetByLabel('UI/Chat/CannotSpeakOnChannel', reason=reason, admin=admin)
            else:
                borki = localization.GetByLabel('UI/Chat/CannotSpeakOnChannel', reason=localization.GetByLabel('UI/Chat/NotSpecified'), admin=localization.GetByLabel('UI/Chat/NotSpecified'))
            self.__LocalEcho(borki)
        if txt != '' and txt.replace('\r', '').replace('\n', '').replace('<br>', '').replace(' ', '').replace('/emote', '').replace('/me', '') != '':
            if txt.startswith('/me'):
                txt = '/emote' + txt[3:]
            spoke = 0
            if self.inputs[-1] != txt:
                self.inputs.append(txt)
            self.inputIndex = None
            nobreak = uiutil.StripTags(txt.replace('<br>', ''))
            if nobreak.startswith('/') and not (nobreak.startswith('/emote') or nobreak == '/'):
                for commandLine in uiutil.StripTags(txt.replace('<br>', '\n')).split('\n'):
                    try:
                        slashRes = uicore.cmd.Execute(commandLine)
                        if slashRes is not None:
                            sm.GetService('logger').AddText('slash result: %s' % slashRes, 'slash')
                        elif nobreak.startswith('/tutorial') and eve.session and eve.session.role & service.ROLE_GML:
                            sm.GetService('tutorial').SlashCmd(commandLine)
                        elif eve.session and eve.session.role & ROLE_SLASH:
                            if commandLine.lower().startswith('/mark'):
                                sm.StartService('logger').LogError('SLASHMARKER: ', (eve.session.userid, eve.session.charid), ': ', commandLine)
                            slashRes = sm.GetService('slash').SlashCmd(commandLine)
                            if slashRes is not None:
                                sm.GetService('logger').AddText('slash result: %s' % slashRes, 'slash')
                        self.__LocalEcho('/slash: ' + commandLine)
                    except:
                        self.__LocalEcho('/slash failed: ' + commandLine)
                        raise 

            else:
                stext = uiutil.StripTags(txt, ignoredTags=['b',
                 'i',
                 'u',
                 'url',
                 'br',
                 'loc'])
                try:
                    if type(self.channelID) != types.IntType and self.channelID[0][0] in ('constellationid', 'regionid') and util.IsWormholeSystem(eve.session.solarsystemid2):
                        self.__Output(localization.GetByLabel('UI/Chat/NoChannelAccessWormhole'), 1, 1)
                        return
                    self.waitingForReturn = blue.os.GetWallclockTime()
                    stext = self.ConstrainChatMessage(stext)
                    self.__LocalEcho(stext)
                    if not IsSpam(stext):
                        sm.GetService('LSC').SendMessage(self.channelID, stext)
                    else:
                        self.waitingForReturn = 0
                except:
                    self.waitingForReturn = 0
                    raise 

    def ConstrainChatMessage(self, message):
        if type(message) not in types.StringTypes:
            message = str(message)
        strippedMessage = uiutil.StripTags(message)
        if len(strippedMessage) > const.CHT_MAX_STRIPPED_INPUT or len(message) > const.CHT_MAX_INPUT:
            message = strippedMessage[:const.CHT_MAX_STRIPPED_INPUT] + '...'
        return message

    def CtrlDown(self, editctrl, *args):
        self.BrowseInputs(1)

    def CtrlUp(self, editctrl, *args):
        self.BrowseInputs(-1)

    def BrowseInputs(self, updown):
        if self.inputIndex is None:
            self.inputIndex = len(self.inputs) - 1
        else:
            self.inputIndex += updown
        if self.inputIndex < 0:
            self.inputIndex = len(self.inputs) - 1
        elif self.inputIndex >= len(self.inputs):
            self.inputIndex = 0
        self.input.SetValue(self.inputs[self.inputIndex], cursorPos=-1)

    def InitUsers(self, onlyRecent):
        members = sm.GetService('LSC').GetMembers(self.channelID, onlyRecent)
        if getattr(self, 'userEntry', None):
            self.SetUserEntryType()
        self.pendingUserNodes = {}
        if members is None:
            self.userlist.ShowHint('List not available')
        else:
            idsToPrime = set()
            for charID in members:
                if charID not in cfg.eveowners:
                    idsToPrime.add(charID)

            sm.GetService('bountySvc').PrimeOwnersFromMembers(members)
            if idsToPrime:
                cfg.eveowners.Prime(idsToPrime)
            scrollProportion = self.userlist.GetScrollProportion() or getattr(self, 'unloadUserlistScrollProportion', 0.0)
            self.unloadUserlistScrollProportion = None
            audioStatus = dict(sm.GetService('vivox').GetMemberVoiceStatus(self.channelID) or [])
            try:
                self.userlist.ShowHint()
                scrolllist = []
                doDisplayDustCharacters = settings.user.ui.Get('%s_dustCharacters' % self.name, True)
                for charID in members:
                    if not doDisplayDustCharacters:
                        isDustChar = util.IsDustCharacter(charID)
                        if isDustChar:
                            continue
                    member = members[charID]
                    ownerInfo = cfg.eveowners.Get(member.charID)
                    if member.charID in audioStatus:
                        voiceStatus = audioStatus.pop(member.charID)
                    else:
                        voiceStatus = None
                    charIndex = ownerInfo.name.lower()
                    scrolllist.append((charIndex, listentry.Get(self.userEntry, {'charID': member.charID,
                      'corpID': member.corpID,
                      'allianceID': member.allianceID,
                      'warFactionID': member.warFactionID,
                      'info': ownerInfo,
                      'color': GetColor(member.role),
                      'channelID': self.channelID,
                      'voiceStatus': voiceStatus,
                      'charIndex': charIndex})))

                if sm.GetService('LSC').IsMemberless(self.channelID):
                    for charID in audioStatus.keys():
                        if charID not in self.voiceOnlyMembers:
                            audioStatus.pop(charID)

                if len(audioStatus) > 0:
                    cfg.eveowners.Prime(audioStatus.keys())
                    for charID, voiceStatus in audioStatus.iteritems():
                        if charID == session.charid:
                            continue
                        ownerInfo = cfg.eveowners.Get(charID)
                        charIndex = ownerInfo.name.lower()
                        scrolllist.append((charIndex, listentry.Get(self.userEntry, {'charID': charID,
                          'info': cfg.eveowners.Get(charID),
                          'color': None,
                          'channelID': self.channelID,
                          'voiceStatus': voiceStatus,
                          'voiceOnly': True,
                          'charIndex': charIndex})))

                scrolllist = uiutil.SortListOfTuples(scrolllist)
                self.userlist.Clear()
                self.userlist.AddNodes(0, scrolllist)
                if scrollProportion:
                    self.userlist.ScrollToProportion(scrollProportion)
            except RuntimeError as e:
                if e.args[0] == 'dictionary changed size during iteration':
                    sys.exc_clear()
                    self.InitUsers(onlyRecent)
                    return
                raise e

    def SetUserEntryType(self):
        if settings.user.ui.Get('chatCondensedUserList_%s' % self.name, False):
            self.userEntry = 'ChatUserSimple'
        else:
            self.userEntry = 'ChatUser'

    def AddMember(self, *args, **keywords):
        if not sm.GetService('LSC').IsMemberless(self.channelID):
            self.__AddUser(*args, **keywords)

    def AddRecentSpeaker(self, *args, **keywords):
        if sm.GetService('LSC').IsMemberless(self.channelID):
            self.__AddUser(*args, **keywords)

    def UserlistSortingLocked(self):
        if self._userlistSortingLocked:
            return True
        mouseOver = uicore.uilib.mouseOver
        scrollContent = self.userlist.GetContentContainer()
        sortingLocked = uiutil.IsUnder(mouseOver, scrollContent) or mouseOver is scrollContent
        if sortingLocked:
            currentMousePos = (uicore.uilib.x, uicore.uilib.y)
            currentTime = blue.os.GetWallclockTime()
            lastUpdateData = self._userlistLockIdleData
            if lastUpdateData and currentMousePos == lastUpdateData[1] and lastUpdateData[0]:
                if blue.os.TimeDiffInMs(lastUpdateData[0], currentTime) > USERLISTLOCK_MOUSEIDLE_TIME:
                    sortingLocked = False
            else:
                self._userlistLockIdleData = (currentTime, currentMousePos)
        else:
            self._userlistLockIdleData = None
        return sortingLocked

    def __AddUser(self, charid, corpid, allianceid, warfactionid, refresh = 1, sort = 1, load = 1, color = None):
        if self.destroyed or not self.channelInitialized or not self.userlist:
            return
        if self.state != uiconst.UI_HIDDEN and self.userlist.state != uiconst.UI_HIDDEN:
            doDisplayDustCharacters = settings.user.ui.Get('%s_dustCharacters' % self.name, True)
            if not doDisplayDustCharacters and util.IsDustCharacter(charid):
                return
            self.userlist.ShowHint()
            ownerInfo = cfg.eveowners.Get(charid)
            idx = 0
            for each in self.userlist.GetNodes():
                if each.charID == charid:
                    if hasattr(each, 'voiceOnly'):
                        try:
                            self.DelVoiceUsers([charid])
                        except ValueError:
                            pass

                        break
                    return
                if util.CaseFoldCompare(each.info.name, ownerInfo.name) > 0:
                    break
                idx += 1

            audioStatus = dict(sm.GetService('vivox').GetMemberVoiceStatus(self.channelID) or [])
            if charid in audioStatus:
                voiceStatus = audioStatus[charid]
            else:
                voiceStatus = None
            userNode = listentry.Get(self.userEntry, {'charID': charid,
             'corpID': corpid,
             'allianceID': allianceid,
             'warFactionID': warfactionid,
             'info': ownerInfo,
             'color': color,
             'channelID': self.channelID,
             'voiceStatus': voiceStatus,
             'charIndex': ownerInfo.name.lower()})
            sortingLocked = self.UserlistSortingLocked()
            if sortingLocked:
                self.FlagUserlistDirty()
                if self.userlist.GetScrollRange():
                    self.pendingUserNodes[charid] = userNode
                else:
                    self.userlist.AddNodes(-1, [userNode])
            else:
                self.userlist.AddNodes(idx, [userNode])
        self.UpdateCaption()

    def LockUserlistSorting(self):
        self._userlistSortingLocked = True
        self._mouseUpCookie = uicore.uilib.RegisterForTriuiEvents(uiconst.UI_MOUSEUP, self.OnAnyMouseUp)

    def OnAnyMouseUp(self, *args, **kwds):
        uthread.new(self._OnAnyMouseUp, *args, **kwds)
        return True

    def _OnAnyMouseUp(self, mouseUp, *args, **kwds):
        if uiutil.IsUnder(mouseUp, uicore.layer.menu) and not mouseUp.destroyed:
            return True
        uicore.event.UnregisterForTriuiEvents(self._mouseUpCookie)
        self._userlistSortingLocked = False
        self._mouseUpCookie = None

    def CleanupUserlist(self):
        if not self._userlistDirty:
            self._userlistCleanupTimer = None
            return
        sortingLocked = self.UserlistSortingLocked()
        if sortingLocked:
            return
        self._userlistCleanupTimer = None
        self._userlistDirty = False
        if self._mouseUpCookie:
            uicore.event.UnregisterForTriuiEvents(self._mouseUpCookie)
        self._userlistSortingLocked = False
        self._mouseUpCookie = None
        if self.pendingUserNodes:
            addPending = self.pendingUserNodes.values()
            self.pendingUserNodes = {}
            self.userlist.AddNodes(-1, addPending)
        sortList = []
        removeList = []
        for each in self.userlist.GetNodes():
            if each.leavingUserlist:
                removeList.append(each)
            else:
                sortList.append((each.charIndex, each))

        if removeList:
            self.userlist.RemoveNodes(removeList, updateScroll=False)
        sortList = uiutil.SortListOfTuples(sortList)
        self.userlist.SetOrderedNodes(sortList)

    def FlagUserlistDirty(self):
        wasDirty = self._userlistDirty
        self._userlistDirty = True
        if self._userlistCleanupTimer is None:
            self._userlistCleanupTimer = base.AutoTimer(500, self.CleanupUserlist)
        if not wasDirty:
            uthread.new(self.BlinkUserList)

    def BlinkUserList(self):
        while self._userlistDirty:
            uicore.animations.FadeTo(self.sortLockFrame, startVal=0.0, endVal=0.2, duration=1.333, curveType=uiconst.ANIM_WAVE, loops=1, sleep=True)

    def RemoveUserNodes(self, nodes):
        sortingLocked = self.UserlistSortingLocked()
        if sortingLocked:
            for node in nodes:
                if node.panel:
                    node.panel.opacity = 0.25
                    node.panel.state = uiconst.UI_DISABLED
                node.leavingUserlist = True

            self.FlagUserlistDirty()
        else:
            self.userlist.RemoveNodes(nodes)

    def DelMember(self, *args, **keywords):
        if not sm.GetService('LSC').IsMemberless(self.channelID):
            self.__DelUser(*args, **keywords)

    def DelRecentSpeaker(self, *args, **keywords):
        self.__DelUser(*args, **keywords)

    @telemetry.ZONE_METHOD
    def __DelUser(self, charid):
        if self.state != uiconst.UI_HIDDEN and self.userlist.state != uiconst.UI_HIDDEN:
            for each in self.userlist.GetNodes():
                if each.charID == charid:
                    self.RemoveUserNodes([each])
                    break

        if charid in self.pendingUserNodes:
            del self.pendingUserNodes[charid]
        self.UpdateCaption()

    def DelVoiceUsers(self, charids):
        for charID in charids:
            if charID in self.voiceOnlyMembers:
                self.voiceOnlyMembers.remove(charID)
            if charID in self.pendingUserNodes:
                del self.pendingUserNodes[charID]

        entries = []
        for each in self.userlist.GetNodes():
            if each.charID in charids:
                entries.append(each)

        if entries:
            self.RemoveUserNodes(entries)
            self.UpdateCaption()

    def UserlistStartScale(self, *args):
        self.uss_w = self.userlist.width
        self.uss_x = uicore.uilib.x
        self.scaling = 1

    def UserlistScaling(self, *args):
        if self.scaling:
            minW = 50
            maxW = 200
            diffx = uicore.uilib.x - self.uss_x
            self.userlist.width = min(maxW, max(minW, self.uss_w - diffx))

    def UserlistEndScale(self, *args):
        self.scaling = 0
        settings.user.ui.Set('%s_userlistwidth' % self.name, self.userlist.width)
        self.LoadMessages()

    def GoTo(self, URL, data = None, args = {}, scrollTo = None):
        uicore.cmd.OpenBrowser(URL, data=data, args=args)

    def GetOutputMenu(self, *args):
        m = [(uiutil.MenuLabel('UI/Common/CopyAll'), self.CopyAll)]
        return m

    def CopyAll(self):
        t = ''
        for node in self.output.GetNodes():
            who, txt, charid, time, colorkey = node.msg
            timestr = ''
            if settings.user.ui.Get('timestampchat', 0):
                year, month, wd, day, hour, min, sec, ms = util.GetTimeParts(time)
                timestr = '[%02d:%02d:%02d] ' % (hour, min, sec)
            t += '%s%s > %s\r\n' % (timestr, who, txt.replace('&gt;', '>').replace('&amp;', '&'))

        blue.pyos.SetClipboardData(t)

    def ClearContent(self, *args):
        if self.output:
            self.output.Clear()
            self.messages = []

    def ShowMotdFromMenu(self, *args):
        self.SpeakMOTD()


class ChannelMenu(list):

    def __init__(self, channelID, charID):
        self.channelID = channelID
        self.charID = charID
        commands = []
        if charID != const.ownerSystem and sm.GetService('LSC').IsOperator(channelID):
            if not sm.GetService('LSC').IsOperator(channelID, charID):
                if sm.GetService('LSC').IsGagged(channelID, charID):
                    commands.append((uiutil.MenuLabel('UI/Chat/Unmute'), self.__UnGag))
                else:
                    commands.append((uiutil.MenuLabel('UI/Chat/Mute'), self.__Gag))
                commands.append((uiutil.MenuLabel('UI/Chat/Kick'), self.__Kick))
        self.append((uiutil.MenuLabel('UI/Chat/ReportIskSpammer'), self.ReportISKSpammer))
        if commands:
            self.append((uiutil.MenuLabel('UI/Chat/Channel'), commands))

    def ExcludeFromVoiceMute(self, *args):
        sm.GetService('fleet').ExcludeFromVoiceMute(self.charID, self.channelID)

    def AddToVoiceMute(self, *args):
        sm.GetService('fleet').AddToVoiceMute(self.charID, self.channelID)

    def ReportISKSpammer(self, *args):
        sm.GetService('menu').ReportISKSpammer(self.charID, self.channelID)

    def __Gag(self, *args):
        import chat
        format = []
        format.append({'type': 'bbline'})
        format.append({'type': 'push',
         'frame': 1})
        format.append({'type': 'edit',
         'key': 'minutes',
         'setvalue': 30,
         'label': localization.GetByLabel('UI/Chat/LengthMinutes'),
         'frame': 1,
         'maxLength': 5,
         'intonly': [0, 43200]})
        format.append({'type': 'push',
         'frame': 1})
        format.append({'type': 'textedit',
         'key': 'reason',
         'label': localization.GetByLabel('UI/Chat/Reason'),
         'frame': 1,
         'maxLength': 255})
        format.append({'type': 'push',
         'frame': 1})
        format.append({'type': 'btline'})
        retval = uix.HybridWnd(format, localization.GetByLabel('UI/Chat/GagCharacter', char=self.charID), 1, None, uiconst.OKCANCEL, minW=300, minH=160)
        if retval is not None:
            if retval['minutes']:
                untilWhen = blue.os.GetWallclockTime() + retval['minutes'] * MIN
            else:
                untilWhen = None
            sm.GetService('LSC').AccessControl(self.channelID, self.charID, chat.CHTMODE_LISTENER, untilWhen, retval['reason'])

    def __UnGag(self, *args):
        import chat
        mode = sm.GetService('LSC').GetChannelInfo(self.channelID).acl[0].mode
        if mode == 1:
            sm.RemoteSvc('LSC').AccessControl(self.channelID, self.charID, chat.CHTMODE_CONVERSATIONALIST)
        else:
            sm.GetService('LSC').AccessControl(self.channelID, self.charID, chat.CHTMODE_NOTSPECIFIED, blue.os.GetWallclockTime() - 30 * MIN, '')

    def __Kick(self, *args):
        import chat
        format = []
        format.append({'type': 'bbline'})
        format.append({'type': 'push',
         'frame': 1})
        format.append({'type': 'edit',
         'key': 'minutes',
         'setvalue': 30,
         'label': localization.GetByLabel('UI/Chat/LengthMinutes'),
         'frame': 1,
         'maxLength': 5,
         'intonly': [0, 43200]})
        format.append({'type': 'push',
         'frame': 1})
        format.append({'type': 'textedit',
         'key': 'reason',
         'label': localization.GetByLabel('UI/Chat/Reason'),
         'frame': 1,
         'maxLength': 255})
        format.append({'type': 'push',
         'frame': 1})
        format.append({'type': 'btline'})
        retval = uix.HybridWnd(format, localization.GetByLabel('UI/Chat/KickCharacter', char=self.charID), 1, None, uiconst.OKCANCEL, minW=300, minH=160)
        if retval is not None:
            if retval['minutes']:
                untilWhen = blue.os.GetWallclockTime() + retval['minutes'] * MIN
            else:
                untilWhen = None
            sm.GetService('LSC').AccessControl(self.channelID, self.charID, chat.CHTMODE_DISALLOWED, untilWhen, retval['reason'])


class ChatUser(listentry.User):
    __guid__ = 'listentry.ChatUser'
    notifyevents = listentry.User.__notifyevents__[:]
    if 'OnPortraitCreated' in notifyevents:
        notifyevents.remove('OnPortraitCreated')
    __notifyevents__ = notifyevents
    ENTRYHEIGHT = 37

    def Load(self, node, *args):
        if node.leavingUserlist:
            self.opacity = 0.25
            self.state = uiconst.UI_DISABLED
        node.GetMenu = self.GetNodeMenu
        listentry.User.Load(self, node, *args)
        self.SetVoiceIcon(node.voiceStatus, hasattr(node, 'voiceOnly') and node.voiceOnly)
        if uicore.uilib.mouseOver is self:
            self.Select()

    def GetNodeMenu(self, *args):
        channelWindow = uiutil.GetWindowAbove(self)
        if channelWindow and hasattr(channelWindow, 'LockUserlistSorting'):
            channelWindow.LockUserlistSorting()
        return [None] + ChannelMenu(self.sr.node.channelID, self.sr.node.charID)

    def OnDropData(self, dragObj, nodes):
        self.sr.node.scroll.GetContentContainer().OnDropData(dragObj, nodes)

    def SetVoiceIcon(self, state, voiceOnly = False):
        if self.sr.voiceIcon is None:
            self.sr.voiceIcon = uicls.Sprite(texturePath='res:/UI/Texture/classes/Chat/Chat.png', name='voiceIcon', parent=self, pos=(16, 3, 12, 12), align=uiconst.TOPRIGHT, idx=0, state=uiconst.UI_DISABLED, hint='')
        if self.sr.eveGateIcon is None:
            self.sr.eveGateIcon = uicls.Sprite(texturePath='res:/UI/Texture/classes/Chat/Chat_EveGate.png', name='voiceIcon', parent=self, pos=(14, 2, 6, 6), align=uiconst.TOPRIGHT, idx=0, state=uiconst.UI_HIDDEN, hint='')
        if state is None:
            self.sr.voiceIcon.state = uiconst.UI_HIDDEN
        else:
            if voiceOnly:
                self.sr.eveGateIcon.state = uiconst.UI_DISABLED
            else:
                self.sr.eveGateIcon.state = uiconst.UI_HIDDEN
            color = {0: (1.0, 1.0, 1.0),
             1: (0.0, 0.75, 0.0),
             2: (0.75, 0.0, 0.0)}.get(state, None)
            if color is None:
                self.sr.voiceIcon.state = uiconst.UI_HIDDEN
                log.LogWarn('Unsupported voice state flag', state)
                return
            self.sr.voiceIcon.SetRGB(*color)
            self.sr.voiceIcon.state = uiconst.UI_NORMAL
        return self.sr.voiceIcon


class ChatUserSimple(ChatUser):
    __guid__ = 'listentry.ChatUserSimple'
    ENTRYHEIGHT = 18

    def Startup(self, *args):
        listentry.ChatUser.Startup(self, *args)
        self.iconCont = uicls.Container(parent=self, align=uiconst.TOLEFT, width=16)

    def Load(self, node, *args):
        listentry.ChatUser.Load(self, node, *args)
        self.sr.namelabel.left = 16

    def SetRelationship(self, data):
        if self.destroyed:
            return
        if not data:
            return
        uix.SetStateFlag(self.iconCont, data, top=4)

    def LoadPortrait(self, orderIfMissing = True):
        pass


class ChatEntry(uicls.SE_BaseClassCore):
    __guid__ = 'listentry.ChatEntry'
    __notifyevents__ = []
    defaultTextProps = {'autoDetectCharset': True,
     'linkStyle': uiconst.LINKSTYLE_REGULAR,
     'state': uiconst.UI_NORMAL,
     'align': uiconst.TOTOP,
     'padRight': 5,
     'padLeft': 5}

    @classmethod
    def GetTextProperties(cls, node):
        textProps = cls.defaultTextProps
        textProps['fontsize'] = node.fontsize
        textProps['letterspace'] = node.letterspace
        if node.mode == 0:
            textProps['padTop'] = 0
            textProps['padLeft'] = 5
            textProps['specialIndent'] = 10
        else:
            textProps['padTop'] = 2
            textProps['specialIndent'] = 0
            if type(node.charid) not in types.StringTypes:
                if node.mode == 1:
                    textProps['padLeft'] = 43
                elif node.mode == 2:
                    textProps['padLeft'] = 75
        return (uicls.Label, textProps)

    def Startup(self, *args):
        self.sr.picParent = uicls.Container(name='picpar', parent=self, align=uiconst.TOPLEFT, width=34, height=34, left=2, top=2)
        self.sr.pic = uicls.Icon(parent=self.sr.picParent, align=uiconst.TOALL, padLeft=1, padTop=1, padRight=1, padBottom=1)
        self.picparFrame = uicls.Frame(bgParent=self.sr.picParent, color=(1.0, 1.0, 1.0, 0.125))

    def Load(self, node):
        self.picloaded = 0
        labelClass, textProps = self.GetTextProperties(node)
        if not self.sr.text:
            self.sr.text = labelClass(parent=self, idx=0, **textProps)
            self.sr.text.GetMenu = self.GetMenu
        else:
            self.sr.text.busy = 1
            for k, v in textProps.iteritems():
                setattr(self.sr.text, k, v)

        if node.mode and type(self.sr.node.charid) not in types.StringTypes:
            self.sr.picParent.width = self.sr.picParent.height = [34, 34, 66][node.mode]
            self.sr.picParent.state = uiconst.UI_NORMAL
            self.LoadPortrait()
        else:
            self.sr.picParent.state = uiconst.UI_HIDDEN
        self.sr.text.busy = 0
        self.sr.text.text = node.text
        self.AddEntryBackground(self.sr.node.charid, self.sr.node.channelName)

    def LoadPortrait(self, orderIfMissing = True):
        if self is None or self.destroyed:
            return
        if self.sr.node.charid == const.ownerSystem:
            self.sr.pic.LoadIcon('ui_6_64_7')
            return
        size = [32, 64][self.sr.node.mode - 1]
        if sm.GetService('photo').GetPortrait(self.sr.node.charid, size, self.sr.pic, orderIfMissing, callback=True):
            self.picloaded = 1

    def GetDynamicHeight(node, width):
        labelClass, props = ChatEntry.GetTextProperties(node)
        width = width - props['padLeft'] - props['padRight']
        try:
            textWidth, textHeight = labelClass.MeasureTextSize(node.text, width=width, **props)
        except:
            log.LogException('listentry.ChatEntry: Unable to determine dynamic height; NODE: %s, WIDTH: %s, PROPS: %s, LABELCLASS: %s' % (node,
             width,
             props,
             labelClass))
            textHeight = 73

        if node.mode == 0:
            return textHeight
        elif node.mode == 1:
            return max(41, textHeight + props['padTop'] * 2)
        else:
            return max(73, textHeight + props['padTop'] * 2)

    def GetMenu(self):
        m = []
        mouseOverUrl = self.sr.text.GetMouseOverUrl()
        if mouseOverUrl:
            if mouseOverUrl.startswith('showinfo:'):
                parsedArgs = uicls.BaseLink().ParseShowInfo(mouseOverUrl)
                if parsedArgs:
                    typeID, itemID, data = parsedArgs
                    try:
                        if typeID and itemID:
                            m = sm.StartService('menu').GetMenuFormItemIDTypeID(itemID, typeID, ignoreMarketDetails=0)
                            if cfg.invtypes.Get(typeID).Group().id == const.groupCharacter:
                                m += [None]
                                m += ChannelMenu(self.sr.node.channelid, itemID)
                        else:
                            m = uicls.BaseLink().GetLinkMenu(self.sr.text, mouseOverUrl.replace('&amp;', '&'))
                    except:
                        log.LogTraceback('failed to convert string to ids in chat entry:GetMenu')
                        sys.exc_clear()

            else:
                m = uicls.BaseLink().GetLinkMenu(self.sr.text, mouseOverUrl.replace('&amp;', '&'))
        m += [None, (uiutil.MenuLabel('UI/Common/Copy'), self.CopyText)]
        if self.sr.node.channelMenu:
            m += self.sr.node.channelMenu()
        return m

    def CopyText(self):
        who, txt, charid, time, colorkey = self.sr.node.msg
        timestr = ''
        if settings.user.ui.Get('timestampchat', 0):
            year, month, wd, day, hour, min, sec, ms = util.GetTimeParts(time)
            timestr = '[%02d:%02d:%02d] ' % (hour, min, sec)
        t = '%s%s > %s' % (timestr, who, txt.replace('&gt;', '>').replace('&amp;', '&'))
        blue.pyos.SetClipboardData(t)

    def AddEntryBackground(self, charID, channelName, *args):
        if util.IsDustCharacter(charID):
            blueColor = util.Color.DUST[:3]
            blueColor = (math.sqrt(blueColor[0]), math.sqrt(blueColor[1]), math.sqrt(blueColor[2]))
            if settings.user.ui.Get('%s_dustHighlighted' % channelName, True):
                gradientBackground = self.AddBackgroundGradient(blueColor)
            gradientFrame = self.AddFrameGradient(blueColor)
        elif charID == session.charid and settings.user.ui.Get('%s_myMsgHighlighted' % channelName, 0):
            gradientBackground = self.AddBackgroundGradient((0.65, 0.65, 0.65))
            gradientFrame = self.AddFrameGradient((0.9, 0.9, 0.9))

    def AddBackgroundGradient(self, color):
        backgroundGradient = uicls.Gradient2DSprite(bgParent=self, idx=0, name='gradient2d', rgbHorizontal=[0, 1], rgbVertical=[0, 1], rgbDataHorizontal=[color, color], rgbDataVertical=[color, color], rgbInterp='bezier', alphaHorizontal=[0, 1], alphaDataHorizontal=[1.0, 0.0], alphaVertical=[0, 0.5, 1], alphaDataVertical=[0.35, 0.05, 0.0], textureSize=16)
        return backgroundGradient

    def AddFrameGradient(self, color):
        frameGradient = uicls.Gradient2DSprite(parent=None, idx=0, name='frameGradient2d', rgbHorizontal=[0, 1], rgbVertical=[0, 1], rgbDataHorizontal=[color, color], rgbDataVertical=[color, color], rgbInterp='linear', alphaHorizontal=[0, 0.5, 1], alphaDataHorizontal=[1.0, 0.8, 0.15], alphaVertical=[0, 0.5, 1], alphaDataVertical=[1.0, 0.8, 0.15], textureSize=16)
        self.sr.picParent.background.insert(0, frameGradient)


def GetColor(role, asInt = 0):
    for colorkey, color, intCol in [(service.ROLE_PINKCHAT, '0xfff07cc7', LtoI(4293950663L)),
     (service.ROLE_QA, '0xff0099ff', LtoI(4278229503L)),
     (service.ROLE_WORLDMOD, '0xffac75ff', LtoI(4289492479L)),
     (service.ROLE_GMH, '0xffee6666', LtoI(4293813862L)),
     (service.ROLE_GML, '0xffffff20', LtoI(4294967072L)),
     (service.ROLE_CENTURION, '0xff00ff00', LtoI(4278255360L)),
     (service.ROLE_LEGIONEER, '0xff00ffcc', LtoI(4278255564L)),
     (service.ROLE_ADMIN, '0xffee6666', LtoI(4293813862L))]:
        if role & colorkey == colorkey:
            return [color, intCol][asInt]

    return ['0xffe0e0e0', LtoI(4292927712L)][asInt]


def FormatTxt(msg, localEcho = False):
    who, txt, charid, time, colorkey = msg
    if type(charid) in types.StringTypes:
        return txt
    color = GetColor(colorkey)
    timestr = ''
    if settings.user.ui.Get('timestampchat', 0):
        year, month, wd, day, hour, min, sec, ms = util.GetTimeParts(time)
        timestr = '<color=%s>[%02d:%02d:%02d]</color> ' % (color,
         hour,
         min,
         sec)
    if charid == const.ownerSystem:
        info = 'showinfo:5//%s' % (eve.session.solarsystemid or eve.session.solarsystemid2)
    else:
        info = 'showinfo:1373//%s' % charid
    if txt.startswith('/emote'):
        return '%s<url:%s><color=%s>* %s</color></url><color=%s> %s</color>' % (timestr,
         info,
         color,
         who,
         color,
         LinkURLs(txt[7:]))
    if txt.startswith('/slash') and localEcho:
        return '<color=0xff00dddd>%s</color>' % txt[1:]
    return '%s<url:%s><color=%s>%s</color></url><color=%s> &gt; %s</color>' % (timestr,
     info,
     color,
     who,
     color,
     LinkURLs(txt))


def LinkURLs(text):
    idx = 0
    parseParts = []
    match = alreadyURLOrTag.search(text)
    while match:
        start, end = match.span()
        parse = text[idx:start]
        if parse:
            parseParts.append((1, parse))
        notParse = text[start:end]
        parseParts.append((0, notParse))
        match = alreadyURLOrTag.search(text, end)
        idx = end

    leftOver = text[idx:]
    if leftOver:
        parseParts.append((1, leftOver))
    retText = ''
    for parseFlag, parseText in parseParts:
        if parseFlag == 0:
            retText += parseText
            continue
        normalizedText = unicodedata.normalize('NFKC', parseText)
        match = seemsURL.search(normalizedText)
        idx = 0
        while match:
            start, end = match.span()
            url = normalizedText[start:end]
            while url[-1] in ',.':
                url = url[:-1]
                end -= 1

            if not url.startswith('http'):
                url = 'http://' + url
            urlText = parseText[start:end]
            retText += parseText[idx:start] + '<url=' + url + '>' + urlText + '</url>'
            match = seemsURL.search(normalizedText, end)
            idx = end

        retText += parseText[idx:]

    return retText


exports = {'chat.GetColor': GetColor,
 'chat.FormatTxt': FormatTxt}