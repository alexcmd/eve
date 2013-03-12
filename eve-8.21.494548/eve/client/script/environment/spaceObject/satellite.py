#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/satellite.py
import spaceObject
import geo2
import math
import blue
import trinity
import uthread
import util
import mathCommon

class Satellite(spaceObject.LargeCollidableStructure):
    __guid__ = 'spaceObject.Satellite'

    def Assemble(self):
        spaceObject.LargeCollidableStructure.Assemble(self)
        self.item = sm.GetService('michelle').GetItem(self.id)
        self.districtID = self.item.districtID
        direction = self.FindClosestPlanetDir()
        yaw = mathCommon.GetYawAngleFromDirectionVector(direction)
        pitch = mathCommon.GetPitchAngleFromDirectionVector(direction)
        self.model.rotationCurve = trinity.TriRotationCurve()
        self.model.rotationCurve.value = geo2.QuaternionRotationSetYawPitchRoll(yaw + math.pi, pitch - math.pi / 2, 0)
        proximity = sm.GetService('godma').GetTypeAttribute(self.item.typeID, const.attributeProximityRange)
        self.AddProximitySensor(proximity, 2, 0, False)

    def Release(self):
        spaceObject.LargeCollidableStructure.Release(self)
        uthread.new(sm.GetService('district').DisableDistrict, self.districtID)

    def DoProximity(self, violator, entered):
        if violator == session.shipid and getattr(self, 'districtID', None) is not None:
            if entered:
                uthread.new(sm.GetService('district').EnableDistrict, self.districtID)
            else:
                uthread.new(sm.GetService('district').DisableDistrict, self.districtID)