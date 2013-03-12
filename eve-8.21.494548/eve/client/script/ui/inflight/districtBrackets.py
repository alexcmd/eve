#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/inflight/districtBrackets.py
import xtriui
import state
import trinity
import uiconst
import uicls
import ui3d
import geo2
import math
import planet
import blue
import log
import uthread
import localization

class DistrictBracket(object):
    __guid__ = 'xtriui.DistrictBracket'
    __notifyevents__ = ['OnDistrictTargets']

    def __init__(self, district):
        sm.RegisterNotify(self)
        trinity.device.RegisterResource(self)
        self.district = district
        self.targets = {}
        self.pending = False
        self.connected = False
        self.mouseOver = False
        self.animating = False
        self.notifications = set()
        self.blink = None
        self.container = None
        self.Load()

    def Load(self):
        self.districtID = self.district['districtID']
        self.planetID = self.district['planetID']
        self.latitude = self.district['latitude']
        self.longitude = self.district['longitude']
        self.planet = sm.GetService('michelle').GetBallpark(session.solarsystemid).balls[self.planetID]
        self.point = planet.SurfacePoint(phi=self.latitude, theta=self.longitude)
        self.name = 'DistrictBracket_%d' % self.districtID
        self.destrictGfxID = self.planet.GetDistrictNum('district-%d' % self.districtID)
        if self.container:
            self.container.Close()
        self.container = ui3d.Container(scene=sm.GetService('sceneManager').GetRegisteredScene('default'), name=self.name, width=512, height=512, clearBackground=True, backgroundColor=(0, 0, 0, 0))
        self.container.transform.translationCurve = self.planet.model.translationCurve
        self.container.transform.translation = geo2.Vec3Scale(geo2.Vec3Normalize(self.point.GetAsXYZTuple()), self.planet.radius)
        self.container.transform.scaling = (1000000, 1000000, 1000000)
        self.container.transform.rotation = geo2.QuaternionRotationSetYawPitchRoll(-self.longitude + math.pi / 2, self.latitude - math.pi / 2, 0)
        self.hover = uicls.Container(parent=self.container, align=uiconst.CENTER, state=uiconst.UI_NORMAL, opacity=1, width=512, height=512)
        self.hover.OnMouseEnter = self.OnMouseEnter
        self.hover.OnMouseExit = self.OnMouseExit
        self.hover.OnClick = self.OnClick
        self.transform = uicls.Transform(parent=self.hover, align=uiconst.TOALL, rotation=0, scalingCenter=(0.5, 0.5))
        uicore.animations.MorphScalar(self.transform, 'rotation', startVal=0, endVal=math.pi / 2, duration=10, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_LINEAR)
        self.frame = self.Corners(parent=self.transform, image='res:/UI/Texture/Bombardment/district_bracket_frame.png', boxSize=450, cornerSize=170, opacity=0.0)
        self.arrows_transform = uicls.Transform(parent=self.transform, align=uiconst.TOALL, rotation=0, scalingCenter=(0.5, 0.5))
        self.arrows = self.Corners(parent=self.arrows_transform, image='res:/UI/Texture/Bombardment/target_triangle.png', boxSize=300, cornerSize=30, opacity=0.0)
        self.Redraw()

    def Redraw(self):
        if not self.container:
            return
        self.container.color = (0.5, 0.8, 1.0, 0.9)
        if self.pending and not self.connected:
            title = localization.GetByLabel('UI/Inflight/Messages/Connecting')
            message = localization.GetByLabel('UI/Inflight/Messages/ToDistrict', districtName=self.district['name'])
            self.SetNotify(title, message)
        if not self.pending and not self.connected and self.mouseOver:
            title = localization.GetByLabel('UI/Inflight/Messages/Connect')
            message = localization.GetByLabel('UI/Inflight/Messages/ToDistrict', districtName=self.district['name'])
            self.SetNotify(title, message)
        if not self.pending and self.connected and self.mouseOver:
            title = localization.GetByLabel('UI/Inflight/Messages/Disconnect')
            message = localization.GetByLabel('UI/Inflight/Messages/FromDistrict', districtName=self.district['name'])
            self.SetNotify(title, message)
        if not self.pending and self.connected and not self.mouseOver:
            title = localization.GetByLabel('UI/Inflight/Messages/Connected')
            message = localization.GetByLabel('UI/Inflight/Messages/ToDistrict', districtName=self.district['name'])
            self.SetNotify(title, message)
        if not self.pending and not self.connected and not self.mouseOver:
            self.ClearNotify()
        if not self.pending and self.connected:
            uicore.animations.MorphScalar(self.frame, 'opacity', startVal=self.frame.opacity, endVal=0.4, duration=0.2)
        if not self.pending and self.mouseOver:
            uicore.animations.MorphScalar(self.frame, 'opacity', startVal=self.frame.opacity, endVal=0.8, duration=0.2)
        if not self.pending and not self.mouseOver and not self.connected:
            uicore.animations.MorphScalar(self.frame, 'opacity', startVal=self.frame.opacity, endVal=0, duration=0.3)
        if self.pending and not self.animating:
            self.animating = True
            self.container.color = (1, 1, 1, 0.7)
            self.frame.opacity = 0
            blue.synchro.Sleep(15)
            self.frame.opacity = 0.9
            blue.synchro.Sleep(15)
            self.frame.opacity = 0
            blue.synchro.Sleep(15)
            self.frame.opacity = 0.9
            blue.synchro.Sleep(15)
            self.frame.opacity = 0
            blue.synchro.Sleep(15)
            self.container.color = (0.4, 0.7, 1.0, 0.7)
            uicore.animations.MorphVector2(self.transform, 'scale', startVal=(0.8, 0.8), endVal=(1, 1), duration=0.6, loops=4)
            uicore.animations.MorphScalar(self.frame, 'opacity', startVal=0, endVal=0.8, duration=0.6, loops=4, curveType=uiconst.ANIM_BOUNCE)
        if not self.pending:
            self.animating = False
        if self.connected:
            uicore.animations.MorphVector2(self.arrows_transform, 'scale', startVal=self.arrows_transform.scale, endVal=(1, 1), duration=0.3)
            uicore.animations.MorphScalar(self.arrows, 'opacity', startVal=0.7, endVal=0.9, duration=0.9, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_BOUNCE)
        if not self.connected:
            uicore.animations.MorphVector2(self.arrows_transform, 'scale', startVal=self.arrows_transform.scale, endVal=(0, 0), duration=0.3)
            uicore.animations.MorphScalar(self.arrows, 'opacity', startVal=self.arrows.opacity, endVal=0, duration=0.3)

    def SetNotify(self, header, message):
        self.notifications.add(header)
        sm.GetService('space').Indicate(header, '<center>' + message)

    def ClearNotify(self):
        header = sm.GetService('space').GetHeader()
        if header in self.notifications:
            sm.GetService('space').Indicate(None, None)

    def Close(self):
        if getattr(self, 'container', None) is not None:
            self.container.Close()
            self.container = None

    def OnMouseEnter(self, *args):
        self.mouseOver = True
        self.Redraw()

    def OnMouseExit(self, *args):
        self.mouseOver = False
        self.Redraw()

    def OnClick(self, *args):
        if not self.pending:
            try:
                if not self.connected:
                    self.SetPending(True)
                    sm.GetService('district').ConnectDistrict()
                else:
                    self.SetPending(False)
                    sm.GetService('district').DisconnectDistrict()
            finally:
                self.SetPending(False)

    def SetConnected(self, connected):
        self.connected = connected
        self.pending = False
        self.Redraw()

    def SetPending(self, pending):
        self.pending = pending
        self.Redraw()

    def OnDistrictTargets(self, targets):
        self.targets = targets
        self.Redraw()

    def OnCreate(self, device):
        if self.container:
            self.Load()

    def Ring(self, parent, size, duration):
        ring = uicls.Icon(parent=parent, icon='res:/UI/Texture/Bombardment/target_circle_medium.png', align=uiconst.CENTER, state=uiconst.UI_DISABLED)
        uicore.animations.MorphScalar(ring, 'width', startVal=5, endVal=size, duration=duration)
        uicore.animations.MorphScalar(ring, 'height', startVal=5, endVal=size, duration=duration)
        blue.synchro.Sleep(50)
        uicore.animations.MorphScalar(ring, 'opacity', startVal=1, endVal=0.0, duration=duration)
        return ring

    def Corners(self, parent, image, boxSize = 1, cornerSize = 1, opacity = 1, boxWidth = None, boxHeight = None):
        boxWidth = boxWidth or boxSize
        boxHeight = boxHeight or boxSize
        corners = uicls.Container(parent=parent, align=uiconst.CENTER, width=boxWidth, height=boxHeight, opacity=opacity)
        corners.corner_tl = uicls.Icon(parent=corners, icon=image, align=uiconst.TOPLEFT, width=cornerSize, height=cornerSize, rotation=0, state=uiconst.UI_DISABLED)
        corners.corner_tr = uicls.Icon(parent=corners, icon=image, align=uiconst.TOPRIGHT, width=cornerSize, height=cornerSize, rotation=-math.pi / 2, state=uiconst.UI_DISABLED)
        corners.corner_br = uicls.Icon(parent=corners, icon=image, align=uiconst.BOTTOMRIGHT, width=cornerSize, height=cornerSize, rotation=math.pi, state=uiconst.UI_DISABLED)
        corners.corner_bl = uicls.Icon(parent=corners, icon=image, align=uiconst.BOTTOMLEFT, width=cornerSize, height=cornerSize, rotation=math.pi / 2, state=uiconst.UI_DISABLED)
        return corners