#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/ship.py
import trinity
import spaceObject
import turretSet
import state
import uthread
import log
import math

class Ship(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.Ship'
    __notifyevents__ = ['OnModularShipReady']

    def __init__(self):
        spaceObject.SpaceObject.__init__(self)
        self.activeTargetID = None
        self.gainCurve = trinity.TriScalarCurve()
        self.gainCurve.value = 0.0
        self.audioEntities = []
        self.shipSpeedParameter = None
        self.fitted = False
        self.fittingThread = None
        self.turrets = []
        self.modules = {}
        self.cloakedCopy = None
        self.cloakedShaderStorage = None
        self.burning = False
        self.isTech3 = False
        self.loadingModel = False

    def Prepare(self, spaceMgr):
        self.spaceMgr = spaceMgr
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        if slimItem is None:
            return
        techLevel = sm.StartService('godma').GetTypeAttribute(slimItem.typeID, const.attributeTechLevel)
        if techLevel == 3.0:
            self.isTech3 = True
            subsystems = {}
            for module in slimItem.modules:
                group = cfg.invtypes.Get(module[1]).Group()
                if group.categoryID == const.categorySubSystem:
                    subsystems[group.groupID] = module[1]

            t3ShipSvc = sm.StartService('t3ShipSvc')
            sm.RegisterNotify(self)
            uthread.new(t3ShipSvc.GetTech3ShipFromDict, slimItem.typeID, subsystems, self.id)
            self.loadingModel = True
        else:
            spaceObject.SpaceObject.Prepare(self, spaceMgr)

    def OnModularShipReady(self, id, modelPath):
        if self.id == id:
            model = trinity.Load(modelPath)
            spaceObject.SpaceObject.LoadModel(self, None, loadedModel=model)
            self.Assemble()
            self.Display(1)
            sm.UnregisterNotify(self)
            self.loadingModel = False

    def LoadModel(self, fileName = None, loadedModel = None):
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        if slimItem is None:
            return
        fileName = cfg.invtypes.Get(slimItem.typeID).GraphicFile()
        spaceObject.SpaceObject.LoadModel(self, fileName)
        self.Display(1)

    def Assemble(self):
        bp = sm.StartService('michelle').GetBallpark()
        if bp is None:
            self.LogInfo('Assemble - could not get ballpark, so no destiny sim running. This should never happen!')
            return
        slimItem = bp.GetInvItem(self.id)
        if not slimItem:
            self.LogInfo('Assemble - could not find the item so not assembling')
            return
        if self.model is None:
            return
        self.typeID = slimItem.typeID
        self.UnSync()
        if self.model.__bluetype__ == 'trinity.EveShip2':
            if len(self.model.damageLocators) == 0:
                self.LogError('Type', self.typeID, 'has no damage locators')
        if self.id == eve.session.shipid:
            self.FitHardpoints()
        self.model.ChainAnimationEx('NormalLoop', 0, 0, 1.0)
        self.FitBoosters()

    def Release(self):
        if self.released:
            return
        if self.model is None:
            return
        self.modules = {}
        self.KillCloakedCopy()
        self.audioEntities = []
        self.generalAudioEntity = None
        spaceObject.SpaceObject.Release(self, 'Ship')
        self.cloakShaderStorage = None

    def KillCloakedCopy(self):
        if getattr(self, 'cloakedCopy', None) is not None:
            cloakedCopy = self.cloakedCopy
            scene = sm.StartService('sceneManager').GetRegisteredScene('default')
            scene.objects.fremove(cloakedCopy)
            if hasattr(cloakedCopy, 'translationCurve'):
                cloakedCopy.translationCurve = None
            if hasattr(cloakedCopy, 'rotationCurve'):
                cloakedCopy.rotationCurve = None
            self.cloakedCopy = None
            self.LogInfo('Removed cloaked copy of ship')

    def LookAtMe(self):
        if not self.model:
            return
        if not self.fitted:
            self.FitHardpoints()
        audsvc = sm.GetServiceIfRunning('audio')
        if audsvc.active:
            if audsvc.lastLookedAt == None:
                self.SetupAmbientAudio()
                audsvc.lastLookedAt = self
            elif audsvc.lastLookedAt is not self:
                audsvc.TurnOffShipSound(audsvc.lastLookedAt)
                self.SetupAmbientAudio()
                audsvc.lastLookedAt = self
            else:
                return

    def CheckHardpointsForXLGuns(self):
        if self.fitted:
            return
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        if slimItem is None:
            self.LogError('no invitem property for ship')
            return
        for moduleID, typeID in slimItem.modules:
            graphicFile = cfg.invtypes.Get(typeID).GraphicFile()
            if graphicFile[1] == 'h':
                return True

        return False

    def ModuleListFromMichelleSlimItem(self, slimItem):
        list = []
        for moduleID, typeID in slimItem.modules:
            list.append((moduleID, typeID))

        list.sort()
        return list

    def PrepareFiringSequence(self, effectWrapper, slaveTurrets, targetID):
        if effectWrapper.itemID in self.modules:
            turretModule = self.modules[effectWrapper.itemID]
            turretModule.TakeAim(targetID)
            for slaveTurret in slaveTurrets:
                turretModule = self.modules[slaveTurret]
                turretModule.TakeAim(targetID)

        else:
            log.LogInfo('PrepareFiringSequence - item not found')

    def EnterWarp(self):
        for t in self.turrets:
            t.EnterWarp()

    def ExitWarp(self):
        for t in self.turrets:
            t.ExitWarp()

    def UnfitHardpoints(self):
        if not self.fitted:
            return
        newModules = {}
        for key, val in self.modules.iteritems():
            if val not in self.turrets:
                newModules[key] = val

        self.modules = newModules
        del self.turrets[:]
        self.fitted = False

    def FitHardpoints(self, blocking = False):
        if getattr(self.fittingThread, 'alive', False):
            self.fitted = False
            self.fittingThread.kill()
        if blocking:
            self._FitHardpoints()
        else:
            self.fittingThread = uthread.new(self._FitHardpoints)

    def _FitHardpoints(self):
        if self.fitted:
            return
        if self.model is None:
            self.LogWarn('FitHardpoints - No model')
            return
        self.fitted = True
        newTurretSetDict = turretSet.TurretSet.FitTurrets(self.id, self.model)
        self.turrets = []
        for key, val in newTurretSetDict.iteritems():
            self.modules[key] = val
            self.turrets.append(val)

    def KillBooster(self):
        if self.shipSpeedParameter is not None:
            self.shipSpeedParameter.value = 0.0

    def OnDamageState(self, damageState):
        if self.model is None:
            return
        self.SetDamageStateSingle(damageState[2])

    def SetDamageStateSingle(self, health):
        damage = 1.0 - health
        effectPosition = trinity.TriVector()
        if damage < 0.2:
            for each in list(self.model.children):
                if each.name == 'autoDamage':
                    self.model.children.remove(each)

            self.burning = False
        elif self.id == sm.StartService('state').GetExclState(state.lookingAt) and not self.burning:
            self.burning = True
            if len(self.model.damageLocators):
                furthestBack = self.model.damageLocators[0][0]
                for locator in self.model.damageLocators:
                    locatorTranslation = locator[0]
                    if locatorTranslation[2] > furthestBack[2]:
                        furthestBack = locatorTranslation

                effectPosition = furthestBack
            scale = math.sqrt(self.model.boundingSphereRadius / 30.0)
            effect = trinity.Load('res:/Emitter/Damage/fuel_low.red')
            effect.name = 'autoDamage'
            effect.translation = effectPosition
            effect.scaling = (1, 1, 1)
            prefix = 'owner.positionDelta'
            for curveSet in effect.curveSets:
                for binding in curveSet.bindings:
                    if binding.name[0:len(prefix)] == prefix:
                        binding.sourceObject = self.model.positionDelta

            generators = effect.Find('trinity.Tr2RandomUniformAttributeGenerator')
            for generator in generators:
                if generator.elementType == trinity.PARTICLE_ELEMENT_TYPE.LIFETIME:
                    generator.minRange = (generator.minRange[0],
                     generator.minRange[1] * scale,
                     0,
                     0)
                    generator.maxRange = (generator.maxRange[0],
                     generator.maxRange[1] * scale,
                     0,
                     0)
                elif generator.elementType == trinity.PARTICLE_ELEMENT_TYPE.CUSTOM and generator.customName == 'sizeDynamic':
                    generator.minRange = (generator.minRange[0] * scale,
                     generator.minRange[1] * scale,
                     0,
                     0)
                    generator.maxRange = (generator.maxRange[0] * scale,
                     generator.maxRange[1] * scale,
                     0,
                     0)

            generators = effect.Find('trinity.Tr2SphereShapeAttributeGenerator')
            for generator in generators:
                generator.minRadius = generator.minRadius * scale
                generator.maxRadius = generator.maxRadius * scale

            self.model.children.append(effect)
            effect = None

    def Explode(self):
        explosionPath, (delay, scaling) = self.GetExplosionInfo()
        if not self.exploded:
            sm.ScatterEvent('OnShipExplode', self.GetModel())
        return spaceObject.SpaceObject.Explode(self, explosionURL=explosionPath, managed=True, delay=delay, scaling=scaling)

    def ShakeShip(self, magnitude, repeat = 1, stepLength = 0.1, timeout = 10.0):
        log.LogException('You should not be using Ship::ShakeShip. It breaks other stuff.')

    def TargetIdleTurrets(self):
        pass


exports = {'spaceObject.Ship': Ship}