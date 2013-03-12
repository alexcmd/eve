#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/backgroundObject.py
import spaceObject
import trinity

class BackgroundObject(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.BackgroundObject'

    def LoadModel(self):
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        graphicURL = cfg.invtypes.Get(slimItem.typeID).GraphicFile()
        object = trinity.Load(graphicURL)
        self.backgroundObject = object
        scene = sm.StartService('sceneManager').GetRegisteredScene('default')
        scene.backgroundObjects.append(object)

    def Release(self):
        if self.released:
            return
        scene = sm.StartService('sceneManager').GetRegisteredScene('default')
        scene.backgroundObjects.fremove(self.backgroundObject)
        self.backgroundObject = None
        spaceObject.SpaceObject.Release(self, 'BackgroundObject')


exports = {'spaceObject.BackgroundObject': BackgroundObject}