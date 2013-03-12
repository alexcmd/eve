#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/effects/turrets.py
import effects
import uthread
import trinity

class StandardWeapon(effects.GenericEffect):
    __guid__ = 'effects.StandardWeapon'

    def __init__(self, trigger, *args):
        self.ballIDs = [trigger.shipID, trigger.targetID]
        self.gfx = None
        self.gfxModel = None
        self.moduleID = trigger.moduleID
        self.otherTypeID = trigger.otherTypeID
        self.fxSequencer = sm.GetService('FxSequencer')

    def Prepare(self):
        pass

    def Shoot(self, shipBall, targetBall):
        if getattr(self, 'turret', None) is not None:
            self.turret.SetTarget(shipBall, targetBall)
            self.turret.StartShooting()

    def Start(self, duration):
        if not settings.user.ui.Get('turretsEnabled', 1):
            return
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        targetID = self.ballIDs[1]
        targetBall = self.fxSequencer.GetBall(targetID)
        if targetBall is None:
            return
        if shipBall is None:
            return
        if not hasattr(shipBall, 'fitted'):
            self.fxSequencer.LogError(self.__guid__ + str(shipBall.id) + ' Turrets: Error! can not fit turrets. No fitted attribute ')
            return
        if not shipBall.fitted:
            shipBall.FitHardpoints(blocking=True)
        if shipBall.modules is None:
            return
        self.turret = shipBall.modules.get(self.moduleID)
        if getattr(self, 'turret', None) is None:
            self.fxSequencer.LogError('Turret not fitted on shipID', shipID)
            return
        if hasattr(self.turret, 'SetAmmoColor'):
            self.SetAmmoColor()
        uthread.worker('FxSequencer::ShootTurrets', self.Shoot, shipID, targetID)

    def SetAmmoColor(self):
        if self.otherTypeID is not None:
            self.turret.SetAmmoColorByTypeID(self.otherTypeID)

    def Stop(self):
        if getattr(self, 'turret', None) is None:
            return
        self.turret.StopShooting()
        self.turret.shooting = 0
        self.turret = None

    def Repeat(self, duration):
        if getattr(self, 'turret', None) is None:
            return
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        targetID = self.ballIDs[1]
        targetBall = self.fxSequencer.GetBall(targetID)
        if targetBall is None:
            self.turret.Rest()
            self.turret.shooting = 0
            return
        if shipBall is None:
            self.turret.Rest()
            self.turret.shooting = 0
            return
        uthread.worker('FxSequencer::ShootTurrets', self.Shoot, shipID, targetID)


class CloudMining(StandardWeapon):
    __guid__ = 'effects.CloudMining'

    def SetAmmoColor(self):
        targetBall = self.GetEffectTargetBall()
        targetModel = getattr(targetBall, 'model', None)
        color = (1.0, 1.0, 1.0, 1.0)
        emitters = targetModel.Find('trinity.EveEmitterStatic')
        if len(emitters):
            if len(emitters[0].particleData):
                color = emitters[0].particleData[0].color
        self.turret.SetAmmoColor(trinity.TriColor(*color))


class MissileLaunch(effects.GenericEffect):
    __guid__ = 'effects.MissileLaunch'

    def __init__(self, trigger, *args):
        self.ballIDs = [trigger.shipID, trigger.targetID]
        self.gfx = None
        self.gfxModel = None
        self.moduleID = trigger.moduleID
        self.otherTypeID = trigger.otherTypeID
        self.fxSequencer = sm.GetService('FxSequencer')

    def Prepare(self):
        pass

    def Shoot(self, shipBall, targetBall):
        if getattr(self, 'turret', None) is not None:
            self.turret.SetTarget(shipBall, targetBall)

    def Start(self, duration):
        if not settings.user.ui.Get('turretsEnabled', 1):
            return
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        targetID = self.ballIDs[1]
        targetBall = self.fxSequencer.GetBall(targetID)
        if targetBall is None:
            return
        if shipBall is None:
            return
        if not hasattr(shipBall, 'fitted'):
            return
        if not shipBall.fitted:
            shipBall.FitHardpoints(blocking=True)
        if shipBall.modules is None:
            return
        self.turret = shipBall.modules.get(self.moduleID)
        if getattr(self, 'turret', None) is None:
            self.fxSequencer.LogError('Turret not fitted on shipID', shipID)
            return
        uthread.worker('FxSequencer::ShootTurrets', self.Shoot, shipID, targetID)

    def SetAmmoColor(self):
        pass

    def Stop(self):
        if getattr(self, 'turret', None) is None:
            return
        self.turret.StopShooting()
        self.turret.shooting = 0
        self.turret = None

    def Repeat(self, duration):
        if getattr(self, 'turret', None) is None:
            return
        shipID = self.ballIDs[0]
        shipBall = self.fxSequencer.GetBall(shipID)
        targetID = self.ballIDs[1]
        targetBall = self.fxSequencer.GetBall(targetID)
        if targetBall is None:
            self.turret.Rest()
            self.turret.shooting = 0
            return
        if shipBall is None:
            self.turret.Rest()
            self.turret.shooting = 0
            return
        uthread.worker('FxSequencer::ShootTurrets', self.Shoot, shipID, targetID)