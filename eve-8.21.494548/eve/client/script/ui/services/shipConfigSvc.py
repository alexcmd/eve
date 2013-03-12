#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/shipConfigSvc.py
import util
import locks
import service
import moniker

class ShipConfigSvc(service.Service):
    __guid__ = 'svc.shipConfig'
    __update_on_reload__ = 1
    __dependencies__ = []
    __notifyevents__ = ['OnSessionChanged']
    __startupdependencies__ = []

    def Run(self, memstream_which_absolutely_noone_uses_anymore_but_no_one_gets_around_to_remove = None):
        self._ship = None
        self.shipid = util.GetActiveShip()
        self.config = None

    def _ClearCachedAttributes(self):
        self.shipid = util.GetActiveShip()
        self.config = None
        self._ship = None

    def OnSessionChanged(self, isRemote, session, change):
        if 'locationid' in change or 'shipid' in change:
            self._ClearCachedAttributes()

    @property
    def ship(self):
        if self._ship is None:
            self._ship = moniker.GetShipAccess()
        return self._ship

    def GetShipConfig(self, shipID = None):
        if shipID is not None:
            return moniker.GetShipAccess().GetShipConfiguration(shipID)
        if util.GetActiveShip() != self.shipid:
            self._ClearCachedAttributes()
        with locks.TempLock('%s:%s' % (self, self.shipid)):
            if self.config is None:
                self.config = self.ship.GetShipConfiguration(self.shipid)
        return self.config

    def SetShipConfig(self, key, value):
        lock = locks.TempLock('%s:%s' % (self, self.shipid))
        if lock.lockedWhen is not None:
            return
        with lock:
            self.ship.ConfigureShip(self.shipid, {key: value})
            self.config[key] = value

    def ToggleFleetHangarFleetAccess(self):
        self.SetShipConfig('FleetHangar_AllowFleetAccess', not self.IsFleetHangarFleetAccessAllowed())

    def ToggleFleetHangarCorpAccess(self):
        self.SetShipConfig('FleetHangar_AllowCorpAccess', not self.IsFleetHangarCorpAccessAllowed())

    def ToggleShipMaintenanceBayFleetAccess(self):
        self.SetShipConfig('SMB_AllowFleetAccess', not self.IsShipMaintenanceBayFleetAccessAllowed())

    def ToggleShipMaintenanceBayCorpAccess(self):
        self.SetShipConfig('SMB_AllowCorpAccess', not self.IsShipMaintenanceBayCorpAccessAllowed())

    def IsFleetHangarFleetAccessAllowed(self):
        return self.GetShipConfig()['FleetHangar_AllowFleetAccess']

    def IsFleetHangarCorpAccessAllowed(self):
        return self.GetShipConfig()['FleetHangar_AllowCorpAccess']

    def IsShipMaintenanceBayFleetAccessAllowed(self):
        return self.GetShipConfig()['SMB_AllowFleetAccess']

    def IsShipMaintenanceBayCorpAccessAllowed(self):
        return self.GetShipConfig()['SMB_AllowCorpAccess']