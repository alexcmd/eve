#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/stargate.py
import spaceObject

class Stargate(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.Stargate'

    def LoadModel(self, fileName = None, loadedModel = None):
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        filename = cfg.invtypes.Get(slimItem.typeID).GraphicFile()
        spaceObject.SpaceObject.LoadModel(self, filename)
        self.SetStaticRotation()

    def Assemble(self):
        if hasattr(self.model, 'ChainAnimationEx'):
            self.model.ChainAnimationEx('NormalLoop', 0, 0, 1.0)
        self.SetupAmbientAudio(u'worldobject_jumpgate_atmo_play')


exports = {'spaceObject.Stargate': Stargate}