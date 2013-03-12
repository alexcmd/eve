#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/inflight/bracketsAndTargets/blinkingSpriteOnSharedCurve.py
import uicls
import trinity

class BlinkingSpriteOnSharedCurve(uicls.Sprite):
    __guid__ = 'uicls.BlinkingSpriteOnSharedCurve'

    def ApplyAttributes(self, attributes):
        uicls.Sprite.ApplyAttributes(self, attributes)
        self.blinkBinding = None
        curveSetName = attributes.curveSetName
        self.curveSetName = curveSetName
        fromCurveValue = attributes.get('fromCurveValue', 0.3)
        toCurveValue = attributes.get('toCurveValue', 0.6)
        duration = attributes.get('duration', 0.5)
        self.SetupSharedBlinkingCurve(curveSetName, fromCurveValue, toCurveValue, duration)

    def SetupSharedBlinkingCurve(self, cuverSetName, fromCurveValue, toCurveValue, duration, *args):
        curveSet = getattr(uicore, cuverSetName, None)
        if curveSet:
            curve = curveSet.curves[0]
        else:
            curveSet = trinity.TriCurveSet()
            setattr(uicore, cuverSetName, curveSet)
            setattr(curveSet, 'name', cuverSetName)
            trinity.device.curveSets.append(curveSet)
            curveSet.Play()
            curve = trinity.Tr2ScalarCurve()
            curve.name = 'blinking_curve'
            curve.length = duration
            curve.startValue = fromCurveValue
            curve.endValue = fromCurveValue
            curve.AddKey(duration / 2.0, toCurveValue)
            curve.cycle = True
            curve.interpolation = trinity.TR2CURVE_LINEAR
            curveSet.curves.append(curve)
        if getattr(self, 'blinkBinding', None) is not None:
            curveSet.bindings.remove(self.blinkBinding)
        self.blinkBinding = trinity.CreatePythonBinding(curveSet, curve, 'currentValue', self, 'opacity')

    def Close(self):
        if getattr(self, 'blinkBinding', None) is not None:
            curveSet = getattr(uicore, self.curveSetName, None)
            if curveSet:
                curveSet.bindings.remove(self.blinkBinding)
            self.blinkBinding = None
        uicls.Sprite.Close(self)