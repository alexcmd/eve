#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\trinity\sceneRenderJobSpaceJessica.py
from trinity.sceneRenderJobSpace import SceneRenderJobSpace
import trinity

def CreateJessicaSpaceRenderJob(name = None, stageKey = None):
    newRJ = SceneRenderJobSpaceJessica()
    if name is not None:
        newRJ.ManualInit(name)
    else:
        newRJ.ManualInit()
    newRJ.SetMultiViewStage(stageKey)
    return newRJ


class SceneRenderJobSpaceJessica(SceneRenderJobSpace):

    def _ManualInit(self, name = 'SceneRenderJobSpace'):
        SceneRenderJobSpace._ManualInit(self, name)
        self.persistedPostProcess = {}
        self.settings = {'aaQuality': 3,
         'postProcessingQuality': 2,
         'shadowQuality': 2,
         'shadowMapSize': 1024,
         'hdrEnabled': True}
        self.backBufferOverride = None
        self.depthBufferOverride = None

    def SetSettings(self, rjSettings):
        self.settings = rjSettings

    def GetSettings(self):
        return self.settings

    def GetMSAATypeFromQuality(self, aaQuality):
        if aaQuality == 0:
            return 0
        return 2 ** aaQuality

    def _RefreshAntiAliasing(self):
        if self.useFXAA:
            self.EnableFXAA(self.antiAliasingEnabled)
        else:
            self.EnableMSAA(self.antiAliasingEnabled)

    def GetPostProcesses(self):
        if self.postProcessingJob is not None:
            return self.postProcessingJob.GetPostProcesses()
        return []

    def _GetSettings(self):
        return self.settings

    def OverrideBuffers(self, backBuffer, depthBuffer):
        self.backBufferOverride = backBuffer
        self.depthBufferOverride = depthBuffer

    def _SetSettingsBasedOnPerformancePreferences(self):
        self.aaQuality = self.settings['aaQuality']
        self.antiAliasingEnabled = self.aaQuality > 0
        self.antiAliasingQuality = self.aaQuality
        self.msaaType = self.GetMSAATypeFromQuality(self.aaQuality)
        self.fxaaQuality = self._GetFXAAQuality(self.aaQuality)
        self.shadowQuality = self.settings['shadowQuality']
        if self.shadowQuality > 0 and self.shadowMap is None:
            self.shadowMap = trinity.TriShadowMap()
            self.shadowMap.size = self.settings['shadowMapSize']
        elif self.shadowQuality == 0:
            self.shadowMap = None
        else:
            self.shadowMap.size = self.settings['shadowMapSize']
        self.usePostProcessing = self.postProcessingJob.liveCount > 0

    def SetRenderTargets(self, *args):
        SceneRenderJobSpace.SetRenderTargets(self, *args)
        if self.depthBufferOverride:
            self.AddStep('SET_SWAPCHAIN_DEPTH', trinity.TriStepSetDepthStencil(self.depthBufferOverride))
        if self.backBufferOverride:
            self.AddStep('SET_SWAPCHAIN_RT', trinity.TriStepSetRenderTarget(self.backBufferOverride))

    def GetBackBufferSize(self):
        if self.backBufferOverride is None:
            return SceneRenderJobSpace.GetBackBufferSize(self)
        width = self.backBufferOverride.width
        height = self.backBufferOverride.height
        return (width, height)

    def _GetRTForDepthPass(self):
        if self.backBufferOverride is not None:
            return self.backBufferOverride
        return SceneRenderJobSpace._GetRTForDepthPass(self)