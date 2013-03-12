#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/capsule.py
import spaceObject
import nodemanager
import state
import trinity

class Capsule(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.Capsule'

    def __init__(self):
        spaceObject.SpaceObject.__init__(self)
        self.targets = []
        self.cloakedCopy = None
        self.cloakedShaderStorage = None

    def LoadModel(self, fileName = None, loadedModel = None):
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        fileName = cfg.invtypes.Get(slimItem.typeID).GraphicFile()
        spaceObject.SpaceObject.LoadModel(self, fileName)
        self.Display(1)

    def Assemble(self):
        if self.model is None:
            self.LogWarn('Capsule::Assemble - No model')
            return
        self.targets = self.model.damageLocators
        self.UnSync()
        self.FitBoosters()

    def Explode(self):
        return spaceObject.SpaceObject.Explode(self, 'res:/Model/Effect/capsule_explosion.blue')

    def Release(self):
        if self.released:
            return
        self.KillCloakedCopy()
        spaceObject.SpaceObject.Release(self, 'Capsule')

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
            self.LogInfo('Removed cloaked copy of capsule')

    def OnDamageState(self, damageState):
        if self.model is None:
            self.LogWarn('OnDamageState - No model')
            return
        self.SetDamageStateSingle(damageState[2])

    def SetDamageStateSingle(self, health):
        damage = 1.0 - health
        if damage < 0.2:
            damageEmitter = None
            for child in self.model.children:
                if getattr(child, 'name', '') == 'damageEmitter':
                    damageEmitter = child
                    break

            if damageEmitter is not None:
                self.model.children.fremove(damageEmitter)
            self.burning = False
        elif self.id == sm.StartService('state').GetExclState(state.lookingAt):
            self.burning = True
            emitter = trinity.Load('res:/Emitter/Damage/fuel_low.red')
            emitter.name = 'damageEmitter'
            emitter.scaling = (0.2, 0.2, 0.2)
            if len(self.model.damageLocators):
                emitter.translation = (self.model.damageLocators[0][0], self.model.damageLocators[0][1], self.model.damageLocators[0][2])
            self.model.children.append(emitter)


exports = {'spaceObject.Capsule': Capsule}