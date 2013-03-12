#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/t3shipSvc.py
import uthread
import service
import blue
import sys
import log
import os
import trinity
import const
import form
MAX_WAIT_FOR_OTHER_PROCESS = 60000

class EveShip2BuildEvent:

    def __init__(self):
        self.isDone = False
        self.succeeded = False

    def __call__(self, success):
        self.isDone = True
        self.succeeded = success

    def Wait(self):
        while not self.isDone:
            blue.pyos.synchro.Yield()


class t3ShipSvc(service.Service):
    __guid__ = 'svc.t3ShipSvc'
    __displayname__ = 'Tech 3 Ship Builder'
    __exportedcalls__ = {'GetTech3ShipFromDict': []}

    def __init__(self):
        service.Service.__init__(self)
        self.buildsInProgress = {}

    def Run(self, ms = None):
        self.state = service.SERVICE_RUNNING

    def GetTech3ShipFromDict(self, shipTypeID, subSystems, itemID = None):
        shipsDir = blue.paths.ResolvePathForWriting('cache:/ships/')
        if not os.path.exists(shipsDir):
            os.makedirs(shipsDir)
        t = subSystems.values()
        t.sort()
        uniqueComboID = '_'.join([ str(id) for id in t ])
        cacheVersion = 'v4'
        blackFileCachePath = 'cache:/ships/%s_%s_%s.black' % (cacheVersion, shipTypeID, uniqueComboID)
        gr2FileCachePath = 'cache:/ships/%s_%s_%s.gr2' % (cacheVersion, shipTypeID, uniqueComboID)
        lockFileCachePath = 'cache:/ships/%s_%s_%s.lock' % (cacheVersion, shipTypeID, uniqueComboID)
        blackFilePath = blue.paths.ResolvePathForWriting(blackFileCachePath)
        gr2FilePath = blue.paths.ResolvePathForWriting(gr2FileCachePath)
        lockFilePath = blue.paths.ResolvePathForWriting(lockFileCachePath)
        model = None
        if os.path.exists(blackFilePath) and os.path.exists(gr2FilePath):
            self.LogInfo('Loading existing modular ship from', blackFileCachePath)
            model = trinity.LoadUrgent(blackFileCachePath)
            trinity.WaitForUrgentResourceLoads()
            if model is None:
                self.LogInfo('Failed to load - black file may no longer be compatible - deleting', blackFileCachePath)
                try:
                    os.remove(blackFilePath)
                    os.remove(gr2FilePath)
                    blue.resMan.loadObjectCache.Delete(blackFileCachePath)
                except OSError:
                    self.LogError("Couldn't delete", blackFileCachePath)

        if model is None:
            if blackFileCachePath in self.buildsInProgress:
                self.LogInfo('Build in progress for modular ship at', blackFileCachePath)
                doneChannel = self.buildsInProgress[blackFileCachePath]
                success = doneChannel.receive()
                self.LogInfo('Done waiting for modular ship at', blackFileCachePath)
            else:
                keepTrying = True
                while keepTrying:
                    try:
                        self.LogInfo('Checking for lock file', lockFilePath)
                        lockFile = os.mkdir(lockFilePath)
                        try:
                            self.LogInfo('Starting to build modular ship at', blackFileCachePath)
                            doneChannel = uthread.Channel()
                            self.buildsInProgress[blackFileCachePath] = doneChannel
                            builder = trinity.EveShip2Builder()
                            builder.weldThreshold = 0.01
                            builder.electronic = cfg.invtypes.Get(subSystems[const.groupElectronicSubSystems]).GraphicFile()
                            builder.defensive = cfg.invtypes.Get(subSystems[const.groupDefensiveSubSystems]).GraphicFile()
                            builder.engineering = cfg.invtypes.Get(subSystems[const.groupEngineeringSubSystems]).GraphicFile()
                            builder.offensive = cfg.invtypes.Get(subSystems[const.groupOffensiveSubSystems]).GraphicFile()
                            builder.propulsion = cfg.invtypes.Get(subSystems[const.groupPropulsionSubSystems]).GraphicFile()
                            builder.highDetailOutputName = gr2FileCachePath
                            uthread.new(self.BuildShip, builder, blackFilePath, doneChannel)
                            success = doneChannel.receive()
                            self.LogInfo('Done building modular ship at', blackFileCachePath)
                        finally:
                            keepTrying = False
                            os.rmdir(lockFilePath)

                    except WindowsError:
                        self.LogInfo('Build in progress by another process for modular ship at', blackFileCachePath)
                        doneChannel = uthread.Channel()
                        self.buildsInProgress[blackFileCachePath] = doneChannel
                        start = blue.os.GetWallclockTime()
                        while os.path.exists(lockFilePath):
                            blue.synchro.Yield()
                            timeOut = blue.os.TimeDiffInMs(start, blue.os.GetWallclockTime())
                            if timeOut > MAX_WAIT_FOR_OTHER_PROCESS:
                                self.LogInfo('Build by another process seems to have failed for modular ship at', blackFileCachePath)
                                try:
                                    os.rmdir(lockFilePath)
                                except WindowsError:
                                    self.LogError("Can't delete lock file for modular ship at", blackFileCachePath)
                                    keepTrying = False

                                break

                        if os.path.exists(blackFilePath) and os.path.exists(gr2FilePath):
                            self.LogInfo('Other process finished building modular ship at', blackFileCachePath)
                            keepTrying = False
                            success = True
                        else:
                            success = False

                del self.buildsInProgress[blackFileCachePath]
            if not success:
                return
        if model is None:
            model = trinity.LoadUrgent(blackFileCachePath)
            trinity.WaitForUrgentResourceLoads()
        if itemID:
            sm.ScatterEvent('OnModularShipReady', itemID, blackFileCachePath)
        return model

    def SaveModelToCache(self, model, filePath):
        shipsDir = blue.paths.ResolvePathForWriting('cache:/ships/')
        if not os.path.exists(shipsDir):
            os.makedirs(shipsDir)
        s = os.path.splitext(filePath)
        tmpFilePath = s[0] + '.tmp%d' % blue.os.pid + s[1]
        blue.resMan.SaveObject(model, tmpFilePath)
        os.rename(tmpFilePath, filePath)

    def BuildShip(self, builder, path, doneChannel):
        shipsDir = blue.paths.ResolvePathForWriting('cache:/ships/')
        if not os.path.exists(shipsDir):
            os.makedirs(shipsDir)
        if builder.PrepareForBuild():
            trinity.WaitForResourceLoads()
            evt = EveShip2BuildEvent()
            builder.BuildAsync(evt)
            evt.Wait()
            if evt.succeeded:
                self.LogInfo('Modular model built successfully:', path)
                ship = builder.GetShip()
                ship.shadowEffect = trinity.Tr2Effect()
                ship.shadowEffect.effectFilePath = 'res:/Graphics/Effect/Managed/Space/Ship/Shadow.fx'
                self.SaveModelToCache(ship, path)
                while doneChannel.balance < 0:
                    doneChannel.send(True)

                return
            self.LogError('Failed building ship:', path)
        while doneChannel.balance < 0:
            doneChannel.send(False)

    def MakeModularShipFromShipItem(self, ship):
        subSystemIds = {}
        for fittedItem in ship.GetFittedItems().itervalues():
            if fittedItem.categoryID == const.categorySubSystem:
                subSystemIds[fittedItem.groupID] = fittedItem.typeID

        if len(subSystemIds) < const.visibleSubSystems:
            windowID = 'assembleWindow_modular'
            form.AssembleShip.CloseIfOpen(windowID=windowID)
            form.AssembleShip.Open(windowID=windowID, ship=ship, groupIDs=subSystemIds.keys())
            return
        return self.GetTech3ShipFromDict(ship.typeID, subSystemIds)

    def LoadShipAsHologram(self, redfile):
        baseShip = trinity.Load(redfile)
        if baseShip is None:
            log.LogError('LoadShipAsHologram: could not load ' + str(redfile))
            return
        if baseShip.__bluetype__ != 'trinity.EveShip2':
            log.LogError('LoadShipAsHologram: ' + str(redfile) + ' is not of type EveShip2')
            return
        hologramPath = 'res:/dx9/model/effect/shiptreeui_prototype.red'
        hologramArea = blue.recycler.RecycleOrLoad(hologramPath)
        if hologramArea is None:
            log.LogError('LoadShipAsHologram: could not load ' + str(hologramPath))
            return
        if hologramArea.__bluetype__ != 'trinity.Tr2MeshArea':
            log.LogError('LoadShipAsHologram: ' + str(hologramPath) + ' is not of type Tr2MeshArea')
            return
        if baseShip.shadowEffect is not None:
            if 'skinned_' in baseShip.shadowEffect.effectFilePath.lower():
                if 'skinned_' not in hologramArea.effect.effectFilePath:
                    hologramArea.effect.effectFilePath = hologramArea.effect.effectFilePath.lower().replace('spaceobject/v3/', 'spaceobject/v3/skinned_')
        areas = []
        highDetailMesh = baseShip.highDetailMesh.object
        trinity.WaitForResourceLoads()
        for area in highDetailMesh.opaqueAreas:
            areas.append(area)

        for area in highDetailMesh.transparentAreas:
            areas.append(area)

        del highDetailMesh.opaqueAreas[:]
        del highDetailMesh.transparentAreas[:]
        del highDetailMesh.decalAreas[:]
        del highDetailMesh.depthAreas[:]
        del highDetailMesh.additiveAreas[:]
        for oldArea in areas:
            newArea = hologramArea.CopyTo()
            nmResPath = None
            for res in oldArea.effect.resources:
                if res.name == 'NormalMap':
                    nmResPath = res.resourcePath
                    break

            if nmResPath is not None:
                for res in newArea.effect.resources:
                    if res.name == 'NormalMap':
                        res.resourcePath = nmResPath
                        break

            newArea.index = oldArea.index
            newArea.count = oldArea.count
            highDetailMesh.transparentAreas.append(newArea)

        baseShip.mediumDetailMesh = None
        baseShip.lowDetailMesh = None
        del baseShip.spriteSets[:]
        del baseShip.spotlightSets[:]
        del baseShip.decals[:]
        del baseShip.children[:]
        return baseShip