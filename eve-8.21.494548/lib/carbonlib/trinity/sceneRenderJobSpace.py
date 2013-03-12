#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\trinity\sceneRenderJobSpace.py
from trinity.sceneRenderJobBase import SceneRenderJobBase
from trinity.renderJobUtils import ConvertDepthFormatToALFormat, renderTargetManager as rtm
import trinity.evePostProcess
import trinity
import blue
import localization
import log

def CreateSceneRenderJobSpace(name = None, stageKey = None):
    newRJ = SceneRenderJobSpace()
    if name is not None:
        newRJ.ManualInit(name)
    else:
        newRJ.ManualInit()
    newRJ.SetMultiViewStage(stageKey)
    return newRJ


class SceneRenderJobSpace(SceneRenderJobBase):
    renderStepOrder = ['PRESENT_SWAPCHAIN',
     'SET_SWAPCHAIN_RT',
     'SET_SWAPCHAIN_DEPTH',
     'UPDATE_SCENE',
     'SET_CUSTOM_RT',
     'SET_DEPTH',
     'SET_VAR_DEPTH',
     'SET_VIEWPORT',
     'SET_PROJECTION',
     'SET_VIEW',
     'CLEAR',
     'BEGIN_RENDER',
     'RENDER_BACKGROUND',
     'RENDER_DEPTH_PASS',
     'RENDER_MAIN_PASS',
     'DO_DISTORTIONS',
     'END_RENDERING',
     'UPDATE_TOOLS',
     'RENDER_PROXY',
     'RENDER_INFO',
     'RENDER_VISUAL',
     'RENDER_TOOLS',
     'SET_FINAL_RT',
     'RESTORE_DEPTH',
     'RJ_POSTPROCESSING',
     'FINAL_BLIT',
     'SET_VAR_GATHER',
     'FXAA_CLEAR',
     'FXAA',
     'POST_RENDER_CALLBACK',
     'FPS_COUNTER']
    multiViewStages = []
    visualizations = []
    renderTargetList = []

    def _ManualInit(self, name = 'SceneRenderJobSpace'):
        self.scene = None
        self.clientToolsScene = None
        self.activeSceneKey = None
        self.camera = None
        self.customBackBuffer = None
        self.customDepthStencil = None
        self.depthTexture = None
        self.blitTexture = None
        self.distortionTexture = None
        self.shadowMap = None
        self.ui = None
        self.hdrEnabled = False
        self.usePostProcessing = False
        self.shadowQuality = 0
        self.useDepth = False
        self.antiAliasingEnabled = False
        self.antiAliasingQuality = 0
        self.aaQuality = 0
        self.useFXAA = False
        self.fxaaEnabled = False
        self.fxaaQuality = 'FXAA_High'
        self.msaaEnabled = False
        self.doDepthPass = False
        self.forceDepthPass = False
        self.msaaType = 4
        self.distortionEffectsEnabled = False
        self.fxaaEffect = None
        self.bbFormat = trinity.renderContext.GetBackBufferFormat()
        self.prepared = False
        self.postProcessingJob = trinity.evePostProcess.EvePostProcessingJob()
        self.distortionJob = trinity.evePostProcess.EvePostProcessingJob()
        self.backgroundDistortionJob = trinity.evePostProcess.EvePostProcessingJob()
        self.overrideSettings = {}
        self.SetSettingsBasedOnPerformancePreferences()

    def Enable(self, schedule = True):
        SceneRenderJobBase.Enable(self, schedule)
        self.SetSettingsBasedOnPerformancePreferences()

    def SetClientToolsScene(self, scene):
        if scene is None:
            self.clientToolsScene = None
        else:
            self.clientToolsScene = blue.BluePythonWeakRef(scene)
        self.AddStep('UPDATE_TOOLS', trinity.TriStepUpdate(scene))
        self.AddStep('RENDER_TOOLS', trinity.TriStepRenderScene(scene))

    def GetClientToolsScene(self):
        if self.clientToolsScene is None:
            return
        else:
            return self.clientToolsScene.object

    def SetActiveCamera(self, camera = None, view = None, projection = None):
        if camera is None and view is None and projection is None:
            self.RemoveStep('SET_VIEW')
            self.RemoveStep('SET_PROJECTION')
            return
        if camera is not None:
            self.AddStep('SET_VIEW', trinity.TriStepSetView(None, camera))
            self.AddStep('SET_PROJECTION', trinity.TriStepSetProjection(camera.projectionMatrix))
        if view is not None:
            self.AddStep('SET_VIEW', trinity.TriStepSetView(view))
        if projection is not None:
            self.AddStep('SET_PROJECTION', trinity.TriStepSetProjection(projection))

    def SetActiveScene(self, scene, key = None):
        self.activeSceneKey = key
        self.SetScene(scene)
        self.postProcessingJob.SetActiveKey(key)

    def _SetDepthMap(self):
        if not self.enabled:
            return
        if self.GetScene() is None:
            return
        if hasattr(self.GetScene(), 'depthTexture'):
            if self.doDepthPass:
                self.GetScene().depthTexture = self.depthTexture
            else:
                self.GetScene().depthTexture = None

    def _SetDistortionMap(self):
        if not self.enabled:
            return
        if self.GetScene() is None:
            return
        if hasattr(self.GetScene(), 'distortionTexture'):
            self.GetScene().distortionTexture = self.distortionTexture

    def _SetShadowMap(self):
        scene = self.GetScene()
        if scene is None:
            return
        if self.shadowQuality > 1:
            scene.shadowMap = self.shadowMap
            scene.shadowFadeThreshold = 180
            scene.shadowThreshold = 80
        elif self.shadowQuality > 0:
            scene.shadowMap = self.shadowMap
            scene.shadowFadeThreshold = 200
            scene.shadowThreshold = 120
        else:
            scene.shadowMap = None

    def ForceDepthPass(self, enabled):
        self.forceDepthPass = enabled

    def EnablePostProcessing(self, enabled):
        if enabled:
            self.AddStep('RJ_POSTPROCESSING', trinity.TriStepRunJob(self.postProcessingJob))
        else:
            self.RemoveStep('RJ_POSTPROCESSING')

    def EnablePostRenderCallbacks(self, enabled):
        if enabled:
            self.AddStep('POST_RENDER_CALLBACK', trinity.TriStepPostRenderCB())
        else:
            self.RemoveStep('POST_RENDER_CALLBACK')

    def _RefreshPostProcessingJob(self, job, enabled):
        if enabled:
            job.Prepare(self._GetSourceRTForPostProcessing(), self.blitTexture, destination=self._GetDestinationRTForPostProcessing())
            job.CreateSteps()
        else:
            job.Release()

    def _GetSourceRTForPostProcessing(self):
        if self.customBackBuffer is not None:
            return self.customBackBuffer
        return self.GetBackBufferRenderTarget()

    def _GetDestinationRTForPostProcessing(self):
        if self.useFXAA and self.antiAliasingEnabled:
            return self.customBackBuffer

    def _DoFormatConversionStep(self, hdrTexture, msaaTexture = None):
        job = trinity.CreateRenderJob()
        job.name = 'DoFormatConversion'
        if msaaTexture is not None:
            if hdrTexture is not None:
                job.steps.append(trinity.TriStepResolve(hdrTexture, msaaTexture))
            else:
                job.steps.append(trinity.TriStepResolve(self.GetBackBufferRenderTarget(), msaaTexture))
                return trinity.TriStepRunJob(job)
        job.steps.append(trinity.TriStepSetStdRndStates(trinity.RM_FULLSCREEN))
        job.steps.append(trinity.TriStepRenderTexture(hdrTexture))
        return trinity.TriStepRunJob(job)

    def _GetRTForDepthPass(self):
        return self.GetBackBufferRenderTarget()

    def _CreateDepthPass(self):
        rj = trinity.TriRenderJob()
        if self.enabled and self.doDepthPass and self.depthTexture is not None:
            rj.steps.append(trinity.TriStepPushViewport())
            rj.steps.append(trinity.TriStepPushRenderTarget(self._GetRTForDepthPass()))
            rj.steps.append(trinity.TriStepPushDepthStencil(self.depthTexture))
            rj.steps.append(trinity.TriStepPopViewport())
            rj.steps.append(trinity.TriStepPushViewport())
            rj.steps.append(trinity.TriStepRenderPass(self.GetScene(), trinity.TRIPASS_DEPTH_PASS))
            rj.steps.append(trinity.TriStepPopDepthStencil())
            rj.steps.append(trinity.TriStepPopRenderTarget())
            rj.steps.append(trinity.TriStepPopViewport())
        self.AddStep('RENDER_DEPTH_PASS', trinity.TriStepRunJob(rj))

    def _CreateBackgroundStep(self, scene = None):
        if scene is None:
            scene = self.GetScene()
        job = trinity.CreateRenderJob()
        job.steps.append(trinity.TriStepRenderPass(scene, trinity.TRIPASS_BACKGROUND_RENDER))
        job.steps.append(trinity.TriStepRunJob(self.backgroundDistortionJob))
        self.AddStep('RENDER_BACKGROUND', trinity.TriStepRunJob(job))

    def _SetBackgroundScene(self, scene):
        backgroundJob = self.GetStep('RENDER_BACKGROUND')
        if backgroundJob is not None:
            backgroundJob.job.steps[0].scene = scene

    def _SetScene(self, scene):
        self.currentMultiViewStageKey
        self.SetStepAttr('UPDATE_SCENE', 'object', scene)
        self.SetStepAttr('RENDER_MAIN_PASS', 'scene', scene)
        self.SetStepAttr('BEGIN_RENDER', 'scene', scene)
        self.SetStepAttr('END_RENDERING', 'scene', scene)
        self.SetStepAttr('RENDER_MAIN_PASS', 'scene', scene)
        self._CreateDepthPass()
        self._SetBackgroundScene(scene)
        self.ApplyPerformancePreferencesToScene()

    def _CreateBasicRenderSteps(self):
        self.AddStep('UPDATE_SCENE', trinity.TriStepUpdate(self.GetScene()))
        self.AddStep('BEGIN_RENDER', trinity.TriStepRenderPass(self.GetScene(), trinity.TRIPASS_BEGIN_RENDER))
        self.AddStep('END_RENDERING', trinity.TriStepRenderPass(self.GetScene(), trinity.TRIPASS_END_RENDER))
        self.AddStep('RENDER_MAIN_PASS', trinity.TriStepRenderPass(self.GetScene(), trinity.TRIPASS_MAIN_RENDER))
        self._CreateDepthPass()
        self._CreateBackgroundStep()
        self.AddStep('CLEAR', trinity.TriStepClear((0.0, 0.0, 0.0, 0.0), 1.0))
        if self.clientToolsScene is not None:
            self.SetClientToolsScene(self.clientToolsScene.object)

    def DoReleaseResources(self, level):
        self.prepared = False
        self.hdrEnabled = False
        self.usePostProcessing = False
        self.shadowQuality = 0
        self.shadowMap = None
        self.depthTexture = None
        self.renderTargetList = None
        self.customBackBuffer = None
        self.customDepthStencil = None
        self.depthTexture = None
        self.blitTexture = None
        self.distortionTexture = None
        self.postProcessingJob.Release()
        self.distortionJob.Release()
        self.backgroundDistortionJob.Release()
        self.distortionJob.SetPostProcessVariable('Distortion', 'TexDistortion', None)
        self.backgroundDistortionJob.SetPostProcessVariable('Distortion', 'TexDistortion', None)
        self._SetDistortionMap()
        self._RefreshRenderTargets()

    def NotifyResourceCreationFailed(self):
        try:
            eve.Message('CustomError', {'error': localization.GetByLabel('UI/Shared/VideoMemoryError')})
        finally:
            pass

    def _GetSettings(self):
        currentSettings = {}
        if sm.IsServiceRunning('device'):
            deviceSvc = sm.GetService('device')
            currentSettings['hdrEnabled'] = bool(settings.public.device.Get('hdrEnabled', deviceSvc.GetDefaultHDRState()))
            defaultPostProcessingQuality = deviceSvc.GetDefaultPostProcessingQuality()
            defaultShadowQuality = deviceSvc.GetDefaultShadowQuality()
        else:
            currentSettings['hdrEnabled'] = trinity.device.hdrEnable
            defaultPostProcessingQuality = 2
            defaultShadowQuality = 2
        currentSettings['postProcessingQuality'] = settings.public.device.Get('postProcessingQuality', defaultPostProcessingQuality)
        currentSettings['shadowQuality'] = settings.public.device.Get('shadowQuality', defaultShadowQuality)
        currentSettings['aaQuality'] = settings.public.device.Get('antiAliasing', 0)
        return currentSettings

    def ApplyBaseSettings(self):
        currentSettings = self._GetSettings()
        self.bbFormat = trinity.renderContext.GetBackBufferFormat()
        self.postProcessingQuality = currentSettings['postProcessingQuality']
        self.shadowQuality = currentSettings['shadowQuality']
        self.aaQuality = currentSettings['aaQuality']
        self.hdrEnabled = currentSettings['hdrEnabled']
        self.distortionEffectsEnabled = self.useDepth = trinity.GetShaderModel().endswith('DEPTH')
        if 'hdrEnabled' in self.overrideSettings:
            self.hdrEnabled = self.overrideSettings['hdrEnabled']
        if 'bbFormat' in self.overrideSettings:
            self.bbFormat = self.overrideSettings['bbFormat']
        if 'aaQuality' in self.overrideSettings:
            self.aaQuality = self.overrideSettings['aaQuality']

    def OverrideSettings(self, key, value):
        self.overrideSettings[key] = value

    def _CreateRenderTargets(self):
        if not self.prepared:
            return
        width, height = self.GetBackBufferSize()
        dsFormatAL = trinity.device.depthStencilFormat
        useCustomBackBuffer = self.hdrEnabled or self.msaaEnabled or self.fxaaEnabled
        customFormat = trinity.PIXEL_FORMAT.R16G16B16A16_FLOAT if self.hdrEnabled else self.bbFormat
        msaaType = self.msaaType if self.msaaEnabled else 1
        if useCustomBackBuffer and self._TargetDiffers(self.customBackBuffer, 'trinity.Tr2RenderTarget', customFormat, msaaType, width, height):
            if self.msaaEnabled:
                self.customBackBuffer = rtm.GetRenderTargetMsaaAL(width, height, customFormat, msaaType, 0)
            else:
                self.customBackBuffer = rtm.GetRenderTargetAL(width, height, 1, customFormat)
            if self.customBackBuffer is not None:
                self.customBackBuffer.name = 'sceneRenderJobSpace.customBackBuffer'
        elif not useCustomBackBuffer:
            self.customBackBuffer = None
        if self.msaaEnabled and self._TargetDiffers(self.customDepthStencil, 'trinity.Tr2DepthStencil', dsFormatAL, msaaType, width, height):
            self.customDepthStencil = rtm.GetDepthStencilAL(width, height, dsFormatAL, msaaType)
        elif not self.msaaEnabled:
            self.customDepthStencil = None
        if self.useDepth and self._TargetDiffers(self.depthTexture, 'trinity.Tr2DepthStencil', trinity.DEPTH_STENCIL_FORMAT.READABLE, 0, width, height):
            self.depthTexture = rtm.GetDepthStencilAL(width, height, trinity.DEPTH_STENCIL_FORMAT.READABLE)
            if self.depthTexture is not None and self.depthTexture.IsReadable():
                self.depthTexture.name = 'sceneRenderJobSpace.depthTexture'
            else:
                self.depthTexture = None
        elif not self.useDepth:
            self.depthTexture = None
        useBlitTexture = self.usePostProcessing or self.distortionEffectsEnabled
        useBlitTexture = useBlitTexture or self.hdrEnabled and self.msaaEnabled
        blitFormat = trinity.PIXEL_FORMAT.R16G16B16A16_FLOAT if self.hdrEnabled else self.bbFormat
        if useBlitTexture and self._TargetDiffers(self.blitTexture, 'trinity.Tr2RenderTarget', blitFormat, 0, width, height):
            self.blitTexture = rtm.GetRenderTargetAL(width, height, 1, blitFormat, index=1)
            if self.blitTexture is not None:
                self.blitTexture.name = 'sceneRenderJobSpace.blitTexture'
        elif not useBlitTexture:
            self.blitTexture = None
        if self.distortionEffectsEnabled:
            index = 0
            if self.fxaaEnabled and self.bbFormat == trinity.PIXEL_FORMAT.B8G8R8A8_UNORM and not self.hdrEnabled:
                index = 1
            if self._TargetDiffers(self.distortionTexture, 'trinity.Tr2RenderTarget', trinity.PIXEL_FORMAT.B8G8R8A8_UNORM, 0, width, height):
                self.distortionTexture = rtm.GetRenderTargetAL(width, height, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM, index)
                if self.distortionTexture:
                    self.distortionTexture.name = 'sceneRenderJobSpace.distortionTexture'
            self._SetDistortionMap()
        else:
            self.distortionTexture = None
            self._SetDistortionMap()

    def _TargetDiffers(self, target, blueType, format, msType = 0, width = 0, height = 0):
        if target is None:
            return True
        if blueType != target.__bluetype__:
            return True
        if format != target.format:
            return True
        multiSampleType = getattr(target, 'multiSampleType', None)
        if multiSampleType is not None and multiSampleType != msType:
            return True
        if width != 0 and target.width != width:
            return True
        if height != 0 and target.height != height:
            return True
        return False

    def _RefreshRenderTargets(self):
        self.renderTargetList = (blue.BluePythonWeakRef(self.customBackBuffer),
         blue.BluePythonWeakRef(self.customDepthStencil),
         blue.BluePythonWeakRef(self.depthTexture),
         blue.BluePythonWeakRef(self.blitTexture),
         blue.BluePythonWeakRef(self.distortionTexture))
        renderTargets = (x.object for x in self.renderTargetList)
        self.SetRenderTargets(*renderTargets)

    def _RefreshAntiAliasing(self):
        if 'aaQuality' not in self.overrideSettings:
            self.antiAliasingQuality = self.aaQuality = settings.public.device.Get('antiAliasing', self.aaQuality)
        if sm.IsServiceRunning('device'):
            self.msaaType = sm.GetService('device').GetMSAATypeFromQuality(self.antiAliasingQuality)
        else:
            self.msaaType = 8
        self.fxaaQuality = self._GetFXAAQuality(self.antiAliasingQuality)
        if self.useFXAA:
            self.EnableFXAA(self.antiAliasingEnabled)
        else:
            self.EnableMSAA(self.antiAliasingEnabled)

    def UseFXAA(self, flag):
        self.useFXAA = flag
        if self.useFXAA:
            self.EnableMSAA(False)
        else:
            self.EnableFXAA(False)
        self._RefreshAntiAliasing()

    def EnableDistortionEffects(self, enable):
        self.distortionEffectsEnabled = enable

    def EnableAntiAliasing(self, enable):
        self.antiAliasingEnabled = enable
        self._RefreshAntiAliasing()

    def EnableFXAA(self, enable):
        self.fxaaEnabled = enable
        if not self.prepared:
            return
        if enable:
            if getattr(self, 'fxaaEffect', None) is None:
                self.fxaaEffect = trinity.Tr2ShaderMaterial()
                self.fxaaEffect.highLevelShaderName = 'PostProcess'
            self.fxaaEffect.defaultSituation = self.fxaaQuality
            self.fxaaEffect.BindLowLevelShader([])
            self.AddStep('FXAA', trinity.TriStepRenderFullScreenShader(self.fxaaEffect))
            if not self.usePostProcessing:
                self.AddStep('FXAA_CLEAR', trinity.TriStepClear((0, 0, 0, 1), 1.0))
            self.RemoveStep('FINAL_BLIT')
        else:
            self.RemoveStep('FXAA')
            self.RemoveStep('FXAA_CLEAR')
        if not self.enabled:
            return
        self._CreateRenderTargets()
        self._RefreshRenderTargets()

    def EnableMSAA(self, enable):
        self.msaaEnabled = enable
        if not self.prepared:
            return
        if not self.enabled:
            return
        self._CreateRenderTargets()
        self._RefreshRenderTargets()

    def DoPrepareResources(self):
        if not self.enabled or not self.canCreateRenderTargets:
            return
        try:
            self.prepared = True
            self.SetSettingsBasedOnPerformancePreferences()
        except trinity.D3DERR_OUTOFVIDEOMEMORY:
            log.LogException()
            self.DoReleaseResources(1)
            self._RefreshRenderTargets()
            uthread.new(self.NotifyResourceCreationFailed)

    def _GetFXAAQuality(self, quality):
        if quality == 3:
            return 'FXAA_High'
        if quality == 2:
            return 'FXAA_Medium'
        if quality == 1:
            return 'FXAA_Low'
        return ''

    def _SetSettingsBasedOnPerformancePreferences(self):
        self.antiAliasingEnabled = self.aaQuality > 0
        self.antiAliasingQuality = self.aaQuality
        if sm.IsServiceRunning('device'):
            deviceSvc = sm.GetService('device')
            self.msaaType = sm.GetService('device').GetMSAATypeFromQuality(self.aaQuality)
        else:
            self.msaaType = 8
        self.fxaaQuality = self._GetFXAAQuality(self.aaQuality)
        if self.shadowQuality > 0 and self.shadowMap is None:
            self.shadowMap = trinity.TriShadowMap()
        elif self.shadowQuality == 0:
            self.shadowMap = None
        if self.postProcessingQuality == 1:
            self.postProcessingJob.AddPostProcess('Bloom', 'res:/PostProcess/BloomExp.red')
        elif self.postProcessingQuality == 2:
            self.postProcessingJob.AddPostProcess('Bloom', 'res:/PostProcess/BloomVivid.red')

    def SetSettingsBasedOnPerformancePreferences(self):
        if not self.enabled:
            return
        self.ApplyBaseSettings()
        self._SetSettingsBasedOnPerformancePreferences()
        self.usePostProcessing = self.postProcessingQuality > 0
        self.doDepthPass = not self.useFXAA and self.msaaType > 1 or self.forceDepthPass
        if self.distortionEffectsEnabled:
            self.distortionJob.AddPostProcess('Distortion', 'res:/PostProcess/distortion.red')
            self.backgroundDistortionJob.AddPostProcess('Distortion', 'res:/PostProcess/distortion.red')
        self._RefreshAntiAliasing()
        self._CreateRenderTargets()
        self._RefreshRenderTargets()
        self.ApplyPerformancePreferencesToScene()

    def ApplyPerformancePreferencesToScene(self):
        self._SetShadowMap()
        self._SetDepthMap()
        self._SetDistortionMap()

    def SetMultiViewStage(self, stageKey):
        self.currentMultiViewStageKey = stageKey

    def SetRenderTargets(self, customBackBuffer, customDepthStencil, depthTexture, blitTexture, distortionTexture):
        self.RemoveStep('SET_DEPTH')
        if self.GetSwapChain() is not None:
            self.AddStep('SET_SWAPCHAIN_RT', trinity.TriStepSetRenderTarget(self.GetSwapChain().backBuffer))
            self.AddStep('SET_SWAPCHAIN_DEPTH', trinity.TriStepSetDepthStencil(self.GetSwapChain().depthStencilBuffer))
        else:
            self.RemoveStep('SET_SWAPCHAIN_RT')
            self.RemoveStep('SET_SWAPCHAIN_DEPTH')
        activePostProcessing = self.usePostProcessing and self.postProcessingJob.liveCount > 0
        if customBackBuffer is not None:
            self.AddStep('SET_CUSTOM_RT', trinity.TriStepPushRenderTarget(customBackBuffer))
            self.AddStep('SET_FINAL_RT', trinity.TriStepPopRenderTarget())
            if self.msaaEnabled and not activePostProcessing:
                if self.hdrEnabled:
                    self.AddStep('FINAL_BLIT', self._DoFormatConversionStep(blitTexture, customBackBuffer))
                else:
                    self.AddStep('FINAL_BLIT', trinity.TriStepResolve(self.GetBackBufferRenderTarget(), customBackBuffer))
            elif self.hdrEnabled and not activePostProcessing and not self.msaaEnabled:
                self.AddStep('FINAL_BLIT', self._DoFormatConversionStep(customBackBuffer))
            else:
                self.RemoveStep('FINAL_BLIT')
            if self.fxaaEnabled:
                self.AddStep('SET_VAR_GATHER', trinity.TriStepSetVariableStore('GatherMap', customBackBuffer))
                self.RemoveStep('FINAL_BLIT')
            else:
                self.RemoveStep('SET_VAR_GATHER')
        else:
            self.RemoveStep('SET_CUSTOM_RT')
            self.RemoveStep('FINAL_BLIT')
            self.RemoveStep('SET_FINAL_RT')
            self.RemoveStep('SET_VAR_GATHER')
        if customDepthStencil is not None:
            self.AddStep('SET_DEPTH', trinity.TriStepPushDepthStencil(customDepthStencil))
            self.AddStep('RESTORE_DEPTH', trinity.TriStepPopDepthStencil())
        else:
            self.RemoveStep('RESTORE_DEPTH')
        if self.depthTexture is not None:
            if not self.doDepthPass:
                self.AddStep('SET_DEPTH', trinity.TriStepPushDepthStencil(depthTexture))
                self.AddStep('RESTORE_DEPTH', trinity.TriStepPopDepthStencil())
            self._SetDepthMap()
            self.AddStep('SET_VAR_DEPTH', trinity.TriStepSetVariableStore('DepthMap', depthTexture))
        else:
            if not self.msaaEnabled:
                self.RemoveStep('SET_DEPTH')
                self.RemoveStep('RESTORE_DEPTH')
            self.RemoveStep('SET_VAR_DEPTH')
        self._RefreshPostProcessingJob(self.postProcessingJob, self.usePostProcessing and self.prepared)
        self._RefreshPostProcessingJob(self.distortionJob, self.distortionEffectsEnabled and self.prepared)
        self._RefreshPostProcessingJob(self.backgroundDistortionJob, self.distortionEffectsEnabled and self.prepared)
        if distortionTexture is not None:
            self.AddStep('DO_DISTORTIONS', trinity.TriStepRunJob(self.distortionJob))
            distortionTriTextureRes = trinity.TriTextureRes()
            distortionTriTextureRes.SetFromRenderTarget(distortionTexture)
            self.distortionJob.SetPostProcessVariable('Distortion', 'TexDistortion', distortionTriTextureRes)
            self.backgroundDistortionJob.SetPostProcessVariable('Distortion', 'TexDistortion', distortionTriTextureRes)
        else:
            self.RemoveStep('DO_DISTORTIONS')
        self._CreateDepthPass()

    def GetRenderTargets(self):
        return self.renderTargetList

    def EnableSceneUpdate(self, isEnabled):
        if isEnabled:
            self.AddStep('UPDATE_SCENE', trinity.TriStepUpdate(self.GetScene()))
        else:
            self.RemoveStep('UPDATE_SCENE')

    def EnableVisibilityQuery(self, isEnabled):
        pass