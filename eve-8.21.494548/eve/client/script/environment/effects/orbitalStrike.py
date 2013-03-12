#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/effects/orbitalStrike.py
import blue
import effects
import uthread
import spaceObject

class OrbitalStrike(effects.StandardWeapon):
    __guid__ = 'effects.OrbitalStrike'
    TYPES = {const.typeTacticalEMPAmmoS: spaceObject.Planet.ORBBOMB_IMPACT_FX_EM,
     const.typeTacticalHybridAmmoS: spaceObject.Planet.ORBBOMB_IMPACT_FX_HYBRID,
     const.typeTacticalLaserAmmoS: spaceObject.Planet.ORBBOMB_IMPACT_FX_LASER}

    def __init__(self, trigger, *args):
        effects.StandardWeapon.__init__(self, trigger, *args)
        if trigger.graphicInfo:
            self.district = sm.GetService('district').GetDistrict(trigger.graphicInfo['districtID'])
            self.ballIDs = [trigger.shipID, self.district['ball'].id]
        else:
            self.district = None

    def Start(self, duration):
        if not self.district:
            return
        effects.StandardWeapon.Start(self, duration)

    def Stop(self):
        effects.StandardWeapon.Stop(self)
        uthread.new(self._PlanetImpact)

    def _PlanetImpact(self):
        if self.otherTypeID not in self.TYPES:
            self.LogWarn('Ignoring orbital strike for unknown type: ', self.otherTypeID)
            return
        if self.district and self.district['planet']:
            self.district['planet'].AddExplosion(self.district['uniqueName'], self.TYPES[self.otherTypeID], 0.1)