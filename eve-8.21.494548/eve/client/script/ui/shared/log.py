#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/shared/log.py
import blue
import uthread
import uix
import uiutil
import xtriui
import form
import log
import util
import listentry
import localization
import service
import os
import base
import sys
import uicls
import uiconst
import telemetry
import trinity
globals().update(service.consts)
MAX_MSGS = 256
SEC = 10000000L
MIN = SEC * 60L
HOUR = MIN * 60L
DAY = HOUR * 24L
COLORS_BY_TYPE = {'error': '<color=0xffeb3700>',
 'warning': '<color=0xffffd800>',
 'slash': '<color=0xffff5500>',
 'combat': '<color=0xffff0000>'}

class Logger(service.Service):
    __exportedcalls__ = {'AddMessage': [],
     'AddCombatMessage': [],
     'AddText': [],
     'GetLog': [ROLE_SERVICE]}
    __guid__ = 'svc.logger'
    __notifyevents__ = ['ProcessSessionChange']
    __servicename__ = 'logger'
    __displayname__ = 'Logger Client Service'
    __dependencies__ = []
    __update_on_reload__ = 0

    def Run(self, memStream = None):
        self.LogInfo('Starting Logger')
        self.broken = 0
        self.Reset()
        self.newfileAttempts = 0
        self.addmsg = []
        self.persistInterval = 1000
        self.combatMessagePeriod = 10000L * prefs.GetValue('combatMessagePeriod', 200)
        self.lastCombatMessage = 0
        self.inMovingMode = False
        self.frameCounterAndWindow = (None, None)
        self.cachedHitQualityText = {}
        self.notificationFontSize = settings.user.ui.Get('dmgnotifictions_fontsize', 12)
        uthread.new(self._PersistWorker)

    def Stop(self, memStream = None):
        self.DumpToLog()
        self.messages = []
        self.msglog = []
        self.addmsg = []

    def ProcessSessionChange(self, isremote, session, change):
        wnd = self.GetWnd()
        if not session.charid:
            self.Stop()

    def GetLog(self, maxsize = const.petitionMaxCombatLogSize, *args):
        log.LogInfo('Getting logfiles')
        self.DumpToLog()
        year, month, weekday, day, hour, minute, second, msec = blue.os.GetTimeParts(blue.os.GetWallclockTime())
        now = '%d%.2d%.2d' % (year, month, day)
        year, month, weekday, day, hour, minute, second, msec = blue.os.GetTimeParts(blue.os.GetWallclockTime() - DAY)
        yesterday = '%d%.2d%.2d' % (year, month, day)
        root = blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL) + '/EVE/logs/Gamelogs'
        logs = []
        for each in os.listdir(root):
            filename = os.path.join(root, each)
            fooname = filename[:-11]
            if fooname.endswith(now) or fooname.endswith(yesterday):
                logs.append((each, filename))

        logs.sort(reverse=True)
        ret = []
        bytesread = 0
        for k, filename in logs:
            f = None
            try:
                f = file(filename)
                tmp = f.read()
                f.close()
                line = '\n\n%s:\n%s' % (filename.encode('utf8', 'replace'), tmp)
                bytesread += len(line)
                ret.append(line)
                if bytesread > maxsize:
                    break
            except:
                log.LogException()
                sys.exc_clear()
                if f and not f.closed:
                    f.close()

        log.LogInfo('Getting logfiles done')
        ret.reverse()
        return ''.join(ret)[-maxsize:]

    def Reset(self):
        self.resettime = blue.os.GetWallclockTime()
        self.messages = []
        self.msglog = ['-' * 60 + '\n', '  %s\n' % localization.GetByLabel('UI/Accessories/Log/GameLog').encode('utf8', 'replace')]
        if eve.session.charid:
            self.msglog.append(('  %s: %s\n' % (localization.GetByLabel('UI/Accessories/Log/Listener'), cfg.eveowners.Get(eve.session.charid).name)).encode('utf8', 'replace'))
        self.msglog += [('  %s: %s\n' % (localization.GetByLabel('UI/Accessories/Log/SessionStarted'), util.FmtDate(self.resettime))).encode('utf8', 'replace'),
         '',
         '-' * 60 + '\n',
         '']
        self.DumpToLog()

    @telemetry.ZONE_METHOD
    def GetWnd(self):
        return form.Logger.GetIfOpen()

    @telemetry.ZONE_METHOD
    def GetWndWithFrameCounter(self, *args):
        frameCounter = trinity.GetCurrentFrameCounter()
        if frameCounter == self.frameCounterAndWindow[0]:
            return self.frameCounterAndWindow[1]
        wnd = self.GetWnd()
        self.frameCounterAndWindow = (frameCounter, wnd)
        return wnd

    def GetMessages(self):
        self.addmsg = []
        return self.messages

    def GetPendingMessages(self):
        retval = self.addmsg
        self.addmsg = []
        return retval

    def AddMessage(self, msg, msgtype = None):
        if msg.type == 'error' and not settings.user.ui.Get('logerrors', 0):
            return
        self.AddText(msg.text, msgtype or msg.type or 'notify', msg)

    @telemetry.ZONE_METHOD
    def AddCombatMessageFromDict(self, damageMessagesArgs):
        hitQuality = damageMessagesArgs['hitQuality']
        isBanked = damageMessagesArgs['isBanked']
        if hitQuality == 0:
            msgKey = 'AttackMiss'
        elif hitQuality > 0 and hitQuality <= 6:
            msgKey = 'AttackHits'
            try:
                hitQualityText = self.cachedHitQualityText[hitQuality]
            except KeyError:
                hitQualityText = localization.GetByLabel('UI/Inflight/HitQuality%s' % hitQuality)
                self.cachedHitQualityText[hitQuality] = hitQualityText

            damageMessagesArgs['hitQualityText'] = hitQualityText
        else:
            msgKey = 'AttackHits'
            hitQualityText = ''
            damageMessagesArgs['hitQualityText'] = hitQualityText
        attackType = damageMessagesArgs.get('attackType', 'me')
        if attackType == 'otherPlayer':
            msgKey += 'RD'
        elif attackType == 'otherPlayerWeapons':
            msgKey += 'R'
        elif attackType == 'me':
            if isBanked:
                msgKey += 'Banked'
        else:
            log.LogError('attackType not valid! attackType = ' + attackType)
            return
        for argName in ('source', 'target', 'owner'):
            if argName not in damageMessagesArgs:
                continue
            slimItem = None
            objectName = ''
            typeName = ''
            tickerText = ''
            if argName == 'owner':
                ownerTypeID, ownerID = damageMessagesArgs[argName]
                if ownerTypeID != OWNERID:
                    continue
                objectID = damageMessagesArgs.get('attackerID', None)
                if objectID is None:
                    continue
            else:
                objectID = damageMessagesArgs[argName]
            bracket = sm.GetService('bracket').GetBracket(objectID)
            if bracket:
                slimItem = bracket.slimItem
            else:
                ballpark = sm.GetService('michelle').GetBallpark()
                if ballpark is None:
                    self.LogWarn('OnDamageMessage: No ballpark, not showing damage message.')
                    return
                slimItem = ballpark.GetInvItem(objectID)
            if slimItem:
                objectName = uix.GetSlimItemName(slimItem) or 'Some object'
                if slimItem.corpID and not util.IsNPC(slimItem.corpID):
                    typeName = cfg.invtypes.Get(slimItem.typeID).name
                    damageMessagesArgs['typeName'] = typeName
                    tickerText = cfg.corptickernames.Get(slimItem.corpID).tickerName
                    damageMessagesArgs['tickerText'] = tickerText
            if objectName is None or not len(objectName):
                if argName == 'owner':
                    continue
                self.LogError('Failed to display message', damageMessagesArgs)
                return
            damageMessagesArgs[argName] = objectName
            damageMessagesArgs['%s_ID' % argName] = objectID

        self.AddCombatMessage(msgKey, damageMessagesArgs)

    @telemetry.ZONE_METHOD
    def AddCombatMessage(self, msgKey, msgTextArgs):
        smallFontsize = max(10, self.notificationFontSize - 2)
        msgTextArgs.update({'strongColor': '<color=0xff00ffff>',
         'faintColor': '<color=0x77ffffff>',
         'fontMarkUpStart': '<font size=%s>' % smallFontsize,
         'fontMarkUpEnd': '</font>'})
        showTicker = settings.user.ui.Get('damageMessagesShowTicker', False)
        showShip = settings.user.ui.Get('damageMessagesShowShip', False)
        showWeapon = settings.user.ui.Get('damageMessagesShowWeapon', False)
        showQuality = settings.user.ui.Get('damageMessagesShowQuality', True)
        doShowInspaceNotifications = settings.user.ui.Get('damageMessageShowInspaceNotifications', True)
        notificationsExtraNameText = ''
        logExtraNameText = ''
        if msgTextArgs.get('tickerText', ''):
            extra = '[%s]' % msgTextArgs.get('tickerText', '')
            logExtraNameText += extra
            if showTicker:
                notificationsExtraNameText += extra
        if msgTextArgs.get('typeName', ''):
            extra = '(%s)' % msgTextArgs.get('typeName', '')
            logExtraNameText += extra
            if showShip:
                notificationsExtraNameText += extra
        msgTextArgs['extraNameText'] = logExtraNameText
        msgFullText = cfg.GetMessageTypeAndText(msgKey, msgTextArgs)
        if msgFullText.type == 'error' and not settings.user.ui.Get('logerrors', 0):
            return
        if doShowInspaceNotifications:
            if logExtraNameText == notificationsExtraNameText:
                msgLimited = msgFullText
            else:
                msgTextArgs['extraNameText'] = notificationsExtraNameText
                msgLimited = cfg.GetMessageTypeAndText(msgKey, msgTextArgs)
        logPostText = ''
        notificationsPostText = ''
        if 'weapon' in msgTextArgs:
            extra = ' - %s' % cfg.invtypes.Get(msgTextArgs['weapon']).name
            logPostText += extra
            if showWeapon:
                notificationsPostText += extra
        if msgTextArgs.get('hitQualityText', ''):
            extra = ' - %s' % msgTextArgs['hitQualityText']
            logPostText += extra
            if showQuality:
                notificationsPostText += extra
        fullText = msgFullText.text + logPostText
        self.AddText(fullText, 'combat')
        if doShowInspaceNotifications:
            limitedText = msgLimited.text + notificationsPostText
            hitQuality = msgTextArgs.get('hitQuality', None)
            attackerID = msgTextArgs.get('attackerID', None)
            self.Say(limitedText, hitQuality, attackerID)

    @telemetry.ZONE_METHOD
    def AddText(self, msgtext, msgtype = None, msg = None):
        timestamp = blue.os.GetWallclockTime()
        if not self.broken:
            formattedTime = self.GetFormattedTime(timestamp)
            formattedMessage = '[%20s ] (%s) %s\n' % (formattedTime, msgtype, msgtext)
            encodedMessage = formattedMessage.encode('utf8', 'replace')
            self.msglog.append(encodedMessage)
        if not self.ShowMessage(msgtype):
            return
        msgData = (msgtext, msgtype, timestamp)
        self.messages.append(msgData)
        maxlog = settings.user.ui.Get('logmessageamount', 100)
        if len(self.messages) > maxlog * 2:
            self.messages = self.messages[-maxlog:]
        wnd = self.GetWndWithFrameCounter()
        if wnd and not wnd.destroyed:
            self.addmsg.append(msgData)

    @telemetry.ZONE_METHOD
    def GetFormattedTime(self, timestamp, *args):
        year, month, wd, day, hour, min, sec, ms = blue.os.GetTimeParts(timestamp)
        return '%d.%.2d.%.2d %.2d:%.2d:%.2d' % (year,
         month,
         day,
         hour,
         min,
         sec)

    def Say(self, msgtext, hitQuality, attackerID, *args):
        message = getattr(uicore.layer.target, 'message', None)
        if not message or message.destroyed:
            message = uicls.CombatMessage(parent=uicore.layer.target, name='combatMessage', state=uiconst.UI_PICKCHILDREN)
            uicore.layer.target.message = message
        message.AddMessage(msgtext, hitQuality, attackerID)

    def ShowMessage(self, msgtype):
        return settings.user.ui.Get('show%slogmessages' % msgtype, 1)

    @telemetry.ZONE_METHOD
    def DumpToLog(self):
        if self.broken or not self.msglog:
            return
        logfile = None
        try:
            filename = self.GetLogfileName()
            try:
                logfile = file(filename, 'a')
            except:
                if self.newfileAttempts < 3:
                    log.LogWarn('Failed to open the logfile %s, creating new logfile...' % filename)
                    filename = self.GetLogfileName(1)
                    log.LogWarn('new logfile name is: ', filename)
                    logfile = file(filename, 'a')
                    self.newfileAttempts += 1
                else:
                    self.broken = 1
                    log.LogException(toAlertSvc=0)
                sys.exc_clear()

            if logfile:
                try:
                    logfile.writelines(self.msglog)
                    logfile.close()
                except IOError:
                    log.LogException(toAlertSvc=0)
                    sys.exc_clear()

                self.msglog = []
        except:
            log.LogException(toAlertSvc=0)
            sys.exc_clear()

        if logfile and not logfile.closed:
            logfile.close()

    def CopyLog(self):
        self.DumpToLog()
        logfile = None
        try:
            filename = self.GetLogfileName()
            logfile = file(filename)
            ret = logfile.read()
            logfile.close()
            blue.pyos.SetClipboardData(ret)
        except:
            log.LogException()
            sys.exc_clear()

        if logfile and not logfile.closed:
            logfile.close()

    def GetLogfileName(self, reset = 0):
        if reset:
            self.Reset(reset)
        year, month, weekday, day, hour, minute, second, msec = blue.os.GetTimeParts(self.resettime)
        filename = '%d%.2d%.2d_%.2d%.2d%.2d' % (year,
         month,
         day,
         hour,
         minute,
         second)
        filename = blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL) + '/EVE/logs/Gamelogs/%s.txt' % filename
        return filename

    def _PersistWorker(self):
        while self.IsRunning():
            blue.pyos.synchro.SleepWallclock(self.persistInterval)
            self.DumpToLog()

    def MoveNotifications(self, enterMode, *args):
        self.SetDragModeState(state=enterMode)
        message = getattr(uicore.layer.target, 'message', None)
        if not message or message.destroyed:
            message = uicls.CombatMessage(parent=uicore.layer.target, name='combatMessage', state=uiconst.UI_PICKCHILDREN, width=400, height=60)
            uicore.layer.target.message = message
            message.SetSizeAndPosition()
        msg = None
        for each in uicore.layer.abovemain.children[:]:
            if each.name == 'message':
                msg = each
                break

        if msg is None:
            msg = uicls.Message(parent=uicore.layer.abovemain, name='message', height=40, width=300, state=uiconst.UI_HIDDEN)
        if enterMode:
            msg.EnterDragMode()
            message.EnterDragMode()
        else:
            msg.ExitDragMode()
            message.ExitDragMode()

    def IsInDragMode(self, *args):
        return self.inMovingMode

    def SetDragModeState(self, state, *args):
        self.inMovingMode = state


class LoggerWindow(uicls.Window):
    __guid__ = 'form.Logger'
    default_windowID = 'logger'

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.SetCaption(localization.GetByLabel('UI/Accessories/Log/Log'))
        self.SetMinSize([256, 100])
        self.SetWndIcon('ui_34_64_4', hidden=True)
        self.SetTopparentHeight(0)
        self.SetScope('all')
        margin = const.defaultPadding
        scroll = uicls.Scroll(parent=self.sr.main, padding=const.defaultPadding)
        scroll.padTop = 20
        scroll.Load(contentList=[], fixedEntryHeight=18, headers=[localization.GetByLabel('UI/Common/DateWords/Time'), localization.GetByLabel('UI/Accessories/Log/Type'), localization.GetByLabel('UI/Accessories/Log/Message')])
        scroll.sr.id = 'logScroll'
        self.sr.scroll = scroll
        self.settingMenu = uicls.UtilMenu(menuAlign=uiconst.TOPLEFT, parent=self.sr.main, align=uiconst.TOPLEFT, GetUtilMenu=self.GetNotificationsSettingsMenu, left=const.defaultPadding, label=localization.GetByLabel('UI/Accessories/Log/CombatSettings'), texturePath='res:/UI/Texture/Icons/38_16_229.png', closeTexturePath='res:/UI/Texture/Icons/38_16_230.png')
        self.filterMenu = uicls.UtilMenu(menuAlign=uiconst.TOPRIGHT, parent=self.sr.main, align=uiconst.TOPRIGHT, GetUtilMenu=self.GetLogFilterMenu, left=const.defaultPadding, width=20, height=20, iconSize=16, texturePath='res:/UI/Texture/Icons/38_16_205.png')
        self.localizedMessages = {'error': localization.GetByLabel('UI/Accessories/Log/LogError'),
         'warning': localization.GetByLabel('UI/Accessories/Log/LogWarn'),
         'slash': localization.GetByLabel('UI/Accessories/Log/LogSlash'),
         'combat': localization.GetByLabel('UI/Accessories/Log/LogCombat'),
         'notify': localization.GetByLabel('UI/Accessories/Log/LogNotify'),
         'question': localization.GetByLabel('UI/Accessories/Log/LogQuestion'),
         'info': localization.GetByLabel('UI/Accessories/Log/LogInfo'),
         'hint': localization.GetByLabel('UI/Accessories/Log/LogHint')}
        self.LoadAllMessages()
        self.timer = base.AutoTimer(1000, self.CheckMessages)

    def _PrepareListEntries(self, messages):
        showmsgs = []
        dateSortKey = 'sort_%s' % localization.GetByLabel('UI/Common/DateWords/Time')
        openMsgTitle = localization.GetByLabel('UI/Accessories/Log/LogMessage')
        for msg in messages:
            msgtext, msgtype, timestamp = msg
            if not self.ShowMessage(msgtype):
                continue
            color = COLORS_BY_TYPE.get(msgtype, '<color=0xffffffff>')
            if msgtype:
                if msgtype in self.localizedMessages:
                    label = self.localizedMessages[msgtype]
                else:
                    label = msgtype
            else:
                label = localization.GetByLabel('UI/Accessories/Log/Generic')
            text = localization.GetByLabel('UI/Accessories/Log/MessageOutput', logtime=timestamp, color=color, label=label, message=uiutil.StripTags(msgtext, stripOnly=['t']))
            data = {'label': text,
             'canOpen': openMsgTitle,
             dateSortKey: timestamp,
             'line': 1}
            entry = listentry.Get('Generic', data=data)
            showmsgs.append(entry)

        return showmsgs

    @telemetry.ZONE_METHOD
    def LoadAllMessages(self):
        maxlog = settings.user.ui.Get('logmessageamount', 100)
        messages = sm.GetService('logger').GetMessages()
        if len(messages) > maxlog:
            messages = messages[-maxlog:]
        showmsgs = self._PrepareListEntries(messages)
        self.sr.scroll.Load(contentList=showmsgs, headers=[localization.GetByLabel('UI/Common/DateWords/Time'), localization.GetByLabel('UI/Accessories/Log/Type'), localization.GetByLabel('UI/Accessories/Log/Message')])

    @telemetry.ZONE_METHOD
    def CheckMessages(self):
        if uiutil.IsVisible(self.sr.scroll):
            dateSortKey = 'sort_%s' % localization.GetByLabel('UI/Common/DateWords/Time')
            messages = sm.GetService('logger').GetPendingMessages()
            if messages:
                entryList = self._PrepareListEntries(messages)
                maxlog = settings.user.ui.Get('logmessageamount', 100)
                self.sr.scroll.AddEntries(0, entryList)
                revSorting = self.sr.scroll.GetSortDirection() or self.sr.scroll.GetSortBy() is None
                if revSorting:
                    self.sr.scroll.RemoveEntries(self.sr.scroll.GetNodes()[maxlog:])
                else:
                    self.sr.scroll.RemoveEntries(self.sr.scroll.GetNodes()[:-maxlog])

    def GetMenu(self, *args):
        m = uicls.Window.GetMenu(self)
        m += [None, (uiutil.MenuLabel('UI/Accessories/Log/CaptureLog'), sm.GetService('logger').DumpToLog), (uiutil.MenuLabel('UI/Accessories/Log/CopyLog'), sm.GetService('logger').CopyLog)]
        return m

    def GetLogFilterMenu(self, menuParent):
        menuParent.AddHeader(text=localization.GetByLabel('UI/Accessories/Log/MessageTypesToLog'))
        for textPath, config in (('UI/Accessories/Log/ShowInfo', 'showinfologmessages'),
         ('UI/Accessories/Log/ShowWarn', 'showwarninglogmessages'),
         ('UI/Accessories/Log/ShowError', 'showerrorlogmessages'),
         ('UI/Accessories/Log/ShowCombat', 'showcombatlogmessages'),
         ('UI/Accessories/Log/ShowNotify', 'shownotifylogmessages'),
         ('UI/Accessories/Log/ShowQuestion', 'showquestionlogmessages')):
            text = localization.GetByLabel(textPath)
            checked = settings.user.ui.Get(config, 1)
            menuParent.AddCheckBox(text=text, checked=checked, callback=(self.SetLogSetting, config, not checked))

        menuParent.AddDivider()
        menuParent.AddHeader(text=localization.GetByLabel('UI/Accessories/Log/NumMessagesInLogView'))
        oldValue = settings.user.ui.Get('logmessageamount', 100)
        checked = oldValue == 100
        menuParent.AddRadioButton(text=100, checked=checked, callback=(self.SetNumMessageSettings, oldValue))
        checked = oldValue == 1000
        menuParent.AddRadioButton(text=1000, checked=checked, callback=(self.SetNumMessageSettings, oldValue))

    def SetLogSetting(self, config, newConfigValue):
        settings.user.ui.Set(config, newConfigValue)
        self.LoadAllMessages()

    def ChangeInspaceNotificationsValue(self, newConfigValue):
        settings.user.ui.Set('damageMessageShowInspaceNotifications', newConfigValue)
        messageBox = getattr(uicore.layer.target, 'message', None)
        if messageBox and not messageBox.destroyed:
            messageBox.Close()

    def ChangeFontSize(self, value, *args):
        settings.user.ui.Set('dmgnotifictions_fontsize', value)
        sm.GetService('logger').notificationFontSize = value
        message = getattr(uicore.layer.target, 'message', None)
        if message:
            message.ChangeFontSize()

    def ChangeAlignment(self, value, *args):
        settings.user.ui.Set('dmgnotifictions_alignment', value)
        message = getattr(uicore.layer.target, 'message', None)
        if message:
            message.ChangeAlignment()

    def ResetDmgNotificationAlignment(self, *args):
        settings.char.ui.Delete('damageMessages_config')
        settings.user.ui.Set('dmgnotifictions_alignment', 'auto')
        message = getattr(uicore.layer.target, 'message', None)
        if message:
            message.ResetAlignment()

    def SetNumMessageSettings(self, oldValue):
        if oldValue == 100:
            settings.user.ui.Set('logmessageamount', 1000)
        else:
            settings.user.ui.Set('logmessageamount', 100)

    def GetNotificationsSettingsMenu(self, menuParent):
        menuParent.AddHeader(text=localization.GetByLabel('UI/Accessories/Log/CombatMessagesToDisplay'))
        dmgShowing = settings.user.ui.Get('damageMessages', True)
        for textPath, config, isEnabled, hintPath in (('UI/SystemMenu/GeneralSettings/Inflight/ShowTacticalNotifications',
          'notifyMessagesEnabled',
          True,
          'UI/SystemMenu/GeneralSettings/Inflight/ShowTacticalNotificationTooltip'),
         ('UI/SystemMenu/GeneralSettings/Inflight/DamageNotifications',
          'damageMessages',
          True,
          None),
         ('UI/SystemMenu/GeneralSettings/Inflight/MissedHitNotifications',
          'damageMessagesNoDamage',
          dmgShowing,
          None),
         ('UI/SystemMenu/GeneralSettings/Inflight/ShowInflictedDamageNotifications',
          'damageMessagesMine',
          dmgShowing,
          None),
         ('UI/SystemMenu/GeneralSettings/Inflight/ShowIncurredDamageNotification',
          'damageMessagesEnemy',
          dmgShowing,
          None)):
            text = localization.GetByLabel(textPath)
            if hintPath:
                hintText = localization.GetByLabel(hintPath)
            else:
                hintText = ''
            checked = settings.user.ui.Get(config, 1)
            if not isEnabled:
                callback = None
            else:
                callback = (self.SetLogSetting, config, not checked)
            menuParent.AddCheckBox(text=text, checked=checked, callback=callback, hint=hintText)

        menuParent.AddDivider()
        menuParent.AddHeader(text=localization.GetByLabel('UI/Accessories/Log/ExtraInfoHeader'))
        text = localization.GetByLabel('UI/Accessories/Log/ShowInspaceNotifications')
        showInSpaceNotifications = settings.user.ui.Get('damageMessageShowInspaceNotifications', True)
        if settings.user.ui.Get('damageMessages', True):
            callback = (self.ChangeInspaceNotificationsValue, not showInSpaceNotifications)
        else:
            callback = None
        menuParent.AddCheckBox(text=text, checked=showInSpaceNotifications, callback=callback)
        for textPath, config, defaultSetting in (('UI/Accessories/Log/DmgNotificationsShowShip', 'damageMessagesShowShip', False),
         ('UI/Accessories/Log/DmgNotificationsShowTicker', 'damageMessagesShowTicker', False),
         ('UI/Accessories/Log/DmgNotificationsShowWeapon', 'damageMessagesShowWeapon', False),
         ('UI/Accessories/Log/DmgNotificationsShowQuality', 'damageMessagesShowQuality', True)):
            text = localization.GetByLabel(textPath)
            checked = settings.user.ui.Get(config, defaultSetting)
            if not showInSpaceNotifications:
                callback = None
            else:
                callback = (self.SetLogSetting, config, not checked)
            menuParent.AddCheckBox(text=text, checked=checked, callback=callback)

        menuParent.AddDivider()
        menuParent.AddHeader(text=localization.GetByLabel('UI/Accessories/Log/FontSize'))
        currentFontSize = settings.user.ui.Get('dmgnotifictions_fontsize', 12)
        for value in [10, 12, 14]:
            checked = value == currentFontSize
            menuParent.AddRadioButton(text=value, checked=checked, callback=(self.ChangeFontSize, value))

        menuParent.AddDivider()
        menuParent.AddHeader(text=localization.GetByLabel('UI/Accessories/Log/InspaceNotificationFontAlignment'))
        currentAlignMent = settings.user.ui.Get('dmgnotifictions_alignment', 'auto')
        for textPath, config in (('UI/Accessories/Log/AlignmentAuto', 'auto'),
         ('UI/Accessories/Log/AlignmentLeft', 'left'),
         ('UI/Accessories/Log/AlignmentRight', 'right'),
         ('UI/Accessories/Log/AlignmentCenter', 'center')):
            text = localization.GetByLabel(textPath)
            checked = config == currentAlignMent
            menuParent.AddRadioButton(text=text, checked=checked, callback=(self.ChangeAlignment, config))

        text = localization.GetByLabel('UI/Accessories/Log/ResetAlignment')
        menuParent.AddIconEntry(icon='res:/UI/Texture/classes/UtilMenu/BulletIcon.png', text=text, callback=self.ResetDmgNotificationAlignment)
        menuParent.AddDivider()
        if sm.GetService('logger').IsInDragMode():
            text = localization.GetByLabel('UI/Accessories/Log/ExitMessageMovingMode')
            enterArgs = False
        else:
            text = localization.GetByLabel('UI/Accessories/Log/EnterMessageMovingMode')
            enterArgs = True
        menuParent.AddIconEntry(icon='res:/UI/Texture/classes/UtilMenu/BulletIcon.png', text=text, callback=(sm.GetService('logger').MoveNotifications, enterArgs))

    def OnEndMaximize(self, *args):
        self.LoadAllMessages()

    def _OnClose(self, *args):
        self.timer = None

    def ShowMessage(self, msgtype):
        return settings.user.ui.Get('show%slogmessages' % msgtype, 1)