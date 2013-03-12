#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/LargeCollidableObject.py
import spaceObject

class LargeCollidableObject(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.LargeCollidableObject'

    def Assemble(self):
        self.SetStaticRotation()
        if getattr(self.model, 'ChainAnimationEx', None) is not None:
            self.model.ChainAnimationEx('NormalLoop', 0, 0, 1.0)


exports = {'spaceObject.LargeCollidableObject': LargeCollidableObject}