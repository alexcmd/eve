#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\RenderTargetManager\RenderTargetManager.py
import blue
import trinity
import telemetry
import uthread

class RenderTargetManager(object):
    __metaclass__ = telemetry.ZONE_PER_METHOD
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state
        if not hasattr(self, 'keepAliveMS'):
            self.targets = {}
            self.lockedTargets = {}
            self.targetsSleepCycles = {}
            self.keepAliveMS = 3000
        trinity.device.RegisterResource(self)

    def OnCreate(self, dev):
        pass

    def OnInvalidate(self, level):
        self.targets.clear()
        self.targetsSleepCycles.clear()

    def GetRenderTarget(self, renderTargetFormat, width, height, locked = False):
        i = 0
        hashKey = self.__Hash(renderTargetFormat, width, height, i)
        while self.lockedTargets.get(hashKey):
            i += 1
            hashKey = self.__Hash(renderTargetFormat, width, height, i)

        rt = self.targets.get(hashKey)
        if rt and locked:
            self.lockedTargets[hashKey] = rt
        reapTasklet = None
        while not rt:
            try:
                rt = trinity.Tr2RenderTarget(width, height, 1, renderTargetFormat)
                self.targets[hashKey] = rt
                if locked:
                    self.lockedTargets[hashKey] = rt
                reapTasklet = uthread.new(self.Reaper_t, hashKey).context = 'RenderTargetMananger::Reaper'
            except (trinity.E_OUTOFMEMORY, trinity.D3DERR_OUTOFVIDEOMEMORY):
                raise 
            except trinity.DeviceLostError:
                rt = None
                blue.synchro.SleepWallclock(100)

        sleepCycles = self.targetsSleepCycles.get(hashKey, 0)
        self.targetsSleepCycles[hashKey] = sleepCycles + 1
        if reapTasklet:
            uthread.schedule(reapTasklet)
        return rt

    def ReturnLockedRenderTarget(self, renderTarget):
        foundKey = None
        for key, value in self.lockedTargets.iteritems():
            if id(value) == id(renderTarget):
                foundKey = key
                break

        if foundKey in self.lockedTargets:
            del self.lockedTargets[foundKey]

    def Reaper_t(self, hashKey):
        if self.targetsSleepCycles.get(hashKey, 0) > 0:
            self.targetsSleepCycles[hashKey] -= 1
            blue.synchro.SleepWallclock(self.keepAliveMS)
        if self.targets.get(hashKey):
            del self.targets[hashKey]
        if self.lockedTargets.get(hashKey):
            del self.lockedTargets[hashKey]

    def __Hash(self, textureFormat, width, height, level):
        k = (textureFormat,
         width,
         height,
         level)
        return hash(k)