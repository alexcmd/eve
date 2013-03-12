#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/wrecksvc.py
import blue
import dbg
import log
import service
import state
import sys

class WreckService(service.Service):
    __guid__ = 'svc.wreck'
    __dependencies__ = [('state', 'statesvc'), 'gameui']
    __startupdependencies__ = ['settings']

    def Run(self, *args):
        service.Service.Run(self, *args)
        expire_hours, expire_mins = (2, 5)
        expire_ms = 1000 * (3600 * expire_hours + 60 * expire_mins)
        self.viewedWrecks = {}
        for itemID, time in settings.char.ui.Get('viewedWrecks', {}).iteritems():
            try:
                if blue.os.TimeDiffInMs(time, blue.os.GetWallclockTime()) < expire_ms:
                    self.viewedWrecks[itemID] = time
            except blue.error:
                sys.exc_clear()

        try:
            self._PersistSettings()
        except:
            log.LogException()
            sys.exc_clear()

    def MarkViewed(self, itemID, isViewed, playSound = False):
        if self.IsMarkedViewed(itemID) == isViewed:
            return
        self._SetViewed(itemID, isViewed)
        self._MarkVisually(itemID, isViewed)
        self._PersistSettings()
        if isViewed and playSound:
            sm.GetService('audio').SendUIEvent('ui_sfx_open_wreck_play')

    def IsMarkedViewed(self, itemID):
        return sm.GetService('state').GetStates(itemID, (state.flagWreckAlreadyOpened,))[0]

    def IsViewedWreck(self, itemID):
        return itemID in self.viewedWrecks

    def _MarkVisually(self, itemID, isViewed):
        sm.GetService('state').SetState(itemID, state.flagWreckAlreadyOpened, isViewed)

    def _SetViewed(self, itemID, isViewed):
        if isViewed and itemID not in self.viewedWrecks:
            self.viewedWrecks[itemID] = blue.os.GetWallclockTime()
        elif not isViewed and itemID in self.viewedWrecks:
            del self.viewedWrecks[itemID]

    def _PersistSettings(self):
        settings.char.ui.Set('viewedWrecks', self.viewedWrecks)