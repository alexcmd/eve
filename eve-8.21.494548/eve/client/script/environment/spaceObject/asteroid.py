#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/asteroid.py
import spaceObject
import trinity
import random
import math
import timecurves

class Asteroid(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.Asteroid'

    def LoadModel(self, fileName = None, loadedModel = None):
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        if slimItem is not None:
            type = cfg.invtypes.Get(slimItem.typeID)
            typeName = type._typeName
            if ' ' in typeName:
                typeNameParts = typeName.split(' ')
                typeName = ''.join(typeNameParts[1:]) + '_' + typeNameParts[0]
            variationID = '0' + str(self.id % 4 + 1)
            scene2url3D = 'res:/dx9/Model/WorldObject/Asteroid/' + typeName + '/Shards/' + typeName + '_shard' + variationID + '_unmined.red'
            spaceObject.SpaceObject.LoadModel(self, fileName=scene2url3D)

    def Assemble(self):
        if self.model is None:
            self.LogError('Cannot Assemble Asteroid, model failed to load')
            return
        if self.HasBlueInterface(self.model, 'IEveSpaceObject2'):
            self.model.modelScale = self.radius
            pi = math.pi
            id = trinity.TriQuaternion()
            cleanRotation = trinity.TriQuaternion()
            preRotation = trinity.TriQuaternion()
            postRotation = trinity.TriQuaternion()
            rotKey = trinity.TriQuaternion()
            preRotation.SetYawPitchRoll(random.random() * pi, random.random() * pi, random.random() * pi)
            postRotation.SetYawPitchRoll(random.random() * pi, random.random() * pi, random.random() * pi)
            curve = trinity.TriRotationCurve()
            curve.extrapolation = trinity.TRIEXT_CYCLE
            duration = 50.0 + random.random() * 50.0 * math.log(self.radius)
            for i in [0.0,
             0.5,
             1.0,
             1.5,
             2.0]:
                cleanRotation.SetYawPitchRoll(0.0, pi * i, 0.0)
                rotKey.SetIdentity()
                rotKey.MultiplyQuaternion(preRotation)
                rotKey.MultiplyQuaternion(cleanRotation)
                rotKey.MultiplyQuaternion(postRotation)
                curve.AddKey(duration * i, rotKey, id, id, trinity.TRIINT_SLERP)

            curve.Sort()
            self.model.modelRotationCurve = curve
        else:
            self.model.rotation.SetYawPitchRoll(random.random() * 6.28, random.random() * 6.28, random.random() * 6.28)
            timecurves.ResetTimeCurves(self.model, self.id * 12345L)
            timecurves.ScaleTime(self.model, 5.0 + self.id % 20 / 20.0)
            self.model.scaling.SetXYZ(self.radius, self.radius, self.radius)
            self.model.boundingSphereRadius = 1.0


exports = {'spaceObject.Asteroid': Asteroid}