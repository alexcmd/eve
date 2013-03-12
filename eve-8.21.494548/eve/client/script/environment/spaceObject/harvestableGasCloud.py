#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/harvestableGasCloud.py
import spaceObject
import geo2
import math
import random

class HarvestableGasCloud(spaceObject.Cloud):
    __guid__ = 'spaceObject.HarvestableGasCloud'

    def Assemble(self):
        spaceObject.Cloud.Assemble(self)
        self.model.rotation = geo2.QuaternionRotationSetYawPitchRoll(random.random() * math.pi * 2.0, random.random() * math.pi, random.random() * math.pi)

    def SetRadiusScene(self, r):
        r *= 5
        if len(self.model.children):
            self.model.scaling = (r, r, r)