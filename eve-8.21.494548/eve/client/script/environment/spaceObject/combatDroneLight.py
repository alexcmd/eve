#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/combatDroneLight.py
import spaceObject
import turretSet
TURRET_GFXID_FIGHTERBOMBER = {spaceObject.gfxRaceAmarr: 11515,
 spaceObject.gfxRaceGallente: 11517,
 spaceObject.gfxRaceCaldari: 11516,
 spaceObject.gfxRaceMinmatar: 11518}
TURRET_GFXID_COMBATDRONE = {spaceObject.gfxRaceAmarr: 11504,
 spaceObject.gfxRaceGallente: 11506,
 spaceObject.gfxRaceCaldari: 11505,
 spaceObject.gfxRaceMinmatar: 11508}
TURRET_GFXID_GENERIC = 11507

class CombatDroneLight(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.CombatDroneLight'

    def __init__(self):
        spaceObject.SpaceObject.__init__(self)
        self.modules = {}
        self.targets = []
        self.fitted = False
        self.boosters = None
        self.model = None
        self.npcDrone = True

    def LoadModel(self, fileName = None, loadedModel = None):
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        self.typeID = slimItem.typeID
        if settings.user.ui.Get('droneModelsEnabled', 1) or not self.npcDrone:
            fileName = cfg.invtypes.Get(slimItem.typeID).GraphicFile()
        else:
            fileName = 'res:/dx9/model/drone/DroneModelsDisabled.red'
        spaceObject.SpaceObject.LoadModel(self, fileName)

    def Assemble(self):
        if not (settings.user.ui.Get('droneModelsEnabled', 1) or not self.npcDrone):
            return
        if not self.raceID:
            self.raceID = spaceObject.gfxRaceGeneric
        self.FitBoosters(alwaysOn=True, enableTrails=False)
        self.SetupAmbientAudio()
        if hasattr(self.model, 'ChainAnimationEx'):
            self.model.ChainAnimationEx('NormalLoop', 0, 0, 1.0)

    def FitHardpoints(self, blocking = False):
        if self.fitted:
            return
        if self.model is None:
            self.LogWarn('FitHardpoints - No model')
            return
        self.fitted = True
        if not settings.user.ui.Get('turretsEnabled', 1):
            return
        to = cfg.invtypes.Get(self.typeID)
        groupID = to.groupID
        g = cfg.graphics.GetIfExists(to.graphicID)
        raceID = getattr(g, 'gfxRaceID', None)
        turretGraphicID = TURRET_GFXID_GENERIC
        if raceID is not None:
            if groupID == const.groupFighterBomber:
                turretGraphicID = TURRET_GFXID_FIGHTERBOMBER.get(raceID, TURRET_GFXID_GENERIC)
            else:
                turretGraphicID = TURRET_GFXID_COMBATDRONE.get(raceID, TURRET_GFXID_GENERIC)
        if turretGraphicID is not None:
            ts = turretSet.TurretSet.AddTurretToModel(self.model, turretGraphicID, 1)
            if ts is not None and self.modules is not None:
                self.modules[self.id] = ts

    def Release(self):
        if self.released:
            return
        self.modules = None
        spaceObject.SpaceObject.Release(self)

    def Explode(self):
        if not (settings.user.ui.Get('droneModelsEnabled', 1) or not self.npcDrone) or not settings.user.ui.Get('explosionEffectsEnabled', 1):
            return False
        explosionURL, (delay, scaling) = self.GetExplosionInfo()
        return spaceObject.SpaceObject.Explode(self, explosionURL=explosionURL, managed=True, delay=delay, scaling=scaling)


exports = {'spaceObject.CombatDroneLight': CombatDroneLight}