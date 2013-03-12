#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/sys/eve.py
import blue
import base
import uthread
import types
import traceback
import log
import stackless
import util
import sys
import uiconst
import triui
import localization

class Eve():

    def __init__(self):
        self.__stationItem = None
        self.session = None
        self.taketime = 1
        self.noErrorPopups = 0
        self.maxzoom = 30.0
        self.minzoom = 1000000.0
        self.fontFactor = 1.0
        self.themeColor = (0 / 256.0,
         0 / 256.0,
         0 / 256.0,
         0.95)
        self.themeBgColor = (128 / 256.0,
         128 / 256.0,
         128 / 256.0,
         128 / 256.0)
        self.themeCompColor = (2 / 256.0,
         4 / 256.0,
         8 / 256.0,
         110 / 256.0)
        self.themeCompSubColor = (2 / 256.0,
         4 / 256.0,
         8 / 256.0,
         115 / 256.0)
        self.hiddenUIState = None
        self.chooseWndMenu = None
        self.rookieState = None
        blue.pyos.exceptionHandler = self.ExceptionHandler
        import __builtin__
        if hasattr(__builtin__, 'eve'):
            __builtin__.eve.Release()
        __builtin__.eve = self

    def SetRookieState(self, state):
        if state != self.rookieState:
            self.rookieState = state
            sm.ChainEvent('ProcessRookieStateChange', state)
            settings.user.ui.Set('RookieState', state)

    def ClearStationItem(self):
        self.__stationItem = None

    def SetStationItemBits(self, bits):
        self.__stationItem = util.Row(['hangarGraphicID',
         'ownerID',
         'itemID',
         'serviceMask',
         'stationTypeID'], bits)

    def HasInvalidStationItem(self):
        return self.__stationItem is None or self.__stationItem.itemID != self.session.stationid

    def __getattr__(self, key):
        if key == 'stationItem':
            if self.session.stationid2 and self.HasInvalidStationItem():
                self.SetStationItemBits(sm.RemoteSvc('stationSvc').GetStationItemBits())
            return self.__stationItem
        if key in self.__dict__:
            return self.__dict__[key]
        raise AttributeError(key)

    def Release(self):
        sm.UnregisterNotify(self)
        if self.session is not None:
            base.CloseSession(self.session)
        blue.pyos.exceptionHandler = None

    def Message(self, *args, **kw):
        if args and args[0] == 'IgnoreToTop':
            return
        if not getattr(uicore, 'desktop', None):
            return
        curr = stackless.getcurrent()
        if curr.is_main:
            uthread.new(self._Message, *args, **kw).context = 'eve.Message'
        else:
            return self._Message(*args, **kw)

    def _Message(self, msgkey, params = None, buttons = None, suppress = None, default = None, modal = True):
        if type(msgkey) not in types.StringTypes:
            raise RuntimeError('Invalid argument, msgkey must be a string', msgkey)
        msg = cfg.GetMessage(msgkey, params, onNotFound='raise')
        if msg.text and settings.public.generic.Get('showMessageId', 0):
            rawMsg = cfg.GetMessage(msgkey, None, onDictMissing=None)
            if rawMsg.text:
                newMsgText = '{message}<br>------------------<br>[Message ID: <b>{messageKey}</b>]<br>{rawMessage}'
                rawMsg.text = rawMsg.text.replace('<', '&lt;').replace('>', '&gt;')
                msg.text = newMsgText.format(message=msg.text, messageKey=msgkey, rawMessage=rawMsg.text)
        if uicore.desktop is None:
            try:
                log.general.Log("Some dude is trying to send a message with eve.Message before  it's ready.  %s,%s,%s,%s" % (strx(msgkey),
                 strx(params),
                 strx(buttons),
                 strx(suppress)), log.LGERR)
                flag = 0
                flag |= 48
                flag |= 8192
                blue.win32.MessageBox(msg.text, msg.title, flag)
            except:
                sys.exc_clear()

            return
        if buttons is not None and msg.type not in ('warning', 'question', 'fatal'):
            raise RuntimeError('Cannot override buttons except in warning, question and fatal messages', msg, buttons, msg.type)
        supp = settings.user.suppress.Get('suppress.' + msgkey, None)
        if supp is not None:
            if suppress is not None:
                return suppress
            else:
                return supp
        if not msg.suppress and suppress is not None:
            txt = 'eve.Message() called with the suppress parameter without a suppression specified in the message itself - %s / %s'
            log.general.Log(txt % (msgkey, params), log.LGWARN)
        elif suppress in (uiconst.ID_CLOSE, uiconst.ID_CANCEL):
            txt = 'eve.Message() called with the suppress parameter of ID_CLOSE or ID_CANCEL which is not supported suppression - %s / %s'
            log.general.Log(txt % (msgkey, params), log.LGWARN)
        sm.GetService('audio').AudioMessage(msg)
        sm.ScatterEvent('OnEveMessage', msgkey)
        if uicore.uilib:
            gameui = sm.GetService('gameui')
        else:
            gameui = None
        if msg.type in ('hint', 'notify', 'warning', 'question', 'infomodal', 'info'):
            sm.GetService('logger').AddMessage(msg)
        if msg.type in ('info', 'infomodal', 'warning', 'question', 'error', 'fatal', 'windowhelp'):
            supptext = None
            if msg.suppress:
                if buttons in [None, triui.OK]:
                    supptext = localization.GetByLabel('/Carbon/UI/Common/DoNotShowAgain')
                else:
                    supptext = localization.GetByLabel('/Carbon/UI/Common/DoNotAskAgain')
            if gameui:
                if buttons is None:
                    buttons = uiconst.OK
                if msg.icon == '':
                    msg.icon = None
                icon = msg.icon
                if icon is None:
                    icon = {'info': triui.INFO,
                     'infomodal': triui.INFO,
                     'warning': triui.WARNING,
                     'question': triui.QUESTION,
                     'error': triui.ERROR,
                     'fatal': triui.FATAL}.get(msg.type, triui.ERROR)
                customicon = None
                if params:
                    customicon = params.get('customicon', None)
                msgtitle = msg.title
                if msg.title is None:
                    msgTitles = {'info': localization.GetByLabel('UI/Common/Information'),
                     'infomodal': localization.GetByLabel('UI/Common/Information'),
                     'warning': localization.GetByLabel('UI/Generic/Warning'),
                     'question': localization.GetByLabel('UI/Common/Question'),
                     'error': localization.GetByLabel('UI/Common/Error'),
                     'fatal': localization.GetByLabel('UI/Common/Fatal')}
                    msgtitle = msgTitles.get(msg.type, localization.GetByLabel('UI/Common/Information'))
                ret, supp = gameui.MessageBox(msg.text, msgtitle, buttons, icon, supptext, customicon, default=default, modal=modal)
                if supp and ret not in (uiconst.ID_CLOSE, uiconst.ID_CANCEL):
                    if not suppress or ret == suppress:
                        settings.user.suppress.Set('suppress.' + msgkey, ret)
                        sm.GetService('settings').SaveSettings()
                return ret
        elif msg.type in ('notify', 'hint', 'event'):
            if gameui:
                return gameui.Say(msg.text)
        elif msg.type in ('audio',):
            pass
        elif msg.type == '':
            if msgkey in ('BrowseHtml', 'BrowseIGB'):
                sm.GetService('ui').Browse(msgkey, params)
            elif msgkey == 'OwnerPopup':
                sm.StartService('gameui').MessageBox(params.get('body', ''), params.get('title', ''), triui.OK, triui.INFO)
            else:
                return msg
        else:
            raise RuntimeError('Unknown message type', msg)

    def IsDestroyedWindow(self, tb):
        try:
            argnames = tb.tb_frame.f_code.co_varnames[:tb.tb_frame.f_code.co_argcount + 1]
            locals_ = tb.tb_frame.f_locals.copy()
            if argnames:
                for each in argnames:
                    try:
                        theStr = repr(locals_[each])
                        if theStr and theStr.find('destroyed=1') != -1:
                            return theStr
                    except:
                        sys.exc_clear()

            return ''
        except AttributeError:
            sys.exc_clear()
            return ''

    def ExceptionHandler(self, exctype, exc, tb, message = ''):
        try:
            if isinstance(exc, UserError):
                self.Message(exc.msg, exc.dict)
            else:
                toMsgWindow = prefs.GetValue('showExceptions', 0)
                if isinstance(exc, RuntimeError) and len(exc.args) and exc.args[0] == 'ErrMessageNotFound':
                    if toMsgWindow:
                        self.Message('ErrMessageNotFound', exc.args[1])
                else:
                    toMsgWindow = toMsgWindow and not self.noErrorPopups
                    if isinstance(exc, AttributeError):
                        deadWindowCheck = self.IsDestroyedWindow(tb)
                        if deadWindowCheck:
                            name = ''
                            try:
                                nameIdx = deadWindowCheck.find('name=')
                                if nameIdx != -1:
                                    nameIdx += 6
                                    endNameIdx = deadWindowCheck[nameIdx:].find('",')
                                    if endNameIdx != -1:
                                        name = deadWindowCheck[nameIdx:nameIdx + endNameIdx]
                            except:
                                sys.exc_clear()

                            log.LogWarn('Message sent to dead window:', name)
                            exctype = exc = tb = None
                            return
                    if getattr(exc, 'msg', None) == 'DisconnectedFromServer':
                        toMsgWindow = 0
                    severity = log.LGERR
                    extraText = '; caught by eve.ExceptionHandler'
                    if message:
                        extraText += '\nContext info: ' + message
                    return log.LogException(extraText=extraText, toMsgWindow=toMsgWindow, exctype=exctype, exc=exc, tb=tb, severity=severity)
        except:
            exctype = exc = tb = None
            traceback.print_exc()
            sys.exc_clear()


e = Eve()
exports = {'eve.eve': e}