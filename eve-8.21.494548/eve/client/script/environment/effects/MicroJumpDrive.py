#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/effects/MicroJumpDrive.py
import effects
import trinity
import blue
import uthread
SECOND = 1000
CAMERA_RESET_TIME = 1500

class MicroJumpDriveEngage(effects.ShipEffect):
    __guid__ = 'effects.MicroJumpDriveEngage'

    def __init__(self, trigger, *args):
        effects.ShipEffect.__init__(self, trigger, *args)
        self.playerEffect = None

    def Prepare(self):
        effects.ShipEffect.Prepare(self, False)
        if session.shipid == self.GetEffectShipID():
            self.playerEffect = trinity.Load('res:/dx9/model/effect/mjd_effect_player.red')
            self.AddSoundToEffect(2)

    def Stop(self):
        pass

    def _DelayedStop(self, delay):
        blue.synchro.SleepSim(delay)
        if self.playerEffect is not None:
            self.RemoveFromScene(self.playerEffect)
            self.playerEffect = None
        effects.ShipEffect.Stop(self)

    def Start(self, duration):
        if self.gfx is None:
            raise RuntimeError('MicroJumpDriveEngage: no effect defined:' + self.__guid__)
        self.curveSets = self.gfx.curveSets
        self.controllerCurve = None
        length = 0
        for each in self.gfx.curveSets:
            length = max(each.GetMaxCurveDuration() * 1000, length)
            each.Play()
            if each.name == 'PLAY_START':
                self.controllerCurve = each.curves[0]

        self.AddToScene(self.gfxModel)
        if self.playerEffect is None:
            self._SetCurveTime(duration * 0.001)
        else:
            self._SetCurveTime(duration * 0.001 - 0.25)
            length = 0
            for each in self.playerEffect.curveSets:
                length = max(each.GetMaxCurveDuration() * 1000, length)
                each.Stop()

            triggerDelayPlayer = duration - length
            uthread.new(self._TriggerPlaybackPlayer, triggerDelayPlayer)
        uthread.new(self._DelayedStop, duration + 2 * SECOND)

    def _SetCurveTime(self, duration):
        lastKey = self.controllerCurve.GetKeyCount() - 1
        timeDelta = self.controllerCurve.length - self.controllerCurve.GetKeyTime(lastKey)
        self.controllerCurve.length = duration
        self.controllerCurve.SetKeyTime(lastKey, duration - timeDelta)
        self.controllerCurve.Sort()

    def _TriggerPlaybackPlayer(self, delay):
        blue.synchro.SleepSim(delay - CAMERA_RESET_TIME)
        cam = sm.GetService('camera')
        if cam.LookingAt() != session.shipid:
            cam.LookAt(session.shipid, resetCamera=False)
        blue.synchro.SleepSim(CAMERA_RESET_TIME)
        self.AddToScene(self.playerEffect)
        for each in self.playerEffect.curveSets:
            each.Play()

        sm.GetService('audio').SendUIEvent('microjumpdrive_jump_play')


class MicroJumpDriveJump(effects.GenericEffect):
    __guid__ = 'effects.MicroJumpDriveJump'

    def __init__(self, trigger, *args):
        effects.GenericEffect.__init__(self, trigger, *args)
        self.position = trigger.graphicInfo
        self.gfxModel = None

    def Prepare(self):
        self.ball = self._SpawnClientBall(self.position)
        gfx = trinity.Load('res:/dx9/model/effect/mjd_effect_jump.red')
        if gfx is None:
            return
        model = getattr(self.GetEffectShipBall(), 'model', None)
        if model is None:
            return
        radius = model.GetBoundingSphereRadius()
        gfx.scaling = (radius, radius, radius)
        self.gfxModel = trinity.EveRootTransform()
        self.gfxModel.children.append(gfx)
        self.gfxModel.boundingSphereRadius = radius
        self.gfxModel.translationCurve = self.ball
        self.sourceObject = self.gfxModel
        self.gfx = gfx
        self.AddSoundToEffect(2)

    def Start(self, duration):
        if self.gfxModel is not None:
            self.AddToScene(self.gfxModel)

    def Stop(self):
        self._DestroyClientBall(self.ball)
        self.ball = None
        self.sourceObject = None
        self.gfx = None
        if self.gfxModel is not None:
            self.RemoveFromScene(self.gfxModel)
            self.gfxModel.translationCurve = None
            self.gfxModel = None

    def _SpawnClientBall(self, position):
        bp = sm.GetService('michelle').GetBallpark()
        if bp is None:
            return
        return bp.AddClientSideBall(position)

    def _DestroyClientBall(self, ball):
        bp = sm.GetService('michelle').GetBallpark()
        if bp is not None:
            bp.RemoveBall(ball.id)