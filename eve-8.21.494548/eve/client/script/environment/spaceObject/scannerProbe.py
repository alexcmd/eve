#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/scannerProbe.py
import spaceObject
import blue
import uthread
import trinity
import random

class ScannerProbe(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.ScannerProbe'
    __notifyevents__ = ['OnSlimItemChange']

    def __init__(self):
        spaceObject.SpaceObject.__init__(self)
        sm.RegisterNotify(self)

    def Release(self, origin = None):
        sm.UnregisterNotify(self)
        spaceObject.SpaceObject.Release(self)

    def FakeWarp(self):
        blue.pyos.synchro.SleepSim(random.randint(100, 1000))
        url = 'res:/Model/Effect3/ProbeWarp.red'
        gfx = trinity.Load(url)
        if gfx.__bluetype__ != 'trinity.EveRootTransform':
            root = trinity.EveRootTransform()
            root.children.append(gfx)
            root.name = url
            gfx = root
        gfx.translationCurve = self
        scene = sm.StartService('sceneManager').GetRegisteredScene('default')
        scene.objects.append(gfx)
        uthread.pool('ScannerProbe::HideBall', self.HideBall)
        uthread.pool('ScannerProbe::DelayedRemove', self.DelayedRemove, 3000, self.model)
        uthread.pool('ScannerProbe::DelayedRemove', self.DelayedRemove, 3000, gfx)

    def DelayedRemove(self, duration, gfx):
        if gfx is None:
            return
        if duration != 0:
            blue.pyos.synchro.SleepSim(duration)
        if hasattr(gfx, 'translationCurve'):
            gfx.translationCurve = None
        scene = sm.StartService('sceneManager').GetRegisteredScene('default')
        if scene is not None:
            scene.objects.fremove(gfx)

    def HideBall(self):
        blue.pyos.synchro.SleepSim(500)
        if self.model:
            self.model.display = 0

    def OnSlimItemChange(self, oldItem, newItem):
        if oldItem.itemID != self.id or not getattr(newItem, 'warpingAway', 0):
            return
        uthread.pool('ScanProbe::FakeWarp', self.FakeWarp)

    def Assemble(self):
        spaceObject.SpaceObject.Assemble(self)

    def Explode(self):
        explosionURL = 'res:/Emitter/explosion_end.blue'
        scale = 0.2 + random.random() * 0.1
        return spaceObject.SpaceObject.Explode(self, explosionURL, scaling=scale)

    def LoadModel(self, fileName = None, loadedModel = None):
        slimItem = sm.StartService('michelle').GetItem(self.id)
        self.LogInfo('Scanner Probe - LoadModel', slimItem.nebulaType)
        fileName = cfg.invtypes.Get(slimItem.typeID).GraphicFile()
        spaceObject.SpaceObject.LoadModel(self, fileName, loadedModel)


exports = {'spaceObject.ScannerProbe': ScannerProbe}