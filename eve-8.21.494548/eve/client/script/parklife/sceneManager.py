#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/parklife/sceneManager.py
from __future__ import with_statement
import blue
import telemetry
import util
import log
import trinity
import audio2
import service
import nodemanager
import locks
import paperDoll
import geo2
import sys
from math import asin, atan2
SCENE_TYPE_CHARACTER_CREATION = 0
SCENE_TYPE_INTERIOR = 1
SCENE_TYPE_SPACE = 2

class SceneContext():

    def __init__(self, scene = None, camera = None, sceneKey = 'default', sceneType = None, renderJob = None):
        self.scene = scene
        self.camera = camera
        self.sceneKey = sceneKey
        self.sceneType = sceneType
        self.renderJob = renderJob


class SceneManager(service.Service):
    __guid__ = 'svc.sceneManager'
    __exportedcalls__ = {'LoadScene': [],
     'GetScene': [],
     'GetIncarnaRenderJob': [],
     'EnableIncarnaRendering': []}
    __startupdependencies__ = ['settings', 'device']
    __notifyevents__ = ['OnGraphicSettingsChanged', 'OnSessionChanged', 'OnReleaseBallpark']

    def __init__(self):
        service.Service.__init__(self)
        self.uiBackdropScene = None
        self.ProcessImportsAndCreateScenes()
        self.primaryJob = SceneContext()
        self.secondaryJob = None
        self.loadingClearJob = trinity.CreateRenderJob()
        self.loadingClearJob.name = 'loadingClear'
        self.loadingClearJob.Clear((0, 0, 0, 1))
        self.loadingClearJob.enabled = False
        self.overlaySceneKeys = ['starmap', 'systemmap', 'planet']
        if '/skiprun' not in blue.pyos.GetArg():
            self._EnableLoadingClear()
        limit = settings.public.device.Get('lodQuality', 3) * 30
        self.explosionManager = util.ExplosionManager(limit)
        self.routeVisualizer = None

    def ProcessImportsAndCreateScenes(self):
        from trinity.sceneRenderJobSpace import CreateSceneRenderJobSpace
        from trinity.eveSceneRenderJobInterior import CreateEveSceneRenderJobInterior
        from trinity.sceneRenderJobCharacters import CreateSceneRenderJobCharacters
        self.fisRenderJob = CreateSceneRenderJobSpace('SpaceScenePrimary')
        self.incarnaRenderJob = CreateEveSceneRenderJobInterior()
        self.characterRenderJob = CreateSceneRenderJobCharacters()
        self._CreateJobInterior()
        self._CreateJobCharCreation()
        self._CreateJobFiS()

    def _EnableLoadingClear(self):
        if not self.loadingClearJob.enabled:
            self.loadingClearJob.enabled = True
            trinity.renderJobs.recurring.insert(0, self.loadingClearJob)

    def _DisableLoadingClear(self):
        if self.loadingClearJob.enabled:
            self.loadingClearJob.enabled = False
            trinity.renderJobs.recurring.remove(self.loadingClearJob)

    def EnableIncarnaRendering(self):
        self._DisableLoadingClear()
        if self.secondaryJob is None:
            self.incarnaRenderJob.Enable()

    def RefreshJob(self, camera):
        sceneType = self.primaryJob.sceneType
        if sceneType == SCENE_TYPE_INTERIOR or sceneType == SCENE_TYPE_CHARACTER_CREATION:
            self.primaryJob.renderJob.SetActiveCamera(camera)
            uicore.uilib.SetSceneView(camera.viewMatrix, camera.projectionMatrix)

    def _CreateJobInterior(self):
        rj = self.incarnaRenderJob
        rj.CreateBasicRenderSteps()
        rj.EnableSceneUpdate(True)
        rj.EnableVisibilityQuery(True)

    def _CreateJobCharCreation(self):
        self.characterRenderJob.CreateBasicRenderSteps()
        self.characterRenderJob.EnableShadows(True)
        self.characterRenderJob.EnableScatter(True)
        self.characterRenderJob.EnableSculpting(True)
        self.characterRenderJob.Set2DBackdropScene(self.uiBackdropScene)

    def _CreateJobFiS(self, rj = None):
        if rj is None:
            rj = self.fisRenderJob
        rj.CreateBasicRenderSteps()
        rj.EnablePostProcessing(True)
        rj.EnablePostRenderCallbacks(True)

    def GetFiSPostProcessingJob(self):
        return self.fisRenderJob.postProcessingJob

    def ApplyClothSimulationSettings(self):
        if 'character' not in sm.services:
            return
        if self.primaryJob.sceneType == SCENE_TYPE_INTERIOR:
            clothSimulation = sm.GetService('device').GetAppFeatureState('Interior.clothSimulation', False)
            sm.GetService('character').EnableClothSimulation(clothSimulation)
        elif self.primaryJob.sceneType == SCENE_TYPE_CHARACTER_CREATION:
            clothSimulation = sm.GetService('device').GetAppFeatureState('CharacterCreation.clothSimulation', True)
            sm.GetService('character').EnableClothSimulation(clothSimulation)

    def OnGraphicSettingsChanged(self, changes):
        deviceSvc = sm.GetService('device')
        self.interiorGraphicsQuality = settings.public.device.Get('interiorGraphicsQuality', deviceSvc.GetDefaultInteriorGraphicsQuality())
        self.shadowQuality = settings.public.device.Get('shadowQuality', deviceSvc.GetDefaultShadowQuality())
        self.postProcessingQuality = settings.public.device.Get('postProcessingQuality', deviceSvc.GetDefaultPostProcessingQuality())
        self.antiAliasingQuality = settings.public.device.Get('antiAliasing', 0)
        self.incarnaRenderJob.SetSettingsBasedOnPerformancePreferences()
        self.fisRenderJob.SetSettingsBasedOnPerformancePreferences()
        self.characterRenderJob.SetSettingsBasedOnPerformancePreferences()
        if self.secondaryJob is not None:
            self.secondaryJob.renderJob.SetSettingsBasedOnPerformancePreferences()
        for each in self.registeredJobs:
            each.object.SetSettingsBasedOnPerformancePreferences()

        if 'interiorGraphics' in changes:
            self.ApplyClothSimulationSettings()
        if 'LOD' in changes:
            limit = settings.public.device.Get('lodQuality', 3) * 30
            self.explosionManager.SetLimit(limit)

    def GetIncarnaRenderJob(self):
        return self.incarnaRenderJob

    def GetIncarnaRenderJobVisualizationsMenu(self):
        return self.incarnaRenderJob.GetInsiderVisualizationMenu()

    def SetupIncarnaBackground(self, scene, sceneTranslation, sceneRotation):
        if scene is not None:
            self.incarnaRenderJob.SetBackgroundScene(scene)
            self.backgroundView = trinity.TriView()
            self.backgroundProjection = trinity.TriProjection()
            backGroundCameraUpdateFunction = self.incarnaRenderJob.GetBackgroundCameraUpdateFunction(self.backgroundView, self.backgroundProjection, 10.0, 40000.0, sceneTranslation, sceneRotation)
            self.incarnaRenderJob.SetBackgroundCameraViewAndProjection(self.backgroundView, self.backgroundProjection, backGroundCameraUpdateFunction)

    @telemetry.ZONE_METHOD
    def OnSessionChanged(self, isremote, session, change):
        if 'locationid' in change:
            newLocationID = change['locationid'][1]
            if util.IsSolarSystem(newLocationID) and self.primaryJob.sceneType != SCENE_TYPE_SPACE:
                log.LogWarn('SceneManager: I detected a session change into space but no one has bothered to update my scene type!')
                self.SetSceneType(SCENE_TYPE_SPACE)

    def OnReleaseBallpark(self):
        scene = self.GetRegisteredScene('default')
        if getattr(scene, 'ballpark', None):
            self.SetActiveScene(None, 'default')

    @telemetry.ZONE_METHOD
    def SetSceneType(self, sceneType):
        if self.primaryJob.sceneType == sceneType:
            if sceneType == SCENE_TYPE_INTERIOR:
                self._EnableLoadingClear()
            return
        self.primaryJob = SceneContext(sceneType=sceneType)
        if sceneType == SCENE_TYPE_INTERIOR:
            log.LogInfo('Setting up WiS interior scene rendering')
            self.primaryJob.renderJob = self.incarnaRenderJob
            self.characterRenderJob.Disable()
            self.fisRenderJob.SetActiveScene(None)
            self.fisRenderJob.Disable()
            for each in self.registeredJobs:
                each.object.UseFXAA(True)

            self.ApplyClothSimulationSettings()
            if getattr(self.secondaryJob, 'sceneType', None) == SCENE_TYPE_SPACE:
                self.secondaryJob.renderJob.UseFXAA(True)
            else:
                self._EnableLoadingClear()
        elif sceneType == SCENE_TYPE_CHARACTER_CREATION:
            log.LogInfo('Setting up character creation scene rendering')
            self.primaryJob.renderJob = self.characterRenderJob
            self.incarnaRenderJob.SetScene(None)
            self.incarnaRenderJob.SetBackgroundScene(None)
            self.incarnaRenderJob.Disable()
            self.fisRenderJob.SetActiveScene(None)
            self.fisRenderJob.Disable()
            self.ApplyClothSimulationSettings()
            self._DisableLoadingClear()
            self.characterRenderJob.Enable()
        elif sceneType == SCENE_TYPE_SPACE:
            log.LogInfo('Setting up space scene rendering')
            self.primaryJob.renderJob = self.fisRenderJob
            self.incarnaRenderJob.SetScene(None)
            self.incarnaRenderJob.SetBackgroundScene(None)
            self.incarnaRenderJob.Disable()
            self.characterRenderJob.SetScene(None)
            self.characterRenderJob.Disable()
            self.fisRenderJob.UseFXAA(False)
            for each in self.registeredJobs:
                each.object.UseFXAA(False)

            self._DisableLoadingClear()
            if getattr(self.secondaryJob, 'sceneType', None) == SCENE_TYPE_SPACE:
                self.secondaryJob.renderJob.UseFXAA(False)
            if self.secondaryJob is None:
                self.fisRenderJob.Enable()

    @telemetry.ZONE_METHOD
    def Initialize(self, scene):
        self.uiBackdropScene = trinity.Tr2Sprite2dScene()
        self.uiBackdropScene.isFullscreen = True
        self.uiBackdropScene.backgroundColor = (0, 0, 0, 1)
        self.characterRenderJob.Set2DBackdropScene(self.uiBackdropScene)
        self.primaryJob = SceneContext(scene=scene, renderJob=self.fisRenderJob)

    @telemetry.ZONE_METHOD
    def SetActiveCamera(self, camera):
        if self.secondaryJob is None:
            self.primaryJob.camera = camera
            if self.primaryJob.renderJob is not None:
                self.primaryJob.renderJob.SetActiveCamera(camera)
        else:
            self.secondaryJob.camera = camera
            self.secondaryJob.renderJob.SetActiveCamera(camera)
        uicore.uilib.SetSceneCamera(camera)

    @telemetry.ZONE_METHOD
    def SetSecondaryScene(self, scene, sceneKey, sceneType):
        if sceneType == SCENE_TYPE_SPACE:
            newJob = self.secondaryJob is None
            if newJob:
                from trinity.sceneRenderJobSpace import CreateSceneRenderJobSpace
                self.secondaryJob = SceneContext(scene=scene, sceneKey=sceneKey, sceneType=sceneType)
                self.secondaryJob.renderJob = CreateSceneRenderJobSpace('SpaceSceneSecondary')
                self._CreateJobFiS(self.secondaryJob.renderJob)
            else:
                self.secondaryJob.scene = scene
                self.secondaryJob.sceneKey = sceneKey
            self.secondaryJob.renderJob.SetActiveScene(scene, sceneKey)
            self.secondaryJob.renderJob.UseFXAA(self.primaryJob.sceneType != SCENE_TYPE_SPACE)
            if newJob:
                self.secondaryJob.renderJob.Enable()

    def ClearSecondaryScene(self):
        if self.secondaryJob is None:
            return
        if self.secondaryJob.renderJob is not None:
            self.secondaryJob.renderJob.Disable()
        self.secondaryJob = None

    def SetActiveScene(self, scene, sceneKey = None):
        sceneType = SCENE_TYPE_INTERIOR
        if getattr(scene, '__bluetype__', None) == 'trinity.EveSpaceScene':
            sceneType = SCENE_TYPE_SPACE
        if sceneKey in self.overlaySceneKeys:
            self.primaryJob.renderJob.Pause()
            self.SetSecondaryScene(scene, sceneKey, sceneType)
        elif sceneType == SCENE_TYPE_SPACE:
            self.primaryJob.sceneKey = sceneKey
            self.primaryJob.scene = scene
            self.primaryJob.renderJob.SetActiveScene(scene, sceneKey)
        else:
            self.primaryJob.scene = scene
            self.primaryJob.renderJob.SetScene(scene)

    def Run(self, ms):
        service.Service.Run(self, ms)
        self.registeredScenes = {}
        self.registeredCameras = {}
        self.sceneLoadedEvents = {}
        self.registeredJobs = []
        self.maxFov = 1
        self.minFov = 0.05
        self.interiorGraphicsQuality = settings.public.device.Get('interiorGraphicsQuality', self.device.GetDefaultInteriorGraphicsQuality())
        self.shadowQuality = settings.public.device.Get('shadowQuality', self.device.GetDefaultShadowQuality())
        self.postProcessingQuality = settings.public.device.Get('postProcessingQuality', self.device.GetDefaultPostProcessingQuality())
        self.antiAliasingQuality = settings.public.device.Get('antiAliasing', 0)

    def RegisterJob(self, job):
        wr = blue.BluePythonWeakRef(job)
        if self.primaryJob.sceneType == SCENE_TYPE_INTERIOR:
            job.UseFXAA(True)

        def ClearDereferenced():
            self.registeredJobs.remove(wr)

        wr.callback = ClearDereferenced
        self.registeredJobs.append(wr)

    def GetRegisteredCamera(self, key, defaultOnActiveCamera = 0):
        if key in self.registeredCameras:
            return self.registeredCameras[key]
        if defaultOnActiveCamera:
            if self.secondaryJob is not None:
                return self.secondaryJob.camera
            return self.primaryJob.camera

    def UnregisterCamera(self, key):
        if key in self.registeredCameras:
            del self.registeredCameras[key]

    def RegisterCamera(self, key, camera):
        self.registeredCameras[key] = camera
        self.SetCameraOffset(camera)

    def SetCameraOffset(self, camera):
        camera.centerOffset = settings.user.ui.Get('cameraOffset', 0) * -0.0075

    def CheckCameraOffsets(self):
        for cam in self.registeredCameras.itervalues():
            self.SetCameraOffset(cam)

    def UnregisterScene(self, key):
        if key in self.registeredScenes:
            del self.registeredScenes[key]

    def RegisterScene(self, scene, key):
        self.registeredScenes[key] = scene

    def GetRegisteredScene(self, key, defaultOnActiveScene = 0):
        if key in self.registeredScenes:
            return self.registeredScenes[key]
        if key in self.sceneLoadedEvents and not self.sceneLoadedEvents[key].is_set():
            self.sceneLoadedEvents[key].wait()
            return self.registeredScenes[key]
        if defaultOnActiveScene:
            return self.primaryJob.scene

    def SetRegisteredScenes(self, key):
        if key == 'default' and self.secondaryJob is not None:
            if self.primaryJob.renderJob.enabled:
                self.primaryJob.renderJob.Start()
            else:
                self.primaryJob.renderJob.Enable()
            self.ClearSecondaryScene()
        if self.primaryJob.sceneType != SCENE_TYPE_INTERIOR or key in self.overlaySceneKeys:
            scene = self.registeredScenes.get(key, None)
            camera = self.registeredCameras.get(key, None)
            self.SetActiveScene(scene, key)
            if camera:
                self.SetActiveCamera(camera)

    def GetActiveScene(self):
        if self.secondaryJob is not None:
            return self.secondaryJob.scene
        return self.primaryJob.scene

    def Get2DBackdropScene(self):
        return self.uiBackdropScene

    @telemetry.ZONE_METHOD
    def Show2DBackdropScene(self, updateRenderJob = False):
        self.showUIBackdropScene = True
        if updateRenderJob:
            self.characterRenderJob.Set2DBackdropScene(self.uiBackdropScene)

    @telemetry.ZONE_METHOD
    def Hide2DBackdropScene(self, updateRenderJob = False):
        self.showUIBackdropScene = False
        if updateRenderJob:
            self.characterRenderJob.Set2DBackdropScene(None)

    def GetScene(self, location = None):
        if location is None:
            location = (eve.session.solarsystemid2, eve.session.constellationid, eve.session.regionid)
        resPath = cfg.GetNebula(*location)
        return resPath

    def DeriveTextureFromSceneName(self, scenePath):
        scene = trinity.Load(scenePath)
        if scene is None:
            return ''
        return scene.envMap1ResPath

    def PrepareCamera(self, camera):
        camera.fieldOfView = self.maxFov
        camera.friction = 7.0
        camera.maxSpeed = 0.07
        camera.frontClip = 6.0
        camera.backClip = 10000000.0
        camera.idleScale = 0.65
        for each in camera.zoomCurve.keys:
            each.value = self.maxFov

    def PrepareBackgroundLandscapes(self, scene):
        starSeed = 0
        securityStatus = 1
        if eve.session.stationid is not None:
            return
        if scene is None:
            return
        if bool(eve.session.solarsystemid2):
            starSeed = int(eve.session.constellationid)
            securityStatus = sm.StartService('map').GetSecurityStatus(eve.session.solarsystemid)
        scene.starfield = trinity.Load('res:/dx9/scene/starfield/spritestars.red')
        if scene.starfield is not None:
            scene.starfield.seed = starSeed
            scene.starfield.minDist = 40
            scene.starfield.maxDist = 80
            if util.IsWormholeSystem(eve.session.solarsystemid):
                scene.starfield.numStars = 0
            else:
                scene.starfield.numStars = 500 + int(250 * securityStatus)
        if scene.backgroundEffect is None:
            scene.backgroundEffect = trinity.Load('res:/dx9/scene/starfield/starfieldNebula.red')
            node = nodemanager.FindNode(scene.backgroundEffect.resources, 'NebulaMap', 'trinity.TriTexture2DParameter')
            if node is not None:
                node.resourcePath = scene.envMap1ResPath
        if scene.starfield is None or scene.backgroundEffect is None:
            return
        scene.backgroundRenderingEnabled = True

    @telemetry.ZONE_METHOD
    def LoadScene(self, scenefile, sceneName = '', fov = None, leaveUntouched = 0, inflight = 0, registerKey = None, setupCamera = True):
        try:
            if registerKey:
                self.sceneLoadedEvents[registerKey] = locks.Event(registerKey)
            self.SetSceneType(SCENE_TYPE_SPACE)
            sceneFromFile = trinity.Load(scenefile)
            if sceneFromFile is None:
                return
            scene = sceneFromFile
            bp = sm.GetService('michelle').GetBallpark()
            camera = self.GetRegisteredCamera(registerKey)
            if setupCamera:
                if camera is None:
                    camera = trinity.Load('res:/dx9/scene/camera.red')
            if inflight:
                if scene.dustfield is None:
                    scene.dustfield = trinity.Load('res:/dx9/scene/dustfield.red')
                scene.dustfieldConstraint = scene.dustfield.Find('trinity.EveDustfieldConstraint')[0]
                if scene.dustfieldConstraint is not None:
                    scene.dustfieldConstraint.camera = camera
                scene.ballpark = bp
                scene.sunDiffuseColor = (1.5, 1.5, 1.5, 1.0)
                if settings.user.ui.Get('effectsEnabled', 1) and session.solarsystemid is not None:
                    universe = getattr(self, 'universe', None)
                    if not universe:
                        universe = trinity.Load('res:/dx9/scene/starfield/universe.red')
                        setattr(self, 'universe', universe)
                    scene.backgroundObjects.append(universe)
                    here = sm.GetService('map').GetItem(session.solarsystemid)
                    if here:
                        scale = 10000000000.0
                        position = (here.x / scale, here.y / scale, -here.z / scale)
                        universe.children[0].translation = position
            if leaveUntouched:
                self.SetActiveScene(scene, registerKey)
                return scene
            if camera:
                self.PrepareCamera(camera)
                if fov:
                    camera.fieldOfView = fov
            self.PrepareBackgroundLandscapes(scene)
            if registerKey:
                self.RegisterCamera(registerKey, camera)
                self.RegisterScene(scene, registerKey)
                activeScene = self.GetActiveScene()
                if activeScene is None or activeScene not in self.registeredScenes.values():
                    self.SetActiveScene(scene, registerKey)
                    if camera:
                        self.SetActiveCamera(camera)
            else:
                self.SetActiveScene(scene, registerKey)
                if camera:
                    self.SetActiveCamera(camera)
            if camera:
                camera.audio2Listener = audio2.GetListener(0)
            if camera and bp is not None:
                myShipBall = bp.GetBallById(bp.ego)
                vel = geo2.Vector(myShipBall.vx, myShipBall.vy, myShipBall.vz)
                if geo2.Vec3Length(vel) > 0.0:
                    vel = geo2.Vec3Normalize(vel)
                    pitch = asin(-vel[1])
                    yaw = atan2(vel[0], vel[2])
                    yaw = yaw - 0.3
                    pitch = pitch - 0.15
                    camera.SetOrbit(yaw, pitch)
            if inflight and settings.user.ui.Get('routeVisualizationEnabled', True):
                if self.routeVisualizer:
                    self.routeVisualizer.Cleanup()
                self.routeVisualizer = RouteVisualizer()
            sm.ScatterEvent('OnLoadScene')
        except Exception:
            log.LogException('sceneManager::LoadScene')
            sys.exc_clear()
        finally:
            if registerKey and registerKey in self.sceneLoadedEvents:
                self.sceneLoadedEvents.pop(registerKey).set()

    def ToggleRouteVisualization(self):
        enabled = not settings.user.ui.Get('routeVisualizationEnabled', True)
        settings.user.ui.Set('routeVisualizationEnabled', enabled)
        if enabled:
            if self.routeVisualizer:
                self.routeVisualizer.Update()
            else:
                self.routeVisualizer = RouteVisualizer()
        elif self.routeVisualizer:
            self.routeVisualizer.Cleanup()
            self.routeVisualizer = None


class RouteVisualizer():
    __guid__ = 'util.RouteVisualizer'
    __notifyevents__ = ['OnDestinationSet']

    def __init__(self):
        sm.RegisterNotify(self)
        self.route = None
        self.CreateLineSet()

    def OnDestinationSet(self, destination):
        self.Update()

    def Update(self):
        self.Cleanup()
        self.CreateLineSet()

    def GetScene(self):
        return sm.GetService('sceneManager').GetRegisteredScene('default')

    def Cleanup(self):
        if self.route:
            scene = self.GetScene()
            if scene and hasattr(scene, 'backgroundObjects'):
                scene.backgroundObjects.fremove(self.route)

    def CreateLineSet(self):
        scene = self.GetScene()
        if not hasattr(scene, 'backgroundObjects'):
            return
        if not scene:
            log.LogWarn('RouteVisualizer - No scene')
            return
        waypoints = sm.GetService('starmap').GetDestinationPath()
        if None in waypoints:
            return
        lineSet = trinity.EveCurveLineSet()
        lineSet.scaling = (1.0, 1.0, 1.0)
        tex2D1 = trinity.TriTexture2DParameter()
        tex2D1.name = 'TexMap'
        tex2D1.resourcePath = 'res:/texture/global/lineSolid.dds'
        lineSet.lineEffect.resources.append(tex2D1)
        tex2D2 = trinity.TriTexture2DParameter()
        tex2D2.name = 'OverlayTexMap'
        tex2D2.resourcePath = 'res:/UI/Texture/Planet/link.dds'
        lineSet.lineEffect.resources.append(tex2D2)
        topTransform = trinity.EveTransform()
        topTransform.name = 'Route'
        topTransform.modifier = 2
        transform = trinity.EveTransform()
        topTransform.children.append(transform)
        transform.name = 'AutoPilotRoute'
        transform.children.append(lineSet)
        scene.backgroundObjects.append(topTransform)
        waypointDisplayCount = 15
        here = sm.StartService('map').GetItem(session.solarsystemid)
        if not here:
            log.LogWarn('RouteVisualizer - No _here_')
            return
        itemInfo = []
        for sid in waypoints:
            if not util.IsSolarSystem(sid):
                continue
            item = sm.StartService('map').GetItem(sid)
            position = (-item.x + here.x, -item.y + here.y, item.z - here.z)
            position = geo2.Vec3Normalize(position)
            position = geo2.Vec3Scale(position, 1000)
            security = item.security
            itemInfo.append((position, security))

        waypointDisplayCount = 15
        itemInfo = itemInfo[0:min(waypointDisplayCount, len(itemInfo))]
        securityColors = sm.GetService('map').GetSecColorList()
        baseAlpha = 0.25
        for i, each in enumerate(itemInfo):
            length = len(itemInfo)
            if i < length - 1:
                colorIndex1 = int(round(max(itemInfo[i][1], 0), 1) * 10)
                color1 = securityColors[colorIndex1]
                alpha1 = 1 - float(i) / len(itemInfo)
                alpha1 *= baseAlpha
                lineColor1 = (color1.r,
                 color1.g,
                 color1.b,
                 alpha1)
                colorIndex2 = int(round(max(itemInfo[i + 1][1], 0), 1) * 10)
                color2 = securityColors[colorIndex2]
                alpha2 = 1 - float(i + 1) / len(itemInfo)
                alpha2 *= baseAlpha
                lineColor2 = (color2.r,
                 color2.g,
                 color2.b,
                 alpha2)
                lineWidth = 3
                l1 = lineSet.AddStraightLine(itemInfo[i][0], lineColor1, itemInfo[i + 1][0], lineColor2, lineWidth)
                animationColor = (0.12, 0.12, 0.12, 0.6)
                lineSet.ChangeLineAnimation(l1, animationColor, -0.35, 1)

        lineSet.SubmitChanges()
        self.route = topTransform


exports = {'sceneManager.SCENE_TYPE_SPACE': SCENE_TYPE_SPACE,
 'sceneManager.SCENE_TYPE_CHARACTER_CREATION': SCENE_TYPE_CHARACTER_CREATION,
 'sceneManager.SCENE_TYPE_INTERIOR': SCENE_TYPE_INTERIOR}