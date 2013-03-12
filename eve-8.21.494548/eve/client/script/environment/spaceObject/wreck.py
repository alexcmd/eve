#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/wreck.py
import blue
import spaceObject
import uthread
import timecurves
import random
import trinity
import geo2

class Wreck(spaceObject.DeployableSpaceObject):
    __guid__ = 'spaceObject.Wreck'

    def Assemble(self):
        self.UnSync()
        self.SetColorBasedOnStatus()

    def Prepare(self, spaceMgr):
        spaceObject.DeployableSpaceObject.Prepare(self, spaceMgr)
        slimItem = sm.StartService('michelle').GetBallpark().GetInvItem(self.id)
        shipBall = None
        if hasattr(slimItem, 'launcherID'):
            shipBall = sm.StartService('michelle').GetBall(slimItem.launcherID)
        if shipBall is None or not hasattr(shipBall, 'model'):
            if hasattr(self.model, 'modelRotationCurve'):
                self.model.modelRotationCurve = trinity.TriRotationCurve()
                quat = geo2.QuaternionRotationSetYawPitchRoll(random.random() * 6.28, random.random() * 6.28, random.random() * 6.28)
                self.model.modelRotationCurve.value = quat
            else:
                self.model.rotationCurve = None
                self.model.rotation.SetYawPitchRoll(random.random() * 6.28, random.random() * 6.28, random.random() * 6.28)
            self.model.display = 1
            self.delayedDisplay = 0
        else:
            self.model.rotationCurve = None
            if hasattr(self.model, 'modelRotationCurve'):
                if shipBall.model is not None:
                    if hasattr(shipBall.model, 'modelRotationCurve') and shipBall.model.modelRotationCurve is not None:
                        self.model.modelRotationCurve = shipBall.model.modelRotationCurve
                    else:
                        self.model.modelRotationCurve = trinity.TriRotationCurve()
                        quat = geo2.QuaternionRotationSetYawPitchRoll(shipBall.yaw, shipBall.pitch, shipBall.roll)
                        self.model.modelRotationCurve.value = quat
            elif shipBall.model is not None:
                if hasattr(shipBall.model, 'rotation'):
                    self.model.rotation = shipBall.model.rotation
                else:
                    quat = geo2.QuaternionRotationSetYawPitchRoll(shipBall.yaw, shipBall.pitch, shipBall.roll)
                    self.model.modelRotationCurve.value = quat
            shipBall.wreckID = self.id
            self.model.display = 0
            self.delayedDisplay = 1
            uthread.pool('Wreck::DisplayWreck', self.DisplayWreck, 3000)

    def Display(self, display = 1, canYield = True):
        if display and getattr(self, 'delayedDisplay', 0):
            return
        spaceObject.SpaceObject.Display(self, display, canYield)

    def DisplayWreck(self, duration):
        if duration:
            blue.pyos.synchro.SleepSim(duration)
        if self.model is not None and self.model.display == 0:
            if len(self.model.children) and getattr(self.model.children[0], 'rotationCurve', None) is not None:
                rotationCurves = self.model.children[0].rotationCurve.Find('trinity.TriScalarCurve')
                self.model.children[0].useCurves = True
                for curve in rotationCurves:
                    curve.start = blue.os.GetSimTime()

            self.model.display = 1
        self.delayedDisplay = 0

    def Explode(self):
        if self.exploded:
            return False
        self.fadeCurve = trinity.Load('res:/dx9/model/shipwrecks/FadeCurve.red')
        self.model.curveSets.append(self.fadeCurve)
        if self.model.mesh:
            for area in self.model.mesh.opaqueAreas:
                for par in area.effect.parameters:
                    if par.name == 'AlphaThreshold':
                        newBinding = self.fadeCurve.bindings[0].CopyTo()
                        newBinding.destinationObject = par
                        newBinding.sourceObject = self.fadeCurve.curves[0]
                        self.fadeCurve.bindings.append(newBinding)

        self.fadeCurve.curves[0].Sort()
        self.exploded = True
        if self.model is None:
            return False
        curves = self.model.Find('trinity.TriColorCurve')
        timecurves.ReverseTimeCurvesF(curves)
        curves.extend(self.model.Find('audio.SoundNode'))
        timecurves.ResetTimeAndSoundCurves(curves)
        self.fadeCurve.Play()
        blue.pyos.synchro.SleepSim(10000)
        return False


exports = {'spaceObject.Wreck': Wreck}