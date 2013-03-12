#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/corpse.py
import spaceObject

class Corpse(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.Corpse'

    def LoadModel(self, fileName = None, loadedModel = None):
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        gender = ['male', 'female'][slimItem.typeID == const.typeCorpseFemale]
        path = 'res:/dx9/Model/Face/fullbody_char/corpses/corpse_%s0%s.red' % (gender, self.id % 3 + 1)
        spaceObject.SpaceObject.LoadModel(self, path)

    def Explode(self):
        if self.model is None:
            return
        explosionURL = 'res:/Model/Effect3/capsule_explosion.red'
        return spaceObject.SpaceObject.Explode(self, explosionURL)


exports = {'spaceObject.Corpse': Corpse}