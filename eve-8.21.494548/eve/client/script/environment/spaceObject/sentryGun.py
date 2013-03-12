#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/sentryGun.py
import spaceObject
import turretSet
import timecurves
import random
entityExplosionsS = ['res:/Emitter/tracerexplosion/NPCDeathS1.blue', 'res:/Emitter/tracerexplosion/NPCDeathS3.blue', 'res:/Emitter/tracerexplosion/NPCDeathS4.blue']
entityExplosionsM = ['res:/Emitter/tracerexplosion/NPCDeathM1.blue', 'res:/Emitter/tracerexplosion/NPCDeathM3.blue', 'res:/Emitter/tracerexplosion/NPCDeathM4.blue']
entityExplosionsL = ['res:/Emitter/tracerexplosion/NPCDeathL1.blue', 'res:/Emitter/tracerexplosion/NPCDeathL3.blue', 'res:/Emitter/tracerexplosion/NPCDeathL4.blue']
TURRET_TYPE_ID = {spaceObject.gfxRaceAmarr: 462,
 spaceObject.gfxRaceGallente: 569,
 spaceObject.gfxRaceCaldari: 574,
 spaceObject.gfxRaceMinmatar: 498,
 spaceObject.gfxRaceAngel: 462,
 spaceObject.gfxRaceSleeper: 4049,
 spaceObject.gfxRaceJove: 4049}
TURRET_FALLBACK_TYPE_ID = 462

class SentryGun(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.SentryGun'

    def __init__(self):
        spaceObject.SpaceObject.__init__(self)
        self.targets = []
        self.modules = {}
        self.fitted = False
        self.typeID = None
        self.turretTypeID = TURRET_FALLBACK_TYPE_ID

    def Assemble(self):
        timecurves.ScaleTime(self.model, 0.9 + random.random() * 0.2)
        self.SetStaticRotation()
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        self.typeID = slimItem.typeID
        to = cfg.invtypes.Get(self.typeID)
        g = cfg.graphics.GetIfExists(to.graphicID)
        raceID = getattr(g, 'gfxRaceID', None)
        if raceID is not None:
            self.turretTypeID = TURRET_TYPE_ID.get(raceID, TURRET_FALLBACK_TYPE_ID)
        if settings.user.ui.Get('turretsEnabled', 1):
            self.FitHardpoints()

    def FitHardpoints(self, blocking = False):
        if self.fitted:
            return
        if self.model is None:
            self.LogWarn('FitHardpoints - No model')
            return
        if self.typeID is None:
            self.LogWarn('FitHardpoints - No typeID')
            return
        self.fitted = True
        self.modules = {}
        ts = turretSet.TurretSet.FitTurret(self.model, self.typeID, self.turretTypeID, 1)
        if ts is not None:
            self.modules[self.id] = ts

    def LookAtMe(self):
        if not self.model:
            return
        if not self.fitted:
            self.FitHardpoints()

    def Release(self):
        if self.released:
            return
        self.modules = None
        spaceObject.SpaceObject.Release(self)

    def Explode(self):
        explosionURL, (delay, scaling) = self.GetExplosionInfo()
        return spaceObject.SpaceObject.Explode(self, explosionURL=explosionURL, managed=True, delay=delay, scaling=scaling)


exports = {'spaceObject.SentryGun': SentryGun}