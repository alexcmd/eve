#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/spaceObject.py
import blue
import decometaclass
import sys
import timecurves
import uthread
import trinity
import random
import log
import types
import audio2
import geo2
import util
from foo import Vector3
import locks
from string import split
DEG2RAD = 0.0174532925199
gfxRaceAmarr = 1
gfxRaceCaldari = 2
gfxRaceGallente = 3
gfxRaceMinmatar = 4
gfxRaceJove = 5
gfxRaceAngel = 6
gfxRaceSleeper = 7
gfxRaceORE = 8
gfxRaceConcord = 9
gfxRaceRogueDrone = 10
gfxRaceSansha = 11
gfxRaceSOCT = 12
gfxRaceTalocan = 13
gfxRaceGeneric = 14
BOOSTER_GFX_SND_RESPATHS = {gfxRaceAmarr: ('res:/dx9/model/ship/booster/booster_amarr.red', 'ship_booster_amarr'),
 gfxRaceCaldari: ('res:/dx9/model/ship/booster/booster_caldari.red', 'ship_booster_caldari'),
 gfxRaceGallente: ('res:/dx9/model/ship/booster/booster_gallente.red', 'ship_booster_gallente'),
 gfxRaceMinmatar: ('res:/dx9/model/ship/booster/booster_minmatar.red', 'ship_booster_minmatar'),
 gfxRaceJove: ('res:/dx9/model/ship/booster/booster_jove.red', 'ship_booster_jove'),
 gfxRaceAngel: ('res:/dx9/model/ship/booster/booster_angel.red', 'ship_booster_angel'),
 gfxRaceSleeper: ('res:/dx9/model/ship/booster/booster_sleeper.red', 'ship_booster_sleeper'),
 gfxRaceORE: ('res:/dx9/model/ship/booster/booster_ORE.red', 'ship_booster_ORE'),
 gfxRaceConcord: ('res:/dx9/model/ship/booster/booster_concord.red', 'ship_booster_concord'),
 gfxRaceRogueDrone: ('res:/dx9/model/ship/booster/booster_roguedrone.red', 'ship_booster_roguedrone'),
 gfxRaceSansha: ('res:/dx9/model/ship/booster/booster_sansha.red', 'ship_booster_sansha'),
 gfxRaceSOCT: ('res:/dx9/model/ship/booster/booster_soct.red', 'ship_booster_soct'),
 gfxRaceTalocan: ('res:/dx9/model/ship/booster/booster_talocan.red', 'ship_booster_talocan'),
 gfxRaceGeneric: ('res:/dx9/model/ship/booster/booster_generic.red', 'ship_booster_generic')}

class SpaceObject(decometaclass.WrapBlueClass('destiny.ClientBall')):
    __guid__ = 'spaceObject.SpaceObject'
    __persistdeco__ = 0
    __update_on_reload__ = 1

    def __init__(self):
        self.explodeOnRemove = False
        self.exploded = False
        self.model = None
        self.released = False
        self.forceLOD = False
        self.wreckID = None
        self.audioEntities = []
        self.generalAudioEntity = None
        self.boosterAudioEvent = ''
        self.audioPumpStarted = False
        self.logChannel = log.GetChannel(self.__guid__)
        self.modelLoadedEvent = locks.Event()
        self.explosionModel = None
        self.typeID = None
        self.raceID = None
        self.explosionManager = util.ExplosionManager()

    def Log(self, channelID, *args, **keywords):
        if self.logChannel.IsOpen(channelID):
            try:
                self.logChannel.Log(' '.join(map(strx, args)), channelID, keywords.get('backtrace', 1))
            except TypeError:
                self.logChannel.Log('[X]'.join(map(strx, args)).replace('\x00', '\\0'), channelID, keywords.get('backtrace', 1))
                sys.exc_clear()

    def LogInfo(self, *args, **keywords):
        self.Log(1, '[', self.id, ']', *args, **keywords)

    def LogWarn(self, *args, **keywords):
        self.Log(2, '[', self.id, ']', *args, **keywords)

    def LogError(self, *args, **keywords):
        self.Log(4, '[', self.id, ']', *args, **keywords)

    def Prepare(self, spaceMgr):
        self.spaceMgr = spaceMgr
        self.LoadModel()
        self.Assemble()

    def HasBlueInterface(self, object, interfaceName):
        if hasattr(object, 'TypeInfo'):
            return interfaceName in object.TypeInfo()[1]
        return False

    def GetModel(self):
        if not self.model:
            self.modelLoadedEvent.wait()
        return self.model

    def LoadModel(self, fileName = None, loadedModel = None):
        shipType = cfg.invtypes.Get(self.typeID)
        if shipType is not None:
            g = cfg.graphics.GetIfExists(shipType.graphicID)
            self.raceID = getattr(g, 'gfxRaceID', None)
        if fileName is None and loadedModel is None:
            if self.typeID is None:
                return
            if shipType.graphicID is not None:
                if shipType.Graphic():
                    fileName = shipType.GraphicFile()
                    if not (fileName.lower().endswith('.red') or fileName.lower().endswith('.blue')):
                        filename_and_turret_type = split(fileName, ' ')
                        fileName = filename_and_turret_type[0]
        self.LogInfo('LoadModel', fileName)
        if fileName is None and loadedModel is None:
            self.LogError('Error: Object type %s has invalid graphicFile, using graphicID: %s' % (self.typeID, cfg.invtypes.Get(self.typeID).graphicID))
            return
        model = None
        if fileName is not None and len(fileName) and loadedModel is None:
            try:
                model = blue.resMan.LoadObject(fileName)
            except:
                model = None
                sys.exc_clear()

        else:
            model = loadedModel
        if not model:
            log.LogError('Could not load model for spaceobject. FileName:', fileName, ' id:', self.id, ' typeID:', getattr(self, 'typeID', '?'))
            log.LogError('Type is:', cfg.invtypes.Get(self.typeID).typeName)
            return
        self.model = model
        if not hasattr(model, 'translationCurve'):
            self.LogError('LoadModel - Model in', fileName, "doesn't have a translationCurve.")
        else:
            model.translationCurve = self
            model.rotationCurve = self
        model.name = '%d' % self.id
        if hasattr(model, 'useCurves'):
            model.useCurves = 1
        if self.model is not None and self.HasBlueInterface(self.model, 'IEveSpaceObject2'):
            scene = sm.StartService('sceneManager').GetRegisteredScene('default')
            if scene is not None:
                scene.objects.append(self.model)
        else:
            raise RuntimeError('Invalid object loaded by spaceObject: %s' % str(self.model))
        sm.StartService('FxSequencer').NotifyModelLoaded(self.id)
        self.modelLoadedEvent.set()

    def Assemble(self):
        pass

    def SetDefaultLOD(self):
        if self.model is None:
            return
        if self.model.__typename__ == 'TriLODGroup':
            if settings.user.ui.Get('lod', 1) == 0 and not self.forceLOD:
                self.model.lodBy = trinity.TRILB_NONE
                self.model.activeLevel = 0
            else:
                self.model.lodBy = trinity.TRITB_CAMERA_DISTANCE_FOV_HEIGHT
                self.SetLODGroupRadius()
                for i in range(8):
                    setattr(self.model, 'treshold' + str(i), 0.0)

                childrenCnt = len(self.model.children)
                if childrenCnt == 4:
                    self.model.treshold0 = 0.025
                    self.model.treshold1 = 0.025
                    self.model.treshold2 = 0.013
                elif childrenCnt == 3:
                    self.model.treshold0 = 0.08
                    self.model.treshold1 = 0.009
                else:
                    self.model.treshold0 = 0.025

    def SetStaticRotation(self):
        if self.model is None:
            return
        self.model.rotationCurve = None
        slimItem = sm.StartService('michelle').GetItem(self.id)
        if slimItem:
            rot = getattr(slimItem, 'dunRotation', None)
            if rot is not None:
                yaw, pitch, roll = rot
                quat = geo2.QuaternionRotationSetYawPitchRoll(yaw * DEG2RAD, pitch * DEG2RAD, roll * DEG2RAD)
                if hasattr(self.model, 'rotation'):
                    if type(self.model.rotation) == types.TupleType:
                        self.model.rotation = quat
                    else:
                        self.model.rotation.SetYawPitchRoll(yaw * DEG2RAD, pitch * DEG2RAD, roll * DEG2RAD)
                else:
                    self.model.rotationCurve = trinity.TriRotationCurve()
                    self.model.rotationCurve.value = quat

    def FindClosestMoonDir(self):
        bp = sm.StartService('michelle').GetBallpark()
        dist = 1e+100
        closestMoonID = None
        for ballID, slimItem in bp.slimItems.iteritems():
            if slimItem.groupID == const.groupMoon:
                test = bp.DistanceBetween(self.id, ballID)
                if test < dist:
                    dist = test
                    closestMoonID = ballID

        if closestMoonID is None:
            return Vector3([1.0, 0.0, 0.0])
        moon = bp.GetBall(closestMoonID)
        direction = Vector3([self.x - moon.x, self.y - moon.y, self.z - moon.z])
        return direction

    def FindClosestPlanetDir(self):
        bp = sm.StartService('michelle').GetBallpark()
        dist = 1e+100
        closestPlanetID = None
        for ballID, slimItem in bp.slimItems.iteritems():
            if slimItem.groupID == const.groupPlanet:
                test = bp.DistanceBetween(self.id, ballID)
                if test < dist:
                    dist = test
                    closestPlanetID = ballID

        if closestPlanetID is None:
            return Vector3([1.0, 0.0, 0.0])
        planet = bp.GetBall(closestPlanetID)
        direction = Vector3([self.x - planet.x, self.y - planet.y, self.z - planet.z])
        return direction

    def GetStaticDirection(self):
        slimItem = sm.StartService('michelle').GetItem(self.id)
        if slimItem is None:
            return
        if slimItem.groupID == const.groupMoonMining:
            direction = self.FindClosestMoonDir()
        else:
            direction = getattr(slimItem, 'dunDirection', None)
        return direction

    def SetStaticDirection(self):
        if self.model is None:
            return
        self.model.rotationCurve = None
        direction = self.GetStaticDirection()
        if direction is None:
            self.LogError('Space object', self.id, 'has no static direction defined - no rotation will be applied')
            return
        self.AlignToDirection(direction)

    def AlignToDirection(self, direction):
        zaxis = Vector3(direction)
        if zaxis.Length2() > 0.0:
            Up = Vector3([0.0, 1.0, 0.0])
            zaxis.Normalize()
            xaxis = zaxis ^ Up
            if xaxis.Length2() == 0.0:
                zaxis += Vector3().Randomize(0.0001)
                zaxis.Normalize()
                xaxis = zaxis ^ Up
            xaxis.Normalize()
            yaxis = xaxis ^ zaxis
        else:
            self.LogError('Space object', self.id, 'has zero dunDirection. I cannot rotate it.')
            return
        mat = ((xaxis[0],
          xaxis[1],
          xaxis[2],
          0.0),
         (yaxis[0],
          yaxis[1],
          yaxis[2],
          0.0),
         (-zaxis[0],
          -zaxis[1],
          -zaxis[2],
          0.0),
         (0.0, 0.0, 0.0, 1.0))
        quat = geo2.QuaternionRotationMatrix(mat)
        if self.model and self.HasBlueInterface(self.model, 'IEveSpaceObject2') and hasattr(self.model, 'modelRotationCurve'):
            if not self.model.modelRotationCurve:
                self.model.modelRotationCurve = trinity.TriRotationCurve(0.0, 0.0, 0.0, 1.0)
            self.model.modelRotationCurve.value = quat
        else:
            self.model.rotationCurve = None

    def UnSync(self):
        if self.model is None:
            return
        startTime = long(random.random() * 123456.0 * 1234.0)
        scaling = 0.95 + random.random() * 0.1
        curves = timecurves.ReadCurves(self.model)
        timecurves.ResetTimeCurves(curves, startTime, scaling)

    def SetMiniballExplosions(self, gfx):
        if gfx is None:
            return
        if not self.HasBlueInterface(gfx, 'IEveSpaceObject2'):
            self.LogWarn(self.id, 'SetMiniBallExplosions called for old content!')
            return
        miniExplosions = [ x for x in gfx.Find('trinity.EveTransform') if x.name == 'SmallExplosion' ]
        if len(self.miniBalls) > 0:
            for explosionTransform in miniExplosions:
                miniball = random.choice(self.miniBalls)
                explosionTransform.translation = (miniball.x, miniball.y, miniball.z)

    def Display(self, display = 1, canYield = True):
        if self.model is None:
            self.LogWarn('Display - No model')
            return
        if canYield:
            blue.synchro.Yield()
        if display and self.IsCloaked():
            if eve.session.shipid == self.id:
                sm.StartService('FxSequencer').OnSpecialFX(self.id, None, None, None, None, None, 'effects.CloakNoAmim', 0, 1, 0, 5, 0)
            return
        if self.model:
            self.model.display = display

    def IsCloaked(self):
        return self.isCloaked

    def OnDamageState(self, damageState):
        pass

    def GetDamageState(self):
        return self.spaceMgr.ballpark.GetDamageState(self.id)

    def DoFinalCleanup(self):
        if not sm.IsServiceRunning('FxSequencer'):
            return
        sm.GetService('FxSequencer').RemoveAllBallActivations(self.id)
        self.ClearExplosion()
        if not self.released:
            self.explodeOnRemove = False
            self.Release()

    def ClearExplosion(self, model = None):
        if hasattr(self, 'gfx') and self.gfx is not None:
            self.RemoveAndClearModel(self.gfx)
            self.gfx = None
        if self.explosionModel is not None:
            if getattr(self, 'explosionDisplayBinding', False):
                self.explosionDisplayBinding.destinationObject = None
                self.explosionDisplayBinding = None
            self.RemoveAndClearModel(self.explosionModel)
            self.explosionModel = None

    def Release(self, origin = None):
        uthread.new(self._Release, origin)

    def _Release(self, origin = None):
        self.LogInfo('Release')
        if self.released:
            return
        self.released = True
        if self.explodeOnRemove:
            delay = self.Explode()
            if delay:
                delay = min(delay, 2000)
                blue.synchro.SleepSim(delay)
        self.Display(display=0, canYield=False)
        uthread.new(self.RemoveAndClearModel, self.model)
        self.audioEntities = []
        self.generalAudioEntity = None
        self.model = None
        self.spaceMgr = None

    def RemoveAndClearModel(self, model, scene = None):
        if model:
            if hasattr(model, 'translationCurve'):
                model.translationCurve = None
                model.rotationCurve = None
            if hasattr(model, 'observers'):
                for ob in model.observers:
                    ob.observer = None

        else:
            self.released = True
            return
        if scene is None:
            scene = sm.StartService('sceneManager').GetRegisteredScene('default')
        if scene:
            scene.objects.fremove(model)

    def GetExplosionInfo(self, basePath = None):
        EXPLOSION_PATH = basePath or 'res:/fisfx/deathexplosion/death'
        RACEID_TO_NAME_MAP = {gfxRaceAmarr: 'amarr',
         gfxRaceCaldari: 'caldari',
         gfxRaceGallente: 'gallente',
         gfxRaceMinmatar: 'minmatar',
         gfxRaceJove: 'jove',
         gfxRaceAngel: 'angel',
         gfxRaceSleeper: 'sleeper',
         gfxRaceORE: 'ore',
         gfxRaceConcord: 'roguedrone',
         gfxRaceRogueDrone: 'roguedrone',
         gfxRaceSansha: 'sansha',
         gfxRaceSOCT: 'roguedrone',
         gfxRaceTalocan: 'roguedrone',
         gfxRaceGeneric: 'roguedrone'}
        name = RACEID_TO_NAME_MAP.get(self.raceID, 'roguedrone')
        size = '_m_'
        radius = getattr(self.model, 'boundingSphereRadius', self.radius)
        delay = 0
        scale = 1.0
        if radius < 20.0:
            size = '_d_'
            scale = radius / 20.0
        elif radius < 100.0:
            size = '_s_'
            delay = 100
            scale = radius / 100.0
        elif radius < 400.0:
            size = '_m_'
            delay = 250
            scale = radius / 400.0
        elif radius < 1500.0:
            size = '_l_'
            delay = 500
            scale = radius / 700.0
        elif radius < 6000.0:
            size = '_h_'
            delay = 1000
            scale = radius / 6000.0
        else:
            size = '_t_'
            delay = 2000
        path = EXPLOSION_PATH + size + name + '.red'
        info = (delay, scale)
        return (path, info)

    def Explode(self, explosionURL = None, scaling = 1.0, managed = False, delay = 0.0):
        self.LogInfo('Exploding')
        if self.exploded:
            return False
        sm.ScatterEvent('OnObjectExplode', self.GetModel())
        self.exploded = True
        delayedRemove = delay
        if settings.user.ui.Get('explosionEffectsEnabled', 1):
            gfx = None
            if managed:
                gfx = self.explosionManager.GetExplosion(explosionURL, callback=self.ClearExplosion)
            else:
                if explosionURL is None:
                    self.LogError('explosionURL not set when calling Explode. Possibly wrongly authored content. typeID:', self.typeID)
                    explosionURL, (delay, scaling) = self.GetExplosionInfo()
                explosionURL = explosionURL.replace('.blue', '.red').replace('/Effect/', '/Effect3/')
                gfx = trinity.Load(explosionURL)
                if not gfx:
                    self.LogError('Failed to load explosion: ', explosionURL, ' - using default')
                    gfx = trinity.Load('res:/Model/Effect/Explosion/entityExplode_large.red')
                if gfx.__bluetype__ == 'trinity.EveEffectRoot':
                    self.LogWarn('EveEffectRoot explosion not managed for %s. ExplosionManager circumvented.' % explosionURL)
                    gfx.Start()
                elif gfx.__bluetype__ != 'trinity.EveRootTransform':
                    root = trinity.EveRootTransform()
                    root.children.append(gfx)
                    root.name = explosionURL
                    gfx = root
            gfx.translationCurve = self
            self.explosionModel = gfx
            scale = scaling
            gfx.scaling = (gfx.scaling[0] * scale, gfx.scaling[1] * scale, gfx.scaling[2] * scale)
            scene = sm.StartService('sceneManager').GetRegisteredScene('default')
            scene.objects.append(gfx)
        if self.wreckID is not None:
            wreckBall = sm.StartService('michelle').GetBall(self.wreckID)
            if wreckBall is not None:
                uthread.pool('Wreck::DisplayWreck', wreckBall.DisplayWreck, 500)
        return delayedRemove

    def SetLODGroupRadius(self):
        r = self.FindSimpleBoundingRadius(self.model.children[0])
        self.model.boundingSphereRadius = r
        self.boundingSphereRadius = r

    def FindSimpleBoundingRadius(self, transform):
        if hasattr(transform, 'object') and hasattr(transform.object, 'vertexRes') and transform.object.vertexRes is not None:
            minbox = transform.object.vertexRes.meshBoxMin.CopyTo()
            maxbox = transform.object.vertexRes.meshBoxMax.CopyTo()
            minbox.TransformCoord(transform.localTransform)
            maxbox.TransformCoord(transform.localTransform)
            spear = maxbox - minbox
            r = spear.Length() * 0.5
            if r * 10.0 < self.radius:
                r = self.radius
            return r
        return self.radius

    def FindHierarchicalBoundingBox(self, transform, printout, parentMat = trinity.TriMatrix(), indent = '', minx = 1e+100, maxx = -1e+100, miny = 1e+100, maxy = -1e+100, minz = 1e+100, maxz = -1e+100, parentScale = trinity.TriVector(1.0, 1.0, 1.0)):
        transform.Update(blue.os.GetSimTime())
        if hasattr(transform, 'translation') and transform.__typename__ in ('TriTransform', 'TriSplTransform', 'TriLODGroup'):
            if transform.__typename__ == 'TriTransform':
                if transform.transformBase != trinity.TRITB_OBJECT:
                    return (minx,
                     maxx,
                     miny,
                     maxy,
                     minz,
                     maxz)
            if hasattr(transform, 'object') and hasattr(transform.object, 'vertexRes') and transform.object.vertexRes is not None:
                damin = transform.object.vertexRes.meshBoxMin.CopyTo()
                damax = transform.object.vertexRes.meshBoxMax.CopyTo()
                damin.TransformCoord(transform.localTransform)
                damax.TransformCoord(transform.localTransform)
                damin.TransformCoord(parentMat)
                damax.TransformCoord(parentMat)
                minx = min(minx, min(damin.x, damax.x))
                maxx = max(maxx, max(damin.x, damax.x))
                miny = min(miny, min(damin.y, damax.y))
                maxy = max(maxy, max(damin.y, damax.y))
                minz = min(minz, min(damin.z, damax.z))
                maxz = max(maxz, max(damin.z, damax.z))
            newmat = transform.localTransform.CopyTo()
            newmat.Multiply(parentMat)
            for child in transform.children:
                indent = indent + '  '
                minx, maxx, miny, maxy, minz, maxz = self.FindHierarchicalBoundingBox(child, printout, newmat, indent, minx, maxx, miny, maxy, minz, maxz, parentScale)

        return (minx,
         maxx,
         miny,
         maxy,
         minz,
         maxz)

    def FitBoosters(self, alwaysOn = False, enableTrails = True):
        if self.typeID is None:
            return
        if self.raceID is None:
            self.LogError('SpaceObject type %s has invaldi raceID (not set!) ' % self.typeID)
            self.raceID = gfxRaceGeneric
        boosterResPath = BOOSTER_GFX_SND_RESPATHS[self.raceID][0]
        boosterSoundName = BOOSTER_GFX_SND_RESPATHS[self.raceID][1]
        boosterFxObj = trinity.Load(boosterResPath)
        if boosterFxObj is None:
            return
        if self.model is None:
            log.LogWarn('No model to fit boosters to on spaceobject with id = ' + str(self.id))
            return
        if not hasattr(self.model, 'boosters'):
            log.LogWarn('Model has no attribute boosters on spaceobject with id = ' + str(self.id))
            return
        self.model.boosters = boosterFxObj
        self.model.boosters.maxVel = self.maxVelocity
        self.model.RebuildBoosterSet()
        self.model.boosters.alwaysOn = alwaysOn
        if not enableTrails:
            self.model.boosters.trails = None
        boosterAudioLocators = filter(lambda node: node.name.startswith('locator_audio_booster'), self.model.locators)
        tmpEntity = None
        tmpParameter = None
        for audLocator in boosterAudioLocators:
            tlpo = trinity.TriObserverLocal()
            transform = audLocator.transform
            tlpo.front = (-transform[2][0], -transform[2][1], -transform[2][2])
            tlpo.position = (transform[3][0], transform[3][1], transform[3][2])
            if tmpEntity is None:
                tmpEntity = audio2.AudEmitter('ship_' + str(self.id) + '_booster')
                tmpParameter = audio2.AudParameter()
                tmpParameter.name = u'ship_speed'
                tmpEntity.parameters.append(tmpParameter)
                self.shipSpeedParameter = tmpParameter
            tlpo.observer = tmpEntity
            self.audioEntities.append(tmpEntity)
            self.model.observers.append(tlpo)

        boosterSize = 'f'
        if self.radius > 99:
            boosterSize = 'c'
            if self.radius > 309:
                boosterSize = 'bs'
                if self.radius > 1500:
                    boosterSize = 'dr'
                    if self.radius > 5000:
                        boosterSize = 't'
        self.boosterAudioEvent = '_'.join([boosterSoundName, boosterSize, 'play'])
        if tmpEntity is not None:
            self.model.audioSpeedParameter = self.shipSpeedParameter
            baseVelocity = 1
            if util.IsNPC(self.id):
                baseVelocity = sm.StartService('godma').GetTypeAttribte(self.typeID, const.attributeEntityCruiseSpeed)
            else:
                baseVelocity = sm.StartService('godma').GetTypeAttribute(self.typeID, const.attributeMaxVelocity)
            if baseVelocity is None:
                baseVelocity = 1.0
            self.model.maxSpeed = baseVelocity
            tmpEntity.SendEvent(unicode(self.boosterAudioEvent))

    def SetupAmbientAudio(self, defaultSoundUrl = None):
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        audioSvc = sm.GetService('audio')
        validResource = True
        soundUrl = None
        soundUrl = audioSvc.GetSoundUrlForType(slimItem)
        if soundUrl is not None:
            validResource = soundUrl.startswith('wise:/')
        if soundUrl is None or len(soundUrl) <= 0 or not validResource:
            if not validResource:
                self.LogWarn(self.id, 'Specified sound resource is not a Wwise resource, either default sound or no sound will be played! (url = %s)' % soundUrl)
            if defaultSoundUrl is None:
                return
            soundUrl = defaultSoundUrl
        self.PlayGeneralAudioEvent(unicode(soundUrl))

    def LookAtMe(self):
        pass

    def GetGeneralAudioEntity(self):
        if self.generalAudioEntity is None:
            if self.model is not None and hasattr(self.model, 'observers'):
                triObserver = trinity.TriObserverLocal()
                self.generalAudioEntity = audio2.AudEmitter('spaceObject_' + str(self.id) + '_general')
                triObserver.observer = self.generalAudioEntity
                self.audioEntities.append(self.generalAudioEntity)
                self.model.observers.append(triObserver)
            else:
                self.LogWarn(self.id, 'unable to construct generalized audio entity - model has no observers property')
        return self.generalAudioEntity

    def PlayGeneralAudioEvent(self, eventName):
        audEntity = self.GetGeneralAudioEntity()
        if audEntity is None:
            return
        if eventName.startswith('wise:/'):
            eventName = eventName[6:]
        self.LogInfo(self.id, 'playing audio event', eventName, 'on generalized emitter')
        audEntity.SendEvent(unicode(eventName))


exports = {'spaceObject.SpaceObject': SpaceObject,
 'spaceObject.BOOSTER_GFX_SND_RESPATHS': BOOSTER_GFX_SND_RESPATHS,
 'spaceObject.gfxRaceAmarr': gfxRaceAmarr,
 'spaceObject.gfxRaceCaldari': gfxRaceCaldari,
 'spaceObject.gfxRaceGallente': gfxRaceGallente,
 'spaceObject.gfxRaceMinmatar': gfxRaceMinmatar,
 'spaceObject.gfxRaceJove': gfxRaceJove,
 'spaceObject.gfxRaceAngel': gfxRaceAngel,
 'spaceObject.gfxRaceSleeper': gfxRaceSleeper,
 'spaceObject.gfxRaceORE': gfxRaceORE,
 'spaceObject.gfxRaceConcord': gfxRaceConcord,
 'spaceObject.gfxRaceRogueDrone': gfxRaceRogueDrone,
 'spaceObject.gfxRaceSansha': gfxRaceSansha,
 'spaceObject.gfxRaceSOCT': gfxRaceSOCT,
 'spaceObject.gfxRaceTalocan': gfxRaceTalocan,
 'spaceObject.gfxRaceGeneric': gfxRaceGeneric}