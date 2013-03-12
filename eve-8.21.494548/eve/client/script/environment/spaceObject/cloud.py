#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/cloud.py
import spaceObject
import trinity
import timecurves
import log
ENVIRONMENTS = (19713, 19746, 19747, 19748, 19749, 19750, 19751, 19752, 19753, 19754, 19755, 19756)

class Cloud(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.Cloud'

    def LoadModel(self, fileName = None, loadedModel = None):
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        if fileName is None and loadedModel is None:
            if slimItem is None:
                return
            invType = cfg.invtypes.Get(slimItem.typeID)
            if invType is not None:
                typeID = invType.id
                if typeID in ENVIRONMENTS:
                    log.LogInfo('Not loading dungeon environment (%s), since rework is pending.' % invType.GraphicFile())
                    return
            if invType.graphicID is not None:
                if type(invType.graphicID) != type(0):
                    raise RuntimeError('NeedGraphicIDNotMoniker', slimItem.itemID)
                tryFileName = invType.GraphicFile()
                model = trinity.Load(tryFileName)
                return spaceObject.SpaceObject.LoadModel(self, tryFileName, loadedModel=model)
        spaceObject.SpaceObject.LoadModel(self, fileName, loadedModel)

    def Assemble(self):
        self.SetStaticRotation()
        self.SetRadius(self.radius)

    def SetRadius(self, r):
        s = 2.0
        if self.model is not None and hasattr(self.model, 'scaling'):
            self.model.scaling = (s * r, s * r, s * r)


exports = {'spaceObject.Cloud': Cloud}