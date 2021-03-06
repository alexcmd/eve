#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/control/scenecontainer.py
import sys
import blue
import uthread
import uiutil
import xtriui
import form
import trinity
import util
import base
import math
import log
import triui
import lg
import destiny
import dbg
import bluepy
import uicls
import uiconst
import bitmapjob
import paperDoll
import geo2

class SceneContainer(uicls.Base):
    __guid__ = 'form.SceneContainer'
    __renderObject__ = trinity.Tr2Sprite2dRenderJob

    def ApplyAttributes(self, attributes):
        self.viewport = trinity.TriViewport()
        self.viewport.x = 0
        self.viewport.y = 0
        self.viewport.width = 1
        self.viewport.height = 1
        self.viewport.minZ = 0.0
        self.viewport.maxZ = 1.0
        self.projection = trinity.TriProjection()
        self.renderJob = None
        self.frontClip = 1.0
        self.backClip = 350000.0
        self.fieldOfView = 1.0
        self.minPitch = -1.4
        self.maxPitch = 1.4
        self.offscreen = False
        uicls.Base.ApplyAttributes(self, attributes)

    def Startup(self, *args):
        self.PrepareCamera()
        self.scene = None
        self.DisplayScene()

    def PrepareSpaceScene(self, maxPitch = 1.4, scenePath = None, offscreen = False):
        self.offscreen = offscreen
        if scenePath is None:
            scenePath = 'res:/dx9/scene/fitting/fitting.red'
        self.scene = trinity.Load(scenePath)
        self.scene.renderGPUParticles = False
        self.frontClip = 1.0
        self.backClip = 350000.0
        self.fieldOfView = 1.0
        self.minPitch = -1.4
        self.maxPitch = maxPitch
        self.SetupCamera()
        if blue.win32.IsTransgaming():
            self.DisplayScene()
        else:
            self.DisplaySpaceScene()

    def PrepareInteriorScene(self, addShadowStep = False, backgroundImage = None):
        self.scene = trinity.Load('res:/Graphics/Interior/characterCreation/Preview.red')
        self.frontClip = 0.1
        self.backClip = 10.0
        self.fieldOfView = 0.3
        self.minPitch = -0.6
        self.maxPitch = 0.6
        self.SetupCamera()
        blue.resMan.Wait()
        self.DisplayScene(addClearStep=True, addBitmapStep=True, addShadowStep=addShadowStep, backgroundImage=backgroundImage)

    def SetupCamera(self):
        self.camera.frontClip = self.frontClip
        self.camera.backClip = self.backClip
        self.camera.fieldOfView = self.fieldOfView
        self.camera.minPitch = self.minPitch
        self.camera.maxPitch = self.maxPitch

    def PrepareCamera(self):
        self.camera = trinity.EveCamera()
        self.cameraParent = self.camera.parent = trinity.EveSO2ModelCenterPos()

    def DisplaySpaceScene(self):
        from trinity.sceneRenderJobSpaceEmbedded import CreateEmbeddedRenderJobSpace
        self.renderJob = CreateEmbeddedRenderJobSpace()
        rj = self.renderJob
        rj.CreateBasicRenderSteps()
        rj.SetActiveCamera(self.camera)
        rj.SetCameraProjection(self.projection)
        rj.SetScene(self.scene)
        rj.SetViewport(self.viewport)
        if self.offscreen:
            rj.SetOffscreen(self.offscreen)
        rj.UpdateViewport(self.viewport)
        sm.GetService('sceneManager').RegisterJob(rj)
        try:
            rj.DoPrepareResources()
        except trinity.D3DError:
            pass

        rj.Enable(False)
        rj.SetSettingsBasedOnPerformancePreferences()
        self.renderObject.renderJob = self.renderJob

    def DisplayScene(self, addClearStep = False, addBitmapStep = False, addShadowStep = False, backgroundImage = None):
        self.renderJob = trinity.CreateRenderJob('SceneInScene')
        self.renderJob.SetViewport(self.viewport)
        self.projection.PerspectiveFov(self.fieldOfView, self.viewport.GetAspectRatio(), self.frontClip, self.backClip)
        self.renderJob.SetProjection(self.projection)
        self.renderJob.SetView(None, self.camera, None)
        self.renderJob.Update(self.scene)
        if addShadowStep:
            paperDoll.SkinSpotLightShadows.CreateShadowStep(self.renderJob)
        if addClearStep:
            self.renderJob.Clear((0.2, 0.2, 0.2, 1.0), 1.0)
        if addBitmapStep:
            if backgroundImage is None:
                backgroundImage = 'res:/UI/Texture/preview/asset_preview_background.png'
            step = bitmapjob.makeBitmapStep(backgroundImage, scaleToFit=False, color=(1.0, 1.0, 1.0, 1.0))
            self.renderJob.steps.append(step)
        self.renderJob.RenderScene(self.scene)
        self.renderObject.renderJob = self.renderJob

    def SetStencilMap(self, path = 'res:/UI/Texture/circleStencil.dds'):
        if hasattr(self.renderJob, 'SetStencil'):
            self.renderJob.SetStencil(path)
        stencilMap = trinity.TriTexture2DParameter()
        stencilMap.name = 'StencilMap'
        stencilMap.resourcePath = path
        self.scene.backgroundEffect.resources.append(stencilMap)
        self.scene.backgroundEffect.effectFilePath = 'res:/Graphics/Effect/Managed/Space/SpecialFX/NebulaWithStencil.fx'

    def AddToScene(self, model, clear = 1):
        if model == None or self.scene == None:
            return
        if clear:
            del self.scene.objects[:]
        self.scene.objects.append(model)
        self.scene.UpdateScene(blue.os.GetSimTime())
        self.cameraParent.parent = model
        self.camera.rotationOfInterest = geo2.QuaternionIdentity()

    def ClearScene(self):
        self.scene.UpdateScene(blue.os.GetSimTime())
        del self.scene.objects[:]

    def _OnResize(self):
        self.UpdateViewPort()

    def UpdateViewPort(self, *args):
        l, t, w, h = self.GetAbsoluteViewport()
        if not w and not h:
            return
        self.viewport.x = uicore.ScaleDpi(l)
        self.viewport.y = uicore.ScaleDpi(t)
        self.viewport.width = uicore.ScaleDpi(w)
        self.viewport.height = uicore.ScaleDpi(h)
        self.projection.PerspectiveFov(self.fieldOfView, self.viewport.GetAspectRatio(), self.frontClip, self.backClip)
        if hasattr(self.renderJob, 'UpdateViewport'):
            self.renderJob.UpdateViewport(self.viewport)

    def OnResize_(self, k, v):
        self.UpdateViewPort()

    def _OnClose(self, *args):
        self.clearStep = None
        self.viewport = None
        self.projection = None
        self.camera = None
        self.cameraParent = None
        self.scene = None
        if hasattr(self.renderJob, 'Disable'):
            self.renderJob.Disable()
        self.renderJob = None


class SceneWindowTest(uicls.Window):
    __guid__ = 'form.SceneWindowTest'

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        sc = form.SceneContainer(uicls.Frame(parent=self.sr.main, padding=(6, 6, 6, 6)))
        sc.Startup()
        nav = SceneContainerBaseNavigation(uicls.Container(parent=self.sr.main, left=6, top=6, width=6, height=6, idx=0, state=uiconst.UI_NORMAL))
        nav.Startup(sc)
        self.sr.navigation = nav
        self.sr.sceneContainer = sc

    def OnResizeUpdate(self, *args):
        self.sr.sceneContainer.UpdateViewPort()


class SceneContainerBaseNavigation(uicls.Container):
    __guid__ = 'form.SceneContainerBaseNavigation'

    def init(self):
        self.sr.cookie = None
        self.isTabStop = 1

    def Startup(self, sceneContainer):
        self.sr.sceneContainer = sceneContainer
        self.minZoom = 10.0
        self.maxZoom = 3000.0
        self.sr.cookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_MOUSEUP, self._OnGlobalMouseUp)

    def _OnClose(self, *args):
        if self.sr.cookie:
            uicore.event.UnregisterForTriuiEvents(self.sr.cookie)
            self.sr.cookie = None

    def SetMinMaxZoom(self, minZoom, maxZoom):
        self.minZoom = minZoom
        self.maxZoom = maxZoom
        self.CheckCameraTranslation()

    def CheckCameraTranslation(self):
        self.sr.sceneContainer.camera.translationFromParent = min(self.maxZoom, max(self.minZoom, self.sr.sceneContainer.camera.translationFromParent))

    def OnMouseWheel(self, *args):
        self.sr.sceneContainer.camera.Dolly(uicore.uilib.dz * 0.001 * abs(self.sr.sceneContainer.camera.translationFromParent))
        self.CheckCameraTranslation()

    def OnMouseMove(self, *args):
        if self.destroyed or uicore.IsDragging():
            return
        lib = uicore.uilib
        dx = lib.dx
        dy = lib.dy
        fov = self.sr.sceneContainer.camera.fieldOfView
        cameraSpeed = 3.0
        ctrl = lib.Key(uiconst.VK_CONTROL)
        if lib.leftbtn and not lib.rightbtn:
            self.sr.sceneContainer.camera.OrbitParent(-dx * fov * 0.2 * cameraSpeed, dy * fov * 0.2 * cameraSpeed)
        if lib.leftbtn and lib.rightbtn:
            self.sr.sceneContainer.camera.Dolly(-(dy * 0.01) * abs(self.sr.sceneContainer.camera.translationFromParent))
            self.CheckCameraTranslation()
            if ctrl:
                self.sr.sceneContainer.camera.fieldOfView = -dx * 0.01 + fov
                if self.sr.sceneContainer.camera.fieldOfView > 1.0:
                    self.sr.sceneContainer.camera.fieldOfView = 1.0
                if self.sr.sceneContainer.camera.fieldOfView < 0.1:
                    self.sr.sceneContainer.camera.fieldOfView = 0.1
            else:
                self.sr.sceneContainer.camera.OrbitParent(-dx * fov * 0.2 * cameraSpeed, 0.0)

    def _OnGlobalMouseUp(self, wnd, msgID, btn, *args):
        if btn and btn[0] == 1:
            self.sr.sceneContainer.camera.rotationOfInterest = geo2.QuaternionIdentity()
        return 1


class SceneContainerBrackets(uicls.Base):
    __guid__ = 'form.SceneContainerBrackets'
    __renderObject__ = trinity.Tr2Sprite2dRenderJob

    def ApplyAttributes(self, attributes):
        uicls.Base.ApplyAttributes(self, attributes)
        self.viewport = trinity.TriViewport()
        self.viewport.x = 0
        self.viewport.y = 0
        self.viewport.width = 1
        self.viewport.height = 1
        self.viewport.minZ = 0.0
        self.viewport.maxZ = 1.0
        self.projection = trinity.TriProjection()
        self.frontClip = 1.0
        self.backClip = 350000.0
        self.fieldOfView = 1.0
        self.minPitch = -3.0
        self.maxPitch = 3.4
        self.scene = trinity.EveSpaceScene()
        self.scene.renderGPUParticles = False
        self.transform = trinity.EveRootTransform()
        self.scene.objects.append(self.transform)
        self.PrepareCamera()
        self.DisplayScene()
        self.CreateBracketCurveSet()
        self.UpdateViewPort()

    def PrepareCamera(self):
        self.cameraParent = trinity.EveSO2ModelCenterPos()
        self.camera = trinity.EveCamera()
        self.camera.parent = self.cameraParent
        self.camera.frontClip = self.frontClip
        self.camera.backClip = self.backClip
        self.camera.fieldOfView = self.fieldOfView
        self.camera.minPitch = self.minPitch
        self.camera.maxPitch = self.maxPitch

    def GetTranslationsForSolarsystemIDs(self, solarSystemIDs):
        xAv = yAv = zAv = 0
        scale = 1e+16
        for solarsystemID in solarSystemIDs:
            systemObj = cfg.solarsystems.Get(solarsystemID)
            xAv += systemObj.x
            yAv += systemObj.y
            zAv += systemObj.z

        numSystems = len(solarSystemIDs)
        xAv = xAv / numSystems
        yAv = yAv / numSystems
        zAv = zAv / numSystems
        translations = []
        for solarsystemID in solarSystemIDs:
            systemObj = cfg.solarsystems.Get(solarsystemID)
            translations.append(((systemObj.x - xAv) / scale, (systemObj.y - yAv) / scale, (systemObj.z - zAv) / scale))

        return translations

    def CreateBracketTransform(self, translation):
        tr = trinity.EveTransform()
        tr.translation = translation
        self.transform.children.append(tr)
        return tr

    def AnimRotateFrom(self, yaw, pitch, zoom, duration):
        sequencer = trinity.TriYPRSequencer()
        self.transform.rotationCurve = sequencer
        start = blue.os.GetSimTime()
        sequencer.YawCurve = yawCurve = trinity.TriScalarCurve()
        yawCurve.start = start
        yawCurve.extrapolation = trinity.TRIEXT_CONSTANT
        yawCurve.AddKey(0.0, yaw, 0, 0, trinity.TRIINT_HERMITE)
        yawCurve.AddKey(duration, 0.0, 0, 0, trinity.TRIINT_HERMITE)
        sequencer.PitchCurve = pitchCurve = trinity.TriScalarCurve()
        pitchCurve.start = start
        pitchCurve.extrapolation = trinity.TRIEXT_CONSTANT
        pitchCurve.AddKey(0.0, pitch, 0, 0, trinity.TRIINT_HERMITE)
        pitchCurve.AddKey(duration, 0.0, 0, 0, trinity.TRIINT_HERMITE)

    def DisplayScene(self):
        self.renderJob = trinity.CreateRenderJob()
        self.renderJob.SetViewport(self.viewport)
        self.renderJob.SetView(None, self.camera, None)
        self.renderJob.SetProjection(self.projection)
        self.renderJob.Update(self.scene)
        self.renderJob.RenderScene(self.scene)
        self.renderObject.renderJob = self.renderJob

    def CreateBracketCurveSet(self):
        self.bracketCurveSet = trinity.TriCurveSet()
        self.bracketCurveSet.Play()
        step = trinity.TriStepUpdate()
        step.object = self.bracketCurveSet
        step.name = 'Update brackets'
        self.renderJob.steps.append(step)

    def _OnResize(self):
        self.UpdateViewPort()

    def UpdateViewPort(self, *args):
        l, t, w, h = self.GetAbsoluteViewport()
        log.LogInfo('SceneContainerBrackets::UpdateViewPort', l, t, w, h)
        if not w and not h:
            return
        self.viewport.width = uicore.ScaleDpi(w)
        self.viewport.height = uicore.ScaleDpi(h)
        log.LogInfo('new viewport dimensions', self.viewport.x, self.viewport.y, self.viewport.width, self.viewport.height)
        log.LogInfo('projection', self.fieldOfView, self.viewport.GetAspectRatio(), self.frontClip, self.backClip)
        self.projection.PerspectiveFov(self.fieldOfView, self.viewport.GetAspectRatio(), self.frontClip, self.backClip)

    def _OnClose(self, *args):
        self.clearStep = None
        self.viewport = None
        self.projection = None
        self.camera = None
        self.cameraParent = None
        self.scene = None
        if hasattr(self.renderJob, 'Disable'):
            self.renderJob.Disable()
        self.renderJob = None