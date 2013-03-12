#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/effects/cloaking.py
import effects

class Cloaking(effects.GenericEffect):
    __guid__ = 'effects.Cloaking'


class Cloak(effects.ShipEffect):
    __guid__ = 'effects.Cloak'

    def Prepare(self):
        effects.ShipEffect.Prepare(self)
        shipID = self.GetEffectShipID()
        shipBall = self.GetEffectShipBall()
        resPath = None
        areaCount = 10
        if shipBall.model.mesh is None:
            if shipBall.model.highDetailMesh is not None:
                if hasattr(shipBall.model.highDetailMesh.object, 'geometryResPath'):
                    resPath = shipBall.model.highDetailMesh.object.geometryResPath
        else:
            areaCount = len(shipBall.model.mesh.Find('trinity.Tr2MeshArea'))
            areaCount = max(areaCount, 3)
            resPath = shipBall.model.mesh.geometryResPath
        if resPath is None:
            self.fxSequencer.LogError("This effect could not determine the respath to use as it's model: ", self.__guid__, shipID)
            return
        for mesh in self.gfxModel.Find('trinity.Tr2Mesh'):
            mesh.geometryResPath = resPath

        effectAreas = self.gfxModel.Find('trinity.Tr2MeshArea')
        for fxArea in effectAreas:
            fxArea.count = areaCount

        normalScalingSize = shipBall.model.GetBoundingSphereRadius() * 0.01
        for parameter in self.gfxModel.Find(['trinity.TriVector4Parameter', 'trinity.Tr2Vector4Parameter']):
            if parameter.name == 'ScaleAlongNormal':
                originalValue = parameter.value
                parameter.value = (normalScalingSize * originalValue[0],
                 normalScalingSize * originalValue[1],
                 normalScalingSize * originalValue[2],
                 normalScalingSize * originalValue[3])

        slimItem = self.fxSequencer.GetItem(shipID)
        if hasattr(slimItem, 'dunRotation') and hasattr(shipBall.model, 'rotationCurve'):
            self.gfxModel.rotationCurve = shipBall.model.rotationCurve

    def Start(self, duration):
        shipBall = self.GetEffectShipBall()
        shipBall.KillCloakedCopy()
        shipBall.PlayGeneralAudioEvent('wise:/ship_cloak_play')
        shipBall.cloakedCopy = self.gfxModel
        effects.ShipEffect.Start(self, duration)
        if getattr(shipBall, 'model', None) is not None:
            model = shipBall.model
            bindings = self.gfxModel.Find('trinity.TriValueBinding')
            for binding in bindings:
                if binding.name == 'hide':
                    binding.destinationObject = model
                    binding.destinationAttribute = 'display'
                    binding.sourceAttribute = 'value'

    def Stop(self):
        pass


class CloakNoAnim(Cloak):
    __guid__ = 'effects.CloakNoAmim'

    def Start(self, duration):
        Cloak.Start(self, 6000)
        length = self.gfx.curveSets[0].GetMaxCurveDuration()
        self.gfx.curveSets[0].PlayFrom(length)
        shipBall = self.GetEffectShipBall()
        if getattr(shipBall, 'model', None) is not None:
            shipBall.model.display = False


class CloakRegardless(Cloak):
    __guid__ = 'effects.CloakRegardless'


class Uncloak(effects.ShipEffect):
    __guid__ = 'effects.Uncloak'

    def Prepare(self):
        shipBall = self.GetEffectShipBall()
        if shipBall is None:
            raise RuntimeError('ShipEffect: no ball found')
        cloakedModel = getattr(shipBall, 'cloakedCopy', None)
        if cloakedModel is not None:
            effects.ShipEffect.Prepare(self)
            self.gfxModel = cloakedModel
            self.gfx = cloakedModel.children[0]
        else:
            effects.Cloak.Prepare(self)
            if getattr(shipBall, 'model', None) is not None:
                model = shipBall.model
                bindings = self.gfxModel.Find('trinity.TriValueBinding')
                for binding in bindings:
                    if binding.name == 'hide':
                        binding.destinationObject = model
                        binding.destinationAttribute = 'display'
                        binding.sourceAttribute = 'value'

    def Start(self, duration):
        shipBall = self.GetEffectShipBall()
        if self.gfx is None:
            return
        length = self.gfx.curveSets[0].GetMaxCurveDuration()
        if length > 0.0:
            scaleValue = -length / (duration / 1000.0)
            self.gfx.curveSets[0].scale = scaleValue
        self.gfx.curveSets[0].PlayFrom(length)
        shipBall.PlayGeneralAudioEvent('wise:/ship_uncloak_play')

    def Stop(self):
        shipBall = self.GetEffectShipBall()
        shipModel = getattr(shipBall, 'model', None)
        if shipBall is not None and self.gfx is not None and self.gfxModel == shipBall.cloakedCopy:
            shipBall.cloakedCopy = None
            if shipModel is not None:
                shipModel.display = True
        effects.ShipEffect.Stop(self)