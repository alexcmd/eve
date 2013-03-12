#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/ui3d.py
import uicls
import trinity
import geo2
import log

class Container(uicls.UIRoot):
    __guid__ = 'ui3d.Container'

    def __init__(self, *args, **kwargs):
        self.renderScene = kwargs['scene']
        self.initialized = False
        self.sceneManager = sm.GetService('sceneManager')
        try:
            uicls.UIRoot.__init__(self, *args, **kwargs)
            self.Create3DRender()
            uicore.uilib.AddRootObject(self)
            self.initialized = True
        finally:
            if not self.initialized:
                self.Close()

    def Create3DRender(self):
        self.renderTexture = trinity.TriTexture2DParameter()
        self.renderTexture.name = 'DiffuseMap'
        self.renderColor = trinity.TriVector4Parameter()
        self.renderColor.name = 'DiffuseColor'
        self.renderColor.value = (1, 1, 1, 1)
        self.renderEffect = trinity.Tr2Effect()
        self.renderEffect.effectFilePath = 'res:/Graphics/Effect/Managed/Space/SpecialFX/TextureColor.fx'
        self.renderEffect.resources.append(self.renderTexture)
        self.renderEffect.parameters.append(self.renderColor)
        self.renderArea = trinity.Tr2MeshArea()
        self.renderArea.effect = self.renderEffect
        self.renderMesh = trinity.Tr2Mesh()
        self.renderMesh.name = 'orbitalBombardmentTarget'
        self.renderMesh.geometryResPath = 'res:/Graphics/Generic/UnitPlane/UnitPlane.gr2'
        self.renderMesh.transparentAreas.append(self.renderArea)
        self.transform = trinity.EveRootTransform()
        self.transform.mesh = self.renderMesh
        self.renderScene.objects.append(self.transform)
        self.renderJob = trinity.CreateRenderJob()
        self.renderJob.Update(self.renderScene)
        self.renderObject = self.GetRenderObject()
        self.renderObject.is2dPick = False
        self.renderTarget = trinity.Tr2RenderTarget(self.width, self.height, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        self.renderJob.PushRenderTarget(self.renderTarget)
        self.renderJob.RenderScene(self.renderObject)
        self.renderJob.PopRenderTarget()
        self.renderJob.ScheduleRecurring(insertFront=True)
        self.renderTexture.SetResource(trinity.TriTextureRes(self.renderTarget))
        self.renderSteps[-1].enabled = False
        return self.transform

    def Close(self):
        if getattr(self, 'renderJob', None) is not None:
            self.renderJob.UnscheduleRecurring()
        if getattr(self, 'transform', None) is not None and getattr(self, 'renderScene', None) is not None:
            if self.transform in self.renderScene.objects:
                self.renderScene.objects.remove(self.transform)
        uicls.UIRoot.Close(self)
        uicore.uilib.RemoveRootObject(self)

    def PickObject(self, x, y):
        if self.sceneManager.GetActiveScene() != self.renderScene:
            return
        rescale = 1.0 / 10000.0
        projection = trinity.TriProjection()
        projection.PerspectiveFov(trinity.GetFieldOfView(), trinity.GetAspectRatio(), trinity.GetFrontClip(), trinity.GetBackClip())
        view = trinity.TriView()
        view.transform = trinity.GetViewTransform()
        scaling, rotation, translation = geo2.MatrixDecompose(self.transform.worldTransform)
        direction = geo2.Vector(*translation) - geo2.Vector(view.transform[0][0], view.transform[1][0], view.transform[2][0])
        if geo2.Vec3Dot(geo2.Vec3Normalize(direction), geo2.Vector(-view.transform[0][2], -view.transform[1][2], -view.transform[2][2])) < 0:
            return
        self.renderObject.translation = geo2.Vec3Scale(translation, rescale)
        self.renderObject.rotation = rotation
        self.renderObject.scaling = geo2.Vec3Scale(scaling, rescale)
        scaling, rotation, translation = geo2.MatrixDecompose(view.transform)
        translation = geo2.Vec3Scale(translation, rescale)
        view.transform = geo2.MatrixTransformation(None, None, scaling, None, rotation, translation)
        return self.renderObject.PickObject(x, y, projection, view, trinity.device.viewport)

    def _GetColor(self):
        return self.renderColor.value

    def _SetColor(self, value):
        self.renderColor.value = value

    color = property(_GetColor, _SetColor)

    def _GetRed(self):
        return self.renderColor.value[0]

    def _SetRed(self, value):
        self.renderColor.value = (value,
         self.renderColor.value[1],
         self.renderColor.value[2],
         self.renderColor.value[3])

    red = property(_GetRed, _SetRed)

    def _GetBlue(self):
        return self.renderColor.value[1]

    def _SetBlue(self, value):
        self.renderColor.value = (self.renderColor.value[0],
         value,
         self.renderColor.value[2],
         self.renderColor.value[3])

    blue = property(_GetBlue, _SetBlue)

    def _GetGreen(self):
        return self.renderColor.value[2]

    def _SetGreen(self, value):
        self.renderColor.value = (self.renderColor.value[0],
         self.renderColor.value[1],
         value,
         self.renderColor.value[3])

    green = property(_GetGreen, _SetGreen)

    def _GetAlpha(self):
        return self.renderColor.value[3]

    def _SetAlpha(self, value):
        self.renderColor.value = (self.renderColor.value[0],
         self.renderColor.value[1],
         self.renderColor.value[2],
         value)

    alpha = property(_GetAlpha, _SetAlpha)